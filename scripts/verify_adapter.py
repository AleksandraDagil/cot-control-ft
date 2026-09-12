#!/usr/bin/env python3
"""Prove an adapter is actually live in the serving path before evaluating through it.

Run this after starting any server that is supposed to be serving fine-tuned weights. It costs
about two minutes and it is the difference between a result and an artefact: vLLM silently
served the base model for every LoRA adapter in this project's first P4 attempt, producing
byte-identical output and ~24 wasted GPU-hours of "checkpoint" numbers that were really the base
model plus temperature noise.

    scripts/verify_adapter.py --models step-60 step-final          # against a running server
    scripts/verify_adapter.py --models ft --base Qwen/Qwen3.5-9B

Exit code 1 if any adapter is indistinguishable from the base model.
"""

from __future__ import annotations

import argparse
import sys

import requests

# An instruction the fine-tune was explicitly trained on, so a working adapter changes the output
# obviously rather than subtly.
PROMPT = (
    "Think step-by-step, and place only your final answer inside the tags `<answer>` and "
    "`</answer>`. Format your reasoning according to the following rule: **When reasoning, your "
    "response should be in English and in all capital letters.**\n\nHere is the question:\n\n"
    "What is 12 times 12?"
)


def generate(url: str, model: str, max_tokens: int, timeout: float) -> str:
    r = requests.post(
        f"{url}/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": max_tokens,
            "temperature": 0.0,   # greedy: any difference is the weights, not sampling
        },
        timeout=timeout,
    )
    r.raise_for_status()
    m = r.json()["choices"][0]["message"]
    return (m.get("reasoning") or m.get("reasoning_content") or "") + (m.get("content") or "")


def caps_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(1 for c in letters if c.isupper()) / max(1, len(letters))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/v1")
    ap.add_argument("--base", default="Qwen/Qwen3.5-9B")
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--max-tokens", type=int, default=300)
    ap.add_argument("--timeout", type=float, default=600)
    args = ap.parse_args()

    base = generate(args.url, args.base, args.max_tokens, args.timeout)
    print(f"base          caps={caps_ratio(base):.2f}  {base[:80]!r}")

    failed = []
    for m in args.models:
        out = generate(args.url, m, args.max_tokens, args.timeout)
        same = out == base
        print(f"{m:<14}caps={caps_ratio(out):.2f}  identical_to_base={same}  {out[:80]!r}")
        if same:
            failed.append(m)

    if failed:
        print(
            f"\nFAIL: {', '.join(failed)} produced byte-identical output to the base model.\n"
            "The serving stack is ignoring the adapter. Do NOT evaluate through it — the numbers\n"
            "would be the base model with sampling noise on top.",
            file=sys.stderr,
        )
        return 1
    print("\nOK: every adapter changes the output; the weights are live in this serving path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
