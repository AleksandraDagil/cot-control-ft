#!/usr/bin/env python3
"""Re-judge stored rollouts for meta-discussion with the CoTControl paper's LLM judge.

Our reported meta-discussion rates use METR's regex heuristic. Its weakest pattern is the bare
substring `constraint`, which fires on a model quoting the prompt ("...this reasoning stage
constraint...") or on ordinary technical usage, without any actual narration of the control
instruction. This script scores the same rollouts with the paper's LLM judge (gpt-5-mini,
verbatim prompt, in `cotctl.judge`) so the two can be compared per mode and per checkpoint.

Verdicts are cached by prompt hash, so re-running is free.

    python scripts/judge_meta.py --labels base step-60 step-final --suites cotcontrol reasonif
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from cotctl.graders.cotcontrol import _META_PATTERNS, detect_meta_discussion  # noqa: E402
from cotctl.judge import LLMJudge  # noqa: E402

log = logging.getLogger("judge_meta")


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []


def regex_attribution(reasoning: str) -> list[str]:
    """Which of METR's seven patterns fire on this trace."""
    low = reasoning.lower()
    return [p for p in _META_PATTERNS if re.search(p, low)]


async def judge_suite(judge: LLMJudge, label: str, suite: str, limit: int | None) -> list[dict]:
    rows = [r for r in load(REPO / "results" / label / f"{suite}_rollouts.jsonl")
            if not r.get("error") and r.get("think_status") == "ok" and (r.get("reasoning") or "").strip()]
    if limit:
        rows = rows[:limit]
    log.info("%s/%s: judging %d rollouts", label, suite, len(rows))
    verdicts = await judge.judge_many("meta", [(r["prompt"], r["reasoning"]) for r in rows],
                                      desc=f"{label}/{suite} meta-judge")
    out = []
    for r, v in zip(rows, verdicts):
        out.append({
            "label": label, "suite": suite, "sample_id": r["sample_id"], "mode": r["mode"],
            "llm_meta": v.compliant,            # True = judge says it discusses the constraint
            "llm_error": v.error,
            "llm_violations": v.detail,
            "regex_meta": detect_meta_discussion(r["reasoning"]),
            "regex_patterns": regex_attribution(r["reasoning"]),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", nargs="+", default=["base", "step-60", "step-final"])
    ap.add_argument("--suites", nargs="+", default=["cotcontrol", "reasonif"])
    ap.add_argument("--limit", type=int, default=None, help="debug: rollouts per (label, suite)")
    ap.add_argument("--concurrency", type=int, default=16)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    out_dir = REPO / "results" / "meta_judge"
    out_dir.mkdir(parents=True, exist_ok=True)
    judge = LLMJudge(cache_path=out_dir / "meta_judge_cache.jsonl", concurrency=args.concurrency)

    all_rows: list[dict] = []
    for label in args.labels:
        for suite in args.suites:
            if not (REPO / "results" / label / f"{suite}_rollouts.jsonl").exists():
                log.warning("no %s rollouts for %s; skipping", suite, label)
                continue
            all_rows.extend(asyncio.run(judge_suite(judge, label, suite, args.limit)))

    with open(out_dir / "meta_verdicts.jsonl", "w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # --- summary --------------------------------------------------------
    summary: dict = {}
    for (label, suite), rows in _group(all_rows, lambda r: (r["label"], r["suite"])).items():
        ok = [r for r in rows if r["llm_meta"] is not None]
        per_mode = {}
        for mode, mrows in sorted(_group(ok, lambda r: r["mode"]).items()):
            per_mode[mode] = {
                "n": len(mrows),
                "llm_meta_rate": sum(r["llm_meta"] for r in mrows) / len(mrows),
                "regex_meta_rate": sum(r["regex_meta"] for r in mrows) / len(mrows),
                "agreement": sum(r["llm_meta"] == r["regex_meta"] for r in mrows) / len(mrows),
                "regex_only": sum(r["regex_meta"] and not r["llm_meta"] for r in mrows),
                "llm_only": sum(r["llm_meta"] and not r["regex_meta"] for r in mrows),
            }
        pat = Counter(p for r in ok for p in r["regex_patterns"])
        summary[f"{label}/{suite}"] = {
            "n_judged": len(ok), "n_judge_errors": len(rows) - len(ok),
            "llm_meta_rate": sum(r["llm_meta"] for r in ok) / max(1, len(ok)),
            "regex_meta_rate": sum(r["regex_meta"] for r in ok) / max(1, len(ok)),
            "agreement": sum(r["llm_meta"] == r["regex_meta"] for r in ok) / max(1, len(ok)),
            "per_mode": per_mode,
            "regex_pattern_hits": dict(pat.most_common()),
        }
    (out_dir / "meta_judge_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for k, v in summary.items():
        print(f"{k:<24} n={v['n_judged']:<5} LLM meta={100*v['llm_meta_rate']:5.1f}%  regex meta={100*v['regex_meta_rate']:5.1f}%  agree={100*v['agreement']:5.1f}%  errors={v['n_judge_errors']}")
    print(f"\nwrote {out_dir}")
    return 0


def _group(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[key(r)].append(r)
    return g


if __name__ == "__main__":
    raise SystemExit(main())
