#!/usr/bin/env python3
"""P0 smoke test against a running vLLM server.

Checks the three things the rest of the pipeline depends on:

1. the server is up and advertises the expected model;
2. a thinking request comes back with a parsed `<think>` block — i.e. the qwen3 reasoning
   parser populates `message.reasoning_content` and leaves the answer in `message.content`,
   which is exactly what `cotctl.inference.split_think` reads;
3. throughput at batch 32 (output tokens/s), to size the compute budget in PLAN.md.

    scripts/serve_vllm.sh &
    python scripts/smoke_test.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from cotctl.inference import OK, Request, SamplingParams, VLLMClient, wait_for_server  # noqa: E402
from cotctl.prompts import cotcontrol_prompt, reasonif_prompt  # noqa: E402

THINK_QUESTION = "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?"


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return ok


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-tokens", type=int, default=1024, help="throughput probe cap")
    ap.add_argument("--out", default=str(REPO / "results" / "smoke_test.json"))
    args = ap.parse_args()

    served = wait_for_server(args.base_url)
    model = args.model or served
    print(f"\nserver up at {args.base_url}, serving: {served}\n")

    ok = True
    report: dict = {"served_model": served, "base_url": args.base_url}

    # --- 1. one thinking request, reasoning parser --------------------------
    print("1. thinking request / <think> parsing")
    client = VLLMClient(model, args.base_url, concurrency=1)
    rollout = (
        await client.run(
            [Request("smoke", "think", reasonif_prompt(THINK_QUESTION, "When reasoning, refrain from the use of any commas."))],
            SamplingParams(max_tokens=4096),
            progress=False,
        )
    )[0]

    ok &= check("no request error", rollout.error is None, rollout.error or "")
    ok &= check("think block parsed", rollout.think_status == OK, f"status={rollout.think_status}")
    ok &= check("reasoning non-empty", bool(rollout.reasoning.strip()), f"{len(rollout.reasoning)} chars")
    ok &= check("answer non-empty", bool(rollout.answer.strip()), f"{len(rollout.answer)} chars")
    ok &= check(
        "raw <think> tags stripped by the parser",
        "<think>" not in rollout.reasoning and "</think>" not in rollout.answer,
    )
    # The rollout must be gradeable end-to-end by the real ReasonIF grader.
    from cotctl.graders.reasonif import grade_reasonif

    no_comma_verdict = grade_reasonif("no_comma", rollout.reasoning)
    ok &= check(
        "ReasonIF grader runs on the rollout",
        isinstance(no_comma_verdict, bool),
        f"no_comma verdict={no_comma_verdict}",
    )

    print(f"\n  reasoning[:300]: {rollout.reasoning[:300]!r}")
    print(f"  answer[:200]:    {rollout.answer[:200]!r}")
    report["think_check"] = {
        "status": rollout.think_status,
        "reasoning_chars": len(rollout.reasoning),
        "answer_chars": len(rollout.answer),
        "completion_tokens": rollout.completion_tokens,
        "finish_reason": rollout.finish_reason,
        "reasoning_head": rollout.reasoning[:500],
        "answer_head": rollout.answer[:500],
    }

    # --- 2. a CoTControl-shaped prompt (uppercase) --------------------------
    print("\n2. CoTControl-shaped request (uppercase_thinking)")
    cc = (
        await client.run(
            [Request("smoke_cc", "uppercase_thinking",
                     cotcontrol_prompt("What is the capital of France?", "uppercase_thinking", "",
                                       ["Paris", "London", "Berlin", "Madrid"]))],
            # Qwen3.5-9B spends ~3-4k tokens reasoning on even a trivial MCQ, so a smaller cap
            # truncates mid-<think> and the probe would report a spurious "unclosed".
            SamplingParams(max_tokens=8192),
            progress=False,
        )
    )[0]
    ok &= check("think block parsed", cc.think_status == OK, f"status={cc.think_status}")
    from cotctl.eval import extract_mcq_answer
    from cotctl.graders.cotcontrol import grade_cotcontrol

    letter = extract_mcq_answer(cc.answer)
    compliant = grade_cotcontrol("uppercase_thinking", cc.reasoning)
    ok &= check("answer letter extractable", letter is not None, f"got {letter!r}")
    print(f"  grader verdict on the uppercase constraint: {compliant} (baseline models usually fail this)")
    report["cotcontrol_check"] = {"status": cc.think_status, "letter": letter, "compliant": compliant}

    # --- 3. throughput at batch N -------------------------------------------
    print(f"\n3. throughput at batch {args.batch} (max_tokens={args.max_tokens})")
    batch_client = VLLMClient(model, args.base_url, concurrency=args.batch)
    reqs = [
        Request(f"bench_{i}", "bench", reasonif_prompt(THINK_QUESTION, "When reasoning, refrain from the use of any commas."))
        for i in range(args.batch)
    ]
    t0 = time.monotonic()
    rollouts = await batch_client.run(reqs, SamplingParams(max_tokens=args.max_tokens), progress=False)
    elapsed = time.monotonic() - t0

    out_tokens = sum(r.completion_tokens for r in rollouts)
    in_tokens = sum(r.prompt_tokens for r in rollouts)
    n_err = sum(1 for r in rollouts if r.error)
    tps = out_tokens / elapsed if elapsed else 0.0
    ok &= check("no errors in batch", n_err == 0, f"{n_err} error(s)")
    print(f"  {len(rollouts)} rollouts in {elapsed:.1f}s")
    print(f"  output {out_tokens} tok  ->  {tps:.0f} output tok/s   (prompt {in_tokens} tok)")
    report["throughput"] = {
        "batch": args.batch,
        "max_tokens": args.max_tokens,
        "n": len(rollouts),
        "elapsed_s": round(elapsed, 2),
        "output_tokens": out_tokens,
        "prompt_tokens": in_tokens,
        "output_tokens_per_s": round(tps, 1),
        "errors": n_err,
    }

    # --- budget projection ---------------------------------------------------
    # PLAN.md: 5 evals x 3,000 rollouts + ~2,000 SFT/calibration rollouts, ~6k tokens each.
    if tps > 0:
        total_rollouts = 5 * 3000 + 2000
        hours = total_rollouts * 6000 / tps / 3600
        print(f"\n  projected full-project inference: {total_rollouts} rollouts x 6k tok "
              f"~= {hours:.1f} GPU-hours at this rate")
        report["projected_gpu_hours"] = round(hours, 1)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out}")
    print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
