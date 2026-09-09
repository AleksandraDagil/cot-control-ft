#!/usr/bin/env python3
"""Turn a finished eval into the P1 deliverable: a markdown report with METR side-by-side.

    python scripts/report_baseline.py --label base

Reads `results/<label>/summary_<label>_{reasonif,cotcontrol}.json` (written by run_baseline.py)
and emits `results/<label>/REPORT.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotctl.analysis.metr import comparison_table, sanity_check  # noqa: E402


def pct(x: float | None) -> float | None:
    return None if x is None else 100 * x


def _table_from_summary(summary: dict) -> str:
    rows = [
        "| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, m in summary["per_mode"].items():
        def f(x):
            return "—" if x is None else f"{100 * x:.1f}"

        lo, hi = m["compliance_ci80"]
        rows.append(
            f"| {mode} | {m['n_total']} | {m['n_gradeable']} | {f(m['compliance'])} | "
            f"{f(lo)}–{f(hi)} | {f(m['accuracy'])} | {f(m['meta_rate'])} | "
            f"{f(m['truncation_rate'])} | {m['median_completion_tokens']} |"
        )
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="base")
    ap.add_argument("--results-dir", default=None)
    args = ap.parse_args()

    out_dir = Path(args.results_dir or REPO / "results" / args.label)
    summaries = {}
    for suite in ("reasonif", "cotcontrol"):
        p = out_dir / f"summary_{args.label}_{suite}.json"
        if p.exists():
            summaries[suite] = json.loads(p.read_text(encoding="utf-8"))
        else:
            print(f"warning: {p} missing, skipping {suite}", file=sys.stderr)

    if not summaries:
        print(f"no summaries found under {out_dir}", file=sys.stderr)
        return 1

    cfg = next(iter(summaries.values())).get("config", {})
    # ReasonIF's headline is the overall pass rate; CoTControl's is the macro mean over modes.
    ours_rif = pct((summaries.get("reasonif", {}).get("overall") or {}).get("compliance"))
    ours_cc = pct(summaries.get("cotcontrol", {}).get("macro_compliance"))

    lines = [
        f"# Baseline: {cfg.get('model', 'unknown model')} (`{args.label}`)",
        "",
        "Independent replication of METR's CoT-controllability experiment; see `PLAN.md`.",
        "",
        "## Headline",
        "",
        f"- **ReasonIF** (300 prompts, overall compliance): **{'—' if ours_rif is None else f'{ours_rif:.1f} %'}**",
        f"- **CoTControl** ({cfg.get('cotcontrol_n_per_mode', '?')} questions x 9 modes, "
        f"macro-average over modes): **{'—' if ours_cc is None else f'{ours_cc:.1f} %'}**",
        "",
        "## Versus METR's published models",
        "",
        comparison_table(ours_cc, ours_rif),
        "",
        "Sanity check against PLAN.md's expectation (a 9B should land between METR's",
        "Qwen3.5-4B and Qwen3.5-27B baselines):",
        "",
    ]
    lines += [f"- {n}" for n in sanity_check(ours_cc, ours_rif)]
    lines += [
        "",
        "Caveats on the comparison: METR's numbers are digitised from figures; our CoTControl",
        "eval uses 300 questions per mode rather than ~100 (per-mode power near the floor); and",
        "our MMLU-Pro prompts include the answer choices, where METR's loader dropped them.",
        "",
    ]

    for suite, summary in summaries.items():
        overall = summary["overall"]
        lines += [
            f"## {suite}",
            "",
            _table_from_summary(summary),
            "",
            f"Rollouts: {overall['n_total']}, gradeable {overall['n_gradeable']} "
            f"({100 * (overall['gradeable_rate'] or 0):.1f} %), "
            f"errors {overall['n_error']}, truncated {100 * (overall['truncation_rate'] or 0):.1f} %.",
            f"Think-block status: {overall['think_status']}.",
            "",
        ]

    lines += ["## Run config", "", "```json", json.dumps(cfg, indent=2), "```", ""]

    report = "\n".join(lines)
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwrote {out_dir / 'REPORT.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
