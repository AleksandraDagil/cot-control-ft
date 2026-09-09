#!/usr/bin/env python3
"""Run one full evaluation (ReasonIF 300 + CoTControl 300/mode) against a served model.

Used for the P1 baseline and, with `--model ft --label step-60`, for each P4 checkpoint.
The CoTControl question set is a single `proportional_sample` draw (seed 42) reused across
every mode and every checkpoint, so base-vs-finetuned comparisons are paired.

    scripts/serve_vllm.sh &                                  # in another shell
    python scripts/run_baseline.py --label base

Everything is resumable: rollouts are keyed by (sample_id, mode) in a JSONL, judge verdicts are
cached by prompt hash. Re-running skips completed work, so an interrupted eval just continues.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from cotctl import eval as ev  # noqa: E402
from cotctl.datasets import load_reasonif  # noqa: E402
from cotctl.inference import RolloutStore, SamplingParams, VLLMClient, run_sync, wait_for_server  # noqa: E402
from cotctl.analysis.metr import comparison_table, sanity_check  # noqa: E402
from cotctl.prompts import COTCONTROL_MODES  # noqa: E402

log = logging.getLogger("baseline")


def load_word_limits(path: str | None) -> dict[str, int] | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # Accept either {"source": n} or the upstream {"model": {"source": n}} shape.
    if data and all(isinstance(v, dict) for v in data.values()):
        if len(data) != 1:
            raise ValueError(f"{path}: expected one model key, got {sorted(data)}")
        data = next(iter(data.values()))
    return {k: int(v) for k, v in data.items()}


def judge_ignore_question(rollouts: list[dict], cfg: dict, cache_path: Path) -> dict:
    """LLM verdicts for the `ignore_question` rollouts that have usable reasoning."""
    from cotctl.judge import LLMJudge

    pending = [
        r
        for r in rollouts
        if r["mode"] == "ignore_question"
        and not r.get("error")
        and r.get("think_status") == "ok"
        and (r.get("reasoning") or "").strip()
    ]
    if not pending:
        return {}
    log.info("judging %d ignore_question rollouts with %s", len(pending), cfg["judge"]["model"])
    judge = LLMJudge(
        model=cfg["judge"]["model"],
        cache_path=cache_path,
        concurrency=int(cfg["judge"].get("concurrency", 16)),
    )
    verdicts = asyncio.run(
        judge.judge_many(
            "ignore_question",
            [(r["prompt"], r["reasoning"]) for r in pending],
            desc="ignore_question judge",
        )
    )
    n_err = sum(1 for v in verdicts if v.error)
    if n_err:
        log.warning("%d judge call(s) failed; those rollouts stay ungraded", n_err)
    return {(r["sample_id"], r["mode"]): v.compliant for r, v in zip(pending, verdicts)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(REPO / "configs" / "base.yaml"))
    ap.add_argument("--label", default="base", help="names the output dir and summary files")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--model", default=None, help="served model id ('ft' for the LoRA adapter)")
    ap.add_argument("--word-limits", default=None, help="json from calibrate_number_words.py")
    ap.add_argument("--suites", default="reasonif,cotcontrol")
    ap.add_argument("--modes", default=None, help="comma-separated CoTControl mode subset")
    ap.add_argument("--limit", type=int, default=None, help="debug: cap questions per suite")
    ap.add_argument("--no-judge", action="store_true", help="skip the ignore_question LLM judge")
    ap.add_argument("--grade-only", action="store_true", help="re-grade stored rollouts, no inference")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import yaml

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    model_name = args.model or cfg["model"]["served_name"]
    suites = [s.strip() for s in args.suites.split(",") if s.strip()]
    out_dir = Path(args.out_dir or REPO / "results" / args.label)
    out_dir.mkdir(parents=True, exist_ok=True)

    word_limits = load_word_limits(args.word_limits or cfg["eval"].get("word_limits"))
    if word_limits:
        log.info("number_words limits: %s", word_limits)
    elif "reasonif" in suites:
        log.warning(
            "no --word-limits given: using the limits shipped in reasonIF_dataset.json, which were "
            "calibrated on GPT-OSS-120B. Run scripts/calibrate_number_words.py first."
        )

    sampling = SamplingParams(**dict(cfg["sampling"]))
    client = None
    if not args.grade_only:
        served = wait_for_server(cfg["server"]["base_url"])
        log.info("server ready, serving %s (requesting %s)", served, model_name)
        client = VLLMClient(model_name, cfg["server"]["base_url"], concurrency=cfg["server"]["concurrency"])

    # --- build request sets ---------------------------------------------
    requests, stores = {}, {}
    if "reasonif" in suites:
        samples = load_reasonif()
        if args.limit:
            samples = samples[: args.limit]
        requests["reasonif"] = ev.reasonif_requests(samples, word_limits)
        stores["reasonif"] = out_dir / "reasonif_rollouts.jsonl"
    if "cotcontrol" in suites:
        modes = [m.strip() for m in args.modes.split(",")] if args.modes else (
            cfg["eval"]["cotcontrol"].get("modes") or list(COTCONTROL_MODES)
        )
        n = args.limit or int(cfg["eval"]["cotcontrol"]["n_per_mode"])
        cc_samples = ev.cotcontrol_samples(n, int(cfg["eval"]["cotcontrol"]["seed"]))
        log.info("CoTControl question set: %d questions x %d modes", len(cc_samples), len(modes))
        requests["cotcontrol"] = ev.cotcontrol_requests(cc_samples, modes)
        stores["cotcontrol"] = out_dir / "cotcontrol_rollouts.jsonl"

    run_config = {
        "label": args.label,
        "model": model_name,
        "adapter": cfg["model"].get("adapter"),
        "sampling": dict(cfg["sampling"]),
        "word_limits": word_limits,
        "cotcontrol_n_per_mode": cfg["eval"]["cotcontrol"]["n_per_mode"],
        "cotcontrol_seed": cfg["eval"]["cotcontrol"]["seed"],
        "judge_model": cfg["judge"]["model"],
    }
    (out_dir / "run_config.json").write_text(json.dumps(run_config, indent=2) + "\n", encoding="utf-8")

    # --- inference -------------------------------------------------------
    summaries, graded_by_suite = {}, {}
    for suite, reqs in requests.items():
        store = RolloutStore(stores[suite])
        if not args.grade_only:
            log.info("%s: %d requests (%d already done)", suite, len(reqs), len(store))
            with store:
                run_sync(client, reqs, sampling, store, desc=f"{args.label}/{suite}")

        rollouts = store.read_all()
        judged = {}
        if suite == "cotcontrol" and not args.no_judge:
            judged = judge_ignore_question(rollouts, cfg, out_dir / "judge_cache.jsonl")

        graded = ev.grade_all(rollouts, judged)
        graded_by_suite[suite] = graded
        summaries[suite] = ev.write_summary(graded, out_dir, f"{args.label}_{suite}", run_config)
        print()
        print(ev.markdown_table(ev.by_mode(graded), f"{args.label} — {suite}"))

    (out_dir / f"summary_{args.label}.json").write_text(
        json.dumps({"config": run_config, "suites": summaries}, indent=2) + "\n", encoding="utf-8"
    )

    # --- deliverable: side-by-side with METR's published numbers ---------
    # CoTControl is the unweighted mean over the 9 modes (METR's headline); ReasonIF is the
    # micro rate over all 300 prompts, with the per-instruction macro reported alongside.
    cc = (summaries.get("cotcontrol") or {}).get("macro_compliance")
    rif_sum = summaries.get("reasonif") or {}
    rif = (rif_sum.get("overall") or {}).get("compliance")
    # comparison_table takes percentages; the summaries store fractions.
    cc_pct = None if cc is None else 100 * cc
    rif_pct = None if rif is None else 100 * rif
    table = comparison_table(cc_pct, rif_pct, label=f"Qwen3.5-9B (ours, {args.label})")
    report = [f"# {args.label} vs METR", "", table, ""]
    report += ["", "Baseline sanity check (PLAN.md):", ""]
    report += [f"- {n}" for n in sanity_check(cc_pct, rif_pct)] + [""]
    if rif_sum.get("macro_compliance") is not None:
        report += [
            f"ReasonIF macro (unweighted over the 6 instruction types): "
            f"{100 * rif_sum['macro_compliance']:.1f} %",
            "",
        ]
    for suite, graded in graded_by_suite.items():
        report += [f"## {suite}", "", ev.markdown_table(ev.by_mode(graded), ""), ""]
    (out_dir / f"report_{args.label}.md").write_text("\n".join(report), encoding="utf-8")
    print()
    print(table)
    print(f"\nwrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
