"""METR's published numbers, for side-by-side reporting.

Read off the figures in https://metr.org/blog/2026-04-01-fine-tuning-cot-controllability/
(Nishimura-Gasparian & Parikh, 2026-04-01). All values are percentages; `ft240` is the
step-60 checkpoint (60 steps x batch 4 = 240 samples), which is METR's headline.
Intervals in the blog are 80 % Wald, the same convention `cotctl.eval.wald_ci` uses.

Qwen3.5-9B is not in METR's set. The two Qwen3.5 entries that *are* (4B and 27B) are
baseline-only, and they bracket our model — which is what makes them the sanity check for
our baseline run: we expect CoTControl ~0-1 % and ReasonIF ~9-10 %.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetrRow:
    model: str
    cotcontrol_base: float
    reasonif_base: float
    cotcontrol_ft240: float | None = None
    reasonif_ft240: float | None = None
    note: str = ""


METR_RESULTS = (
    MetrRow("Qwen3-8B", 1.1, 20.9, 5.6, 43.8),
    MetrRow("Qwen3-32B", 3.7, 28.9, 9.8, 55.3),
    MetrRow("GPT-OSS-20B", 2.1, 15.0, 7.3, 50.7),
    MetrRow("GPT-OSS-120B", 4.4, 23.7, 13.1, 49.0),
    MetrRow("Qwen3.5-4B", 0.0, 9.4, None, None, "baseline only"),
    MetrRow("Qwen3.5-27B", 1.3, 9.9, None, None, "baseline only"),
)

# What PLAN.md predicts for Qwen3.5-9B, interpolating between the 4B and 27B entries.
EXPECTED_BASELINE = {"cotcontrol": (0.0, 1.5), "reasonif": (8.0, 11.0)}

# METR observes that the Qwen3.5 family "uses meta discussion very often".
QWEN35_HIGH_META_DISCUSSION = True


def _fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.1f}"


def comparison_table(
    ours_cotcontrol: float | None = None,
    ours_reasonif: float | None = None,
    label: str = "Qwen3.5-9B (ours, base)",
) -> str:
    """Markdown table of METR's numbers with our run appended."""
    lines = [
        "| Model | CoTControl base | CoTControl FT@240 | ReasonIF base | ReasonIF FT@240 | |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in METR_RESULTS:
        lines.append(
            f"| {r.model} | {_fmt(r.cotcontrol_base)} | {_fmt(r.cotcontrol_ft240)} | "
            f"{_fmt(r.reasonif_base)} | {_fmt(r.reasonif_ft240)} | {r.note} |"
        )
    cc = None if ours_cotcontrol is None else 100 * ours_cotcontrol
    rif = None if ours_reasonif is None else 100 * ours_reasonif
    lines.append(f"| **{label}** | **{_fmt(cc)}** | — | **{_fmt(rif)}** | — | this replication |")

    checks = []
    for name, val in (("cotcontrol", cc), ("reasonif", rif)):
        if val is None:
            continue
        lo, hi = EXPECTED_BASELINE[name]
        verdict = "in range" if lo <= val <= hi else "OUT OF RANGE"
        checks.append(f"- {name}: {val:.1f} % vs expected {lo:.1f}–{hi:.1f} % (4B/27B bracket) — **{verdict}**")
    if checks:
        lines += ["", "Baseline sanity check (PLAN.md):", *checks]
    return "\n".join(lines)
