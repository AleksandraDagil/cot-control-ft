"""Plan SFT assignments and assemble training rows.

Mirrors METR's `sft_builder.plan_assignments`: questions are deduplicated and used **at most
once**, so there is a 1:1 mapping between questions and SFT rows; mode labels are split evenly
and shuffled globally (seed 42) so the dataset is not ordered by mode. Constraint arguments
(which language, which end phrase) are drawn from real ReasonIF rows of that mode rather than
invented, so the instruction wording matches the eval exactly.

A training row is

    user      : the full ReasonIF prompt, instruction included
    assistant : <think>\\n{edited reasoning}\\n</think>\\n\\n{answer from stage 1}

with loss on the assistant tokens only (applied at training time, not here).
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..datasets import load_reasonif
from ..prompts import REASONIF_INSTRUCTION_TYPES, reasonif_baseline_prompt, reasonif_prompt

log = logging.getLogger(__name__)


@dataclass
class Assignment:
    row_idx: int
    question: str
    mode: str
    constraint_args: dict | None
    instruction: str
    question_id: str = ""

    def __post_init__(self):
        if not self.question_id:
            self.question_id = question_id(self.question)

    @property
    def stage1_prompt(self) -> str:
        """Instruction-stripped prompt used for the Stage-1 rollout (METR: the constraint is
        applied by editing afterwards, never by asking for it up front)."""
        return reasonif_baseline_prompt(self.question)

    @property
    def training_prompt(self) -> str:
        """The full ReasonIF prompt, with the instruction, that the model is trained on."""
        return reasonif_prompt(self.question, self.instruction)


def question_id(question: str) -> str:
    """Stable id from the text, so cached rollouts survive pool reordering or refiltering."""
    return hashlib.sha256(question.strip().encode()).hexdigest()[:16]


def even_mode_counts(total: int, modes: list[str]) -> dict[str, int]:
    """Split `total` across `modes`; remainder to the first modes, deterministically."""
    n = len(modes)
    if n == 0 or total <= 0:
        return {}
    base, rem = divmod(total, n)
    return {m: base + (1 if i < rem else 0) for i, m in enumerate(modes)}


def reasonif_templates() -> dict[str, list[dict]]:
    """Real ReasonIF rows grouped by instruction type, as the source of constraint args."""
    out: dict[str, list[dict]] = {}
    for s in load_reasonif():
        itype = s.metadata["instruction_type"]
        instruction = s.metadata["prompt"].split("**", 2)
        out.setdefault(itype, []).append(
            {
                "constraint_args": s.metadata.get("constraint_args"),
                # The instruction sentence sits between the ** ** markers of the eval prompt.
                "instruction": instruction[1] if len(instruction) >= 2 else "",
            }
        )
    return out


def plan_assignments(
    questions: list[str],
    n_rows: int | None = None,
    seed: int = 42,
    modes: tuple[str, ...] = REASONIF_INSTRUCTION_TYPES,
) -> list[Assignment]:
    """Pair each unique question with exactly one mode.

    `n_rows` defaults to every unique question in the pool. Raises if more rows are requested
    than there are unique questions, rather than silently reusing one (which would put the same
    question in the dataset twice under different constraints).
    """
    rng = random.Random(seed)

    seen: set[str] = set()
    unique: list[str] = []
    for q in questions:
        q = (q or "").strip()
        if q and q not in seen:
            seen.add(q)
            unique.append(q)

    total = len(unique) if n_rows is None else int(n_rows)
    if total > len(unique):
        raise ValueError(
            f"requested {total} rows but the pool has only {len(unique)} unique questions; "
            "enlarge the pool or lower n_rows"
        )

    labels: list[str] = []
    for mode, k in even_mode_counts(total, list(modes)).items():
        labels.extend([mode] * k)

    rng.shuffle(labels)
    order = list(range(len(unique)))
    rng.shuffle(order)

    templates = reasonif_templates()
    out: list[Assignment] = []
    for row_idx, (mode, q_idx) in enumerate(zip(labels, order)):
        pool = templates.get(mode) or []
        if not pool:
            raise ValueError(f"no ReasonIF template rows for mode {mode}")
        t = rng.choice(pool)
        out.append(
            Assignment(
                row_idx=row_idx,
                question=unique[q_idx],
                mode=mode,
                constraint_args=dict(t["constraint_args"]) if t["constraint_args"] else {},
                instruction=t["instruction"],
            )
        )
    return out


# ---------------------------------------------------------------------------
# training rows
# ---------------------------------------------------------------------------


@dataclass
class TrainingRow:
    row_idx: int
    question_id: str
    mode: str
    prompt: str
    reasoning: str
    answer: str
    constraint_args: dict = field(default_factory=dict)

    @property
    def assistant(self) -> str:
        """Qwen3.5's assistant rendering: the think block, then the answer."""
        return f"<think>\n{self.reasoning}\n</think>\n\n{self.answer}"

    def to_messages(self) -> dict:
        return {
            "messages": [
                {"role": "user", "content": self.prompt},
                {"role": "assistant", "content": self.assistant},
            ],
            "row_idx": self.row_idx,
            "question_id": self.question_id,
            "mode": self.mode,
            "constraint_args": self.constraint_args,
        }


def write_training_jsonl(rows: list[TrainingRow], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r.to_messages(), ensure_ascii=False) + "\n")
    return path
