"""Tokenise SFT rows with assistant-only loss masking.

The single most important thing in this file is the mask. Loss must fall on the assistant turn
only — the reasoning and the answer — never on the user prompt. If the mask silently covers
everything, the model trains on predicting the question too and the run is quietly invalid; if
it covers nothing, there is no gradient at all. Both look like "training ran fine", so
`masked_fraction` is logged per batch and asserted in tests.

Rows longer than `max_len` are **dropped, not truncated**. A truncated example ends mid-reasoning
with no `</think>` and no answer, which would teach exactly the failure mode the eval measures.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

ASSISTANT_HEADER = "<|im_start|>assistant\n"
IGNORE_INDEX = -100


@dataclass
class Example:
    input_ids: list[int]
    labels: list[int]
    mode: str
    row_idx: int

    @property
    def n_supervised(self) -> int:
        return sum(1 for l in self.labels if l != IGNORE_INDEX)

    @property
    def masked_fraction(self) -> float:
        return 1.0 - self.n_supervised / max(1, len(self.input_ids))


def render(tokenizer, messages: list[dict]) -> tuple[str, str]:
    """Return `(full_text, prompt_text)`; the prompt is everything up to the assistant content."""
    full = tokenizer.apply_chat_template(messages, tokenize=False)
    idx = full.rfind(ASSISTANT_HEADER)
    if idx < 0:
        raise ValueError("assistant header not found in rendered chat template")
    return full, full[: idx + len(ASSISTANT_HEADER)]


def encode(tokenizer, messages: list[dict], max_len: int) -> tuple[list[int], list[int]] | None:
    """Tokenise one row into (input_ids, labels). None if it exceeds `max_len`.

    The prompt is tokenised separately and its length used as the mask boundary, rather than
    string-matching in token space, so the boundary cannot drift if the template changes.
    """
    full, prompt = render(tokenizer, messages)
    ids = tokenizer(full, add_special_tokens=False)["input_ids"]
    if len(ids) > max_len:
        return None
    n_prompt = len(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    if n_prompt >= len(ids):
        raise ValueError("prompt is not shorter than the full sequence; masking would be empty")
    labels = [IGNORE_INDEX] * n_prompt + ids[n_prompt:]
    return ids, labels


def load_examples(path: Path | str, tokenizer, max_len: int = 8192) -> tuple[list[Example], dict]:
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    out, dropped = [], []
    for r in rows:
        enc = encode(tokenizer, r["messages"], max_len)
        if enc is None:
            dropped.append({"row_idx": r.get("row_idx"), "mode": r.get("mode")})
            continue
        ids, labels = enc
        out.append(Example(ids, labels, r.get("mode", ""), r.get("row_idx", -1)))
    stats = {
        "n_rows": len(rows),
        "n_kept": len(out),
        "n_dropped_too_long": len(dropped),
        "dropped": dropped,
        "max_len": max_len,
        "mean_supervised_tokens": round(sum(e.n_supervised for e in out) / max(1, len(out)), 1),
        "mean_masked_fraction": round(sum(e.masked_fraction for e in out) / max(1, len(out)), 4),
    }
    log.info(
        "loaded %d/%d rows (dropped %d over %d tokens); mean supervised tokens %.0f, masked %.1f%%",
        stats["n_kept"], stats["n_rows"], stats["n_dropped_too_long"], max_len,
        stats["mean_supervised_tokens"], 100 * stats["mean_masked_fraction"],
    )
    return out, stats


def collate(batch: list[Example], pad_token_id: int) -> dict:
    n = max(len(e.input_ids) for e in batch)
    input_ids, labels, attn = [], [], []
    for e in batch:
        pad = n - len(e.input_ids)
        input_ids.append(e.input_ids + [pad_token_id] * pad)
        labels.append(e.labels + [IGNORE_INDEX] * pad)   # padding is never supervised
        attn.append([1] * len(e.input_ids) + [0] * pad)
    import torch

    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
        "attention_mask": torch.tensor(attn, dtype=torch.long),
    }
