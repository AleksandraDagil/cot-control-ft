"""METR's published numbers, for side-by-side reporting.

Read off the figures in "Fine-tuning experiments on CoT controllability"
(Nishimura-Gasparian & Parikh, 2026-04-01, https://metr.org/blog/2026-04-01-fine-tuning-cot-controllability/)
and recorded in PLAN.md. These are *approximate* — digitised from bar charts, not a released
table — so treat them as the comparison target, not as exact ground truth. All METR intervals
are 80 % Wald, which is why `cotctl.eval` reports the same.

Two deliberate differences from METR's setup are flagged wherever these numbers are used:

* Our CoTControl eval draws 300 questions per mode (2,700 rollouts) rather than METR's ~100
  per mode (900 total), for per-mode power on a model whose baseline sits near the floor.
* METR's loader read only `answer_options`, so its MMLU-Pro prompts carried no answer choices;
  we follow upstream CoTControl and include them.
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

    @property
    def has_ft(self) -> bool:
        return self.cotcontrol_ft240 is not None


# Percentages, as published.
METR_RESULTS: tuple[MetrRow, ...] = (
    MetrRow("Qwen3-8B", 1.1, 20.9, 5.6, 43.8),
    MetrRow("Qwen3-32B", 3.7, 28.9, 9.8, 55.3),
    MetrRow("GPT-OSS-20B", 2.1, 15.0, 7.3, 50.7),
    MetrRow("GPT-OSS-120B", 4.4, 23.7, 13.1, 49.0),
    MetrRow("Qwen3.5-4B", 0.0, 9.4),   # baseline only
    MetrRow("Qwen3.5-27B", 1.3, 9.9),  # baseline only
)

# The Qwen3.5 models bracketing our 9B target; PLAN.md's sanity check for the baseline.
EXPECTED_BASELINE_RANGE = {
    "cotcontrol": (0.0, 1.3),
    "reasonif": (9.4, 9.9),
}


def _fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.1f}"


def comparison_table(ours_cotcontrol: float | None, ours_reasonif: float | None) -> str:
    """Markdown table putting our Qwen3.5-9B baseline next to METR's published models."""
    lines = [
        "| model | CoTControl base % | ReasonIF base % | CoTControl FT@240 % | ReasonIF FT@240 % |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in METR_RESULTS:
        marker = " *(brackets ours)*" if r.model.startswith("Qwen3.5") else ""
        lines.append(
            f"| {r.model}{marker} | {_fmt(r.cotcontrol_base)} | {_fmt(r.reasonif_base)} | "
            f"{_fmt(r.cotcontrol_ft240)} | {_fmt(r.reasonif_ft240)} |"
        )
    lines.append(
        f"| **Qwen3.5-9B (this replication)** | **{_fmt(ours_cotcontrol)}** | "
        f"**{_fmt(ours_reasonif)}** | — | — |"
    )
    return "\n".join(lines)


def sanity_check(ours_cotcontrol: float | None, ours_reasonif: float | None, slack: float = 3.0) -> list[str]:
    """PLAN.md's baseline sanity check: a 9B should land between the 4B and 27B results.

    `slack` (percentage points) allows for the different eval size, the MMLU-Pro choices
    deviation, and the fact that METR's numbers were digitised from figures.
    """
    notes = []
    for suite, value in (("cotcontrol", ours_cotcontrol), ("reasonif", ours_reasonif)):
        if value is None:
            notes.append(f"{suite}: no value to check")
            continue
        lo, hi = EXPECTED_BASELINE_RANGE[suite]
        if lo - slack <= value <= hi + slack:
            notes.append(f"{suite}: {value:.1f} % is within [{lo}, {hi}] ±{slack:g} — as expected")
        else:
            notes.append(
                f"{suite}: {value:.1f} % is OUTSIDE [{lo}, {hi}] ±{slack:g} "
                f"(METR's Qwen3.5-4B / Qwen3.5-27B) — investigate before trusting the run"
            )
    return notes
