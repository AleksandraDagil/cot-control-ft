"""LoRA SFT for Qwen3.5-9B on the ReasonIF controllability dataset.

Hyperparameters from PLAN.md / METR: rank 32, lr 1e-4, effective batch 4 (bs 1 x grad-accum 4),
Adam betas (0.9, 0.95), 1 epoch, max_len 8192, adapters saved at steps 60/120/180/final. METR's
headline is **step 60** — 60 steps x batch 4 = 240 examples, the "~240 SFT examples" of the blog.

LoRA targets every linear in the language model and nothing else: Qwen3.5-9B ships a vision
tower and an MTP head in the same checkpoint, both irrelevant here and both left frozen.

Weights & Biases is required, not optional (PLAN.md P3): a run without its loss-mask chart and
checkpoint artifacts is not reproducible. `WANDB_MODE=offline` works if the host has no network.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

# Every linear leaf in the language model. in_proj_*/out_proj belong to the gated-delta-net
# linear-attention layers (3 of every 4 blocks); q/k/v/o_proj to the full-attention blocks.
TARGET_MODULES = (
    "q_proj", "k_proj", "v_proj", "o_proj",
    "in_proj_qkv", "in_proj_z", "in_proj_b", "in_proj_a", "out_proj",
    "gate_proj", "up_proj", "down_proj",
)
EXCLUDE_PATTERN = re.compile(r"(^|\.)(visual|mtp)(\.|$)")


@dataclass
class TrainConfig:
    model: str = "Qwen/Qwen3.5-9B"
    data: str = "data/sft/qwen3.5-9b_reasonif.jsonl"
    out_dir: str = "results/ckpts"
    max_len: int = 8192
    lora_r: int = 32
    lora_alpha: int = 32
    lora_dropout: float = 0.0
    lr: float = 1e-4
    batch_size: int = 1
    grad_accum: int = 4
    epochs: int = 1
    adam_beta1: float = 0.9
    adam_beta2: float = 0.95
    max_grad_norm: float = 1.0
    warmup_ratio: float = 0.0
    seed: int = 42
    # METR's headline is step 60 (240 examples). We also push weights every `push_every` steps
    # so the training curve has checkpoints behind it, not just four points.
    checkpoint_steps: tuple[int, ...] = (60, 120, 180)
    push_every: int = 30
    wandb_project: str = "cot-control-ft"
    wandb_mode: str | None = None
    log_every: int = 1

    @property
    def effective_batch(self) -> int:
        return self.batch_size * self.grad_accum


def target_module_names(model) -> list[str]:
    """Fully-qualified linear names to adapt: language model only, never vision or MTP."""
    import torch

    out = []
    for name, mod in model.named_modules():
        if not isinstance(mod, torch.nn.Linear):
            continue
        if EXCLUDE_PATTERN.search(name) or name.endswith("lm_head"):
            continue
        if name.split(".")[-1] in TARGET_MODULES:
            out.append(name)
    return out


def dataset_fingerprint(path: Path | str) -> str:
    """Content hash of the training file, so a run can be tied to the exact data."""
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def chunked_causal_loss(model, batch: dict, chunk: int = 512, ignore_index: int = -100):
    """Cross-entropy without materialising the full logits tensor.

    Qwen3.5's vocabulary is 248,320. For a 4k-token sequence the logits alone are ~2 GB in
    bf16, and `cross_entropy` upcasts to fp32 and keeps a gradient, which OOMs a 32 GB card
    once 18 GB of weights are resident. Running the LM head over slices of the sequence keeps
    peak logit memory at `chunk x vocab` instead of `seq_len x vocab`.

    The returned value is the token-mean loss over supervised positions, identical to what
    `ForCausalLMLoss` computes -- the sum is accumulated over chunks and divided once at the
    end, so chunk boundaries cannot reweight it.
    """
    import torch
    import torch.nn.functional as F

    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    body, head = base.model, base.lm_head

    hidden = body(
        input_ids=batch["input_ids"], attention_mask=batch["attention_mask"], use_cache=False
    ).last_hidden_state

    # Standard causal shift: position t predicts token t+1.
    hidden = hidden[:, :-1, :]
    labels = batch["labels"][:, 1:]
    flat_h = hidden.reshape(-1, hidden.size(-1))
    flat_y = labels.reshape(-1)

    total = flat_h.new_zeros((), dtype=torch.float32)
    n_sup = int((flat_y != ignore_index).sum())
    if n_sup == 0:
        raise ValueError("batch has no supervised tokens; the loss mask is broken")

    for i in range(0, flat_h.size(0), chunk):
        h, y = flat_h[i : i + chunk], flat_y[i : i + chunk]
        if (y != ignore_index).sum() == 0:
            continue
        total = total + F.cross_entropy(
            head(h).float(), y, ignore_index=ignore_index, reduction="sum"
        )
    return total / n_sup
