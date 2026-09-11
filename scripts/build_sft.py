#!/usr/bin/env python3
"""Build the ReasonIF SFT dataset (P2).

Stage 1  generate an unconstrained reasoning trace per question, with the *instruction-stripped*
         prompt -- METR applies the constraint by editing afterwards, never by asking for it.
Stage 2  edit each trace so it satisfies its assigned constraint (4 rule-based, 2 via an editor
         LLM), then verify with the canonical ReasonIF grader and drop whatever fails.

    scripts/serve_vllm.sh &
    python scripts/build_sft.py --stage 1
    python scripts/build_sft.py --stage 2

Both stages are resumable: Stage-1 rollouts are keyed by (question_id, "sft") in a JSONL and
editor responses are cached by prompt hash, so a re-run costs nothing for work already done.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from cotctl.datasets import load_multilingual_thinking_prompts  # noqa: E402
from cotctl.graders.reasonif import grade_reasonif  # noqa: E402
from cotctl.inference import RolloutStore, SamplingParams, VLLMClient, Request, run_sync, wait_for_server  # noqa: E402
from cotctl.sft.build import Assignment, TrainingRow, plan_assignments, write_training_jsonl  # noqa: E402
from cotctl.sft.editor import Editor  # noqa: E402
from cotctl.sft.transforms import TransformContext, apply_transform  # noqa: E402

log = logging.getLogger("build_sft")


def load_plan(seed: int, n_rows: int | None) -> list[Assignment]:
    return plan_assignments(load_multilingual_thinking_prompts(), n_rows, seed)


def stage1(plan: list[Assignment], cfg: dict, out_dir: Path, model: str | None) -> None:
    model = model or cfg["model"]["served_name"]
    served = wait_for_server(cfg["server"]["base_url"])
    log.info("server ready, serving %s (requesting %s)", served, model)
    client = VLLMClient(model, cfg["server"]["base_url"], concurrency=cfg["server"]["concurrency"])
    sampling = SamplingParams(**dict(cfg["sampling"]))

    # Keyed by question_id, not row index: the Stage-1 prompt carries no mode, so a rollout
    # stays valid even if the plan is regenerated with a different seed.
    reqs = [
        Request(sample_id=a.question_id, mode="sft", prompt=a.stage1_prompt,
                meta={"suite": "sft", "row_idx": a.row_idx, "assigned_mode": a.mode})
        for a in plan
    ]
    store = RolloutStore(out_dir / "stage1_rollouts.jsonl")
    log.info("stage 1: %d questions (%d already done)", len(reqs), len(store))
    with store:
        run_sync(client, reqs, sampling, store, desc="sft/stage1")


async def stage2(plan: list[Assignment], out_dir: Path, editor_model: str, limit: int | None) -> None:
    rollouts = {r["sample_id"]: r for r in RolloutStore(out_dir / "stage1_rollouts.jsonl").read_all()}
    log.info("stage 2: %d stage-1 rollouts available", len(rollouts))
    editor = Editor(model=editor_model, cache_path=out_dir / "editor_cache.jsonl")

    rows: list[TrainingRow] = []
    dropped: list[dict] = []
    plan = plan[:limit] if limit else plan

    async def one(a: Assignment):
        r = rollouts.get(a.question_id)
        if r is None or r.get("error"):
            dropped.append({"row_idx": a.row_idx, "mode": a.mode, "reason": "no stage-1 rollout"})
            return
        if r.get("think_status") != "ok" or not (r.get("reasoning") or "").strip():
            dropped.append({"row_idx": a.row_idx, "mode": a.mode, "reason": f"think_status={r.get('think_status')}"})
            return
        # An empty answer would train the model to emit nothing after </think>, which is the
        # opposite of what we want: the point is a controlled CoT *and* a real answer.
        if not (r.get("answer") or "").strip():
            dropped.append({"row_idx": a.row_idx, "mode": a.mode, "reason": "empty answer"})
            return

        args = dict(a.constraint_args or {})
        ctx = TransformContext(question=a.question, full_prompt=a.stage1_prompt, editor=editor)
        try:
            edited = await apply_transform(a.mode, r["reasoning"], args, ctx)
        except Exception as e:  # noqa: BLE001
            dropped.append({"row_idx": a.row_idx, "mode": a.mode, "reason": f"transform failed: {e}"})
            return

        # The grader is the arbiter, not the transform. number_words rewrites args["num_words"],
        # so the row must be graded against the target actually used and the prompt must state it.
        if not grade_reasonif(a.mode, edited, args):
            dropped.append({"row_idx": a.row_idx, "mode": a.mode, "reason": "failed its own grader"})
            return

        instruction = a.instruction
        if a.mode == "number_words":
            import re as _re
            instruction = _re.sub(r"(?<=less than )\d+(?= words)", str(args["num_words"]), instruction)

        from cotctl.prompts import reasonif_prompt
        rows.append(TrainingRow(
            row_idx=a.row_idx, question_id=a.question_id, mode=a.mode,
            prompt=reasonif_prompt(a.question, instruction),
            reasoning=edited, answer=(r.get("answer") or "").strip(),
            constraint_args=args,
        ))

    sem = asyncio.Semaphore(16)

    async def guarded(a):
        async with sem:
            await one(a)

    try:
        from tqdm.auto import tqdm
        bar = tqdm(total=len(plan), desc="sft/stage2")
    except ImportError:
        bar = None

    async def tracked(a):
        await guarded(a)
        if bar:
            bar.update(1)

    await asyncio.gather(*(tracked(a) for a in plan))
    if bar:
        bar.close()

    rows.sort(key=lambda r: r.row_idx)
    out = write_training_jsonl(rows, REPO / "data" / "sft" / "qwen3.5-9b_reasonif.jsonl")
    (out_dir / "dropped.json").write_text(json.dumps(dropped, indent=2), encoding="utf-8")

    kept = Counter(r.mode for r in rows)
    drop = Counter(d["mode"] for d in dropped)
    reasons = Counter(d["reason"].split(":")[0] for d in dropped)
    print(f"\n{'mode':<22}{'kept':>7}{'dropped':>9}{'yield':>8}")
    for m in sorted(set(kept) | set(drop)):
        k, d = kept[m], drop[m]
        print(f"{m:<22}{k:>7}{d:>9}{100*k/max(1,k+d):>7.0f}%")
    print(f"{'TOTAL':<22}{len(rows):>7}{len(dropped):>9}{100*len(rows)/max(1,len(rows)+len(dropped)):>7.0f}%")
    print(f"\ndrop reasons: {dict(reasons)}")
    print(f"editor calls: {editor.n_calls} made, {editor.n_cached} from cache")
    print(f"wrote {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", type=int, choices=(1, 2), required=True)
    ap.add_argument("--config", default=str(REPO / "configs" / "base.yaml"))
    ap.add_argument("--out-dir", default=str(REPO / "results" / "sft"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-rows", type=int, default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--editor-model", default="openai/gpt-4.1")
    ap.add_argument("--limit", type=int, default=None, help="debug: only the first N assignments")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import yaml

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plan = load_plan(args.seed, args.n_rows)
    log.info("plan: %d rows, modes %s", len(plan), dict(Counter(a.mode for a in plan)))
    (out_dir / "plan.json").write_text(
        json.dumps([{k: v for k, v in vars(a).items()} for a in plan], indent=2), encoding="utf-8"
    )

    if args.stage == 1:
        stage1(plan, cfg, out_dir, args.model)
    else:
        asyncio.run(stage2(plan, out_dir, args.editor_model, args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
