#!/usr/bin/env python3
"""Generate unconstrained CoTControl rollouts: the same questions with no Requirement clause.

Needed as the denominator for continuous word-suppression scoring. The honest reference for
"how much of its normal keyword use did the model suppress" is how often *that same model*
uses the word when not asked to avoid it — so each model needs its own unconstrained run, and
scoring a fine-tuned model against the base model's usage would confound the two.

    scripts/gen_unconstrained.py --model results/merged/step-final --label step-final
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from cotctl import eval as ev  # noqa: E402
from cotctl.inference import Request, RolloutStore, SamplingParams, VLLMClient, run_sync, wait_for_server  # noqa: E402
from cotctl.prompts import cotcontrol_prompt  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--concurrency", type=int, default=64)
    args = ap.parse_args()

    wait_for_server(args.base_url)
    samples = ev.cotcontrol_samples(args.n, args.seed)
    reqs = [
        Request(
            sample_id=s.id,
            mode="unconstrained",
            prompt=cotcontrol_prompt(s.question, None, options=s.options),  # no Requirement clause
            meta={
                "suite": "cotcontrol",
                "dataset": s.dataset,
                "keywords": s.metadata.get("valid_keywords") or s.metadata.get("keywords") or [],
                "correct_answer": s.correct_answer,
                "correct_letter": s.metadata.get("answer_letter"),
            },
        )
        for s in samples
    ]
    out = REPO / "results" / args.label / "unconstrained_rollouts.jsonl"
    store = RolloutStore(out)
    print(f"{args.label}: {len(reqs)} unconstrained rollouts ({len(store)} already done)")
    with store:
        run_sync(
            VLLMClient(args.model, args.base_url, concurrency=args.concurrency),
            reqs,
            SamplingParams(max_tokens=32768),
            store,
            desc=f"{args.label}/unconstrained",
        )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
