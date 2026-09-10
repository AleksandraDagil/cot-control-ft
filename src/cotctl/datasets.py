"""Dataset loading (ReasonIF json, CoTControl CSVs, Multilingual-Thinking) and sampling."""

from __future__ import annotations

import ast
import csv
import json
import re
import random
from dataclasses import dataclass, field
from pathlib import Path

from .prompts import REASONIF_CONSTRAINT_IDS

REPO_ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = REPO_ROOT / "data" / "upstream"

COTCONTROL_FILES = {
    "cotcontrol/gpqa": "gpqa_w_keyword.csv",
    "cotcontrol/hle": "hle_w_keyword.csv",
    "cotcontrol/mmlu_pro": "mmlu_pro_mini_w_keyword.csv",
}


@dataclass
class Sample:
    id: str
    dataset: str
    question: str
    correct_answer: str
    options: list[str] | None = None
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ReasonIF
# ---------------------------------------------------------------------------


def load_reasonif(path: Path | None = None) -> list[Sample]:
    path = path or UPSTREAM / "reasonif" / "reasonIF_dataset.json"
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    out = []
    for i, r in enumerate(rows):
        cid = r["constraint_name"][0]
        args = r["constraint_args"][0] or None
        out.append(
            Sample(
                id=f"reasonif_{i}",
                dataset="reasonif",
                question=r["question"],
                correct_answer=str(r["answer"]),
                metadata={
                    "source": r["source"],
                    "hf_id": r.get("hf_id", ""),
                    "instruction_type": REASONIF_CONSTRAINT_IDS[cid],
                    "constraint_id": cid,
                    "constraint_args": dict(args) if args else None,
                    "prompt": r["prompt"],
                },
            )
        )
    return out


# ---------------------------------------------------------------------------
# CoTControl QA
# ---------------------------------------------------------------------------


def _parse_list(raw: str | None) -> list | None:
    if not raw or not raw.strip():
        return None
    for parser in (json.loads, ast.literal_eval):
        try:
            v = parser(raw)
        except (ValueError, SyntaxError, TypeError):
            continue
        if isinstance(v, list):
            return v
    return None


def answer_letter(answer: str, options: list[str] | None) -> str | None:
    """Resolve a gold answer to its option letter.

    The three upstream CSVs disagree: `hle` stores a bare letter, while `gpqa` and
    `mmlu_pro_mini` store the answer *text* and expect you to find it among the options.
    Scoring `ANSWER: X` against the first character of an answer string is meaningless for the
    latter two, so resolve to a letter here, once, at load time.

    Returns None when the answer cannot be located among the options, so the caller can treat
    the row as unscorable rather than silently wrong.
    """
    a = (answer or "").strip()
    if not a:
        return None
    # Already a bare letter (hle).
    if len(a) == 1 and a.isalpha():
        return a.upper()
    if not options:
        return None

    def norm(x: str) -> str:
        return re.sub(r"\s+", " ", str(x or "").strip().lower()).strip(" .")

    target = norm(a)
    normed = [norm(o) for o in options]
    if target in normed:
        return chr(ord("A") + normed.index(target))
    # Fall back to a unique containment match: some rows carry trailing whitespace or a
    # trailing period that the option text does not.
    hits = [i for i, o in enumerate(normed) if o and (o == target or o.startswith(target) or target.startswith(o))]
    if len(hits) == 1:
        return chr(ord("A") + hits[0])
    return None


def load_cotcontrol_file(path: Path, dataset_name: str) -> list[Sample]:
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            kw_entries = _parse_list(row.get("keywords_with_synonyms")) or []
            keywords, synonyms = [], {}
            for e in kw_entries:
                kw = e.get("keyword", "")
                if kw:
                    keywords.append(kw)
                    if e.get("synonyms"):
                        synonyms[kw] = e["synonyms"]
            # GPQA/HLE store choices in `answer_options`, MMLU-Pro in `options`.
            options = _parse_list(row.get("answer_options")) or _parse_list(row.get("options"))
            out.append(
                Sample(
                    id=f"{dataset_name}_{i}",
                    dataset=dataset_name,
                    question=row["question"],
                    correct_answer=row["answer"],
                    options=options,
                    metadata={
                        "answer_letter": answer_letter(row["answer"], options),
                        "source": row.get("source", ""),
                        "domain": row.get("domain", ""),
                        "keywords": keywords,
                        "valid_keywords": _parse_list(row.get("valid_keywords")) or [],
                        "synonyms_map": synonyms,
                    },
                )
            )
    return out


def load_cotcontrol(root: Path | None = None) -> list[Sample]:
    root = root or UPSTREAM / "cotcontrol"
    out: list[Sample] = []
    for name, fname in COTCONTROL_FILES.items():
        out.extend(load_cotcontrol_file(root / fname, name))
    return out


def proportional_sample(
    samples: list[Sample], n: int, seed: int = 42, require_valid_keywords: bool = True
) -> list[Sample]:
    """Deterministic stratified draw of `n` samples proportional to per-dataset sizes
    (largest-remainder allocation, groups processed in sorted order). Same algorithm METR used
    for its CoTControl subset, so seed 42 / n 900 reproduces their draw."""
    if require_valid_keywords:
        samples = [s for s in samples if s.metadata.get("valid_keywords")]
    groups: dict[str, list[Sample]] = {}
    for s in samples:
        groups.setdefault(s.dataset, []).append(s)
    total = len(samples)
    if total == 0 or n <= 0:
        return []
    raw = {k: len(v) / total * n for k, v in groups.items()}
    counts = {k: int(v) for k, v in raw.items()}
    remaining = n - sum(counts.values())
    for k in sorted(raw, key=lambda k: raw[k] - counts[k], reverse=True):
        if remaining <= 0:
            break
        counts[k] += 1
        remaining -= 1
    rng = random.Random(seed)
    out: list[Sample] = []
    for k in sorted(groups):
        out.extend(rng.sample(groups[k], min(counts.get(k, 0), len(groups[k]))))
    return out


# ---------------------------------------------------------------------------
# Multilingual-Thinking (SFT prompt pool)
# ---------------------------------------------------------------------------


def load_multilingual_thinking_prompts(cache_dir: Path | None = None) -> list[str]:
    """User prompts from HuggingFaceH4/Multilingual-Thinking (1000 rows), deduplicated, order preserved."""
    from datasets import load_dataset  # lazy: only needed on the GPU host

    ds = load_dataset("HuggingFaceH4/Multilingual-Thinking", split="train", cache_dir=str(cache_dir) if cache_dir else None)
    seen, out = set(), []
    for row in ds:
        q = (row.get("user") or "").strip()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out
