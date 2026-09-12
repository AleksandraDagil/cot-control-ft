#!/usr/bin/env python3
"""Merge a LoRA adapter into the base weights and save a standalone model.

vLLM silently ignored this project's adapters when served via `--enable-lora` (see
METHODOLOGY.md). Merging sidesteps its LoRA path entirely: the served model is ordinary dense
weights, so there is nothing left to silently skip. Costs ~19 GB of disk per checkpoint and a
server restart per evaluation, which is a fair price for numbers that are unambiguous.

    python scripts/merge_adapter.py results/ckpts/step-60 results/merged/step-60
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adapter")
    ap.add_argument("out")
    ap.add_argument("--base", default="Qwen/Qwen3.5-9B")
    args = ap.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    out = Path(args.out)
    if (out / "config.json").exists():
        print(f"{out} already exists; nothing to do")
        return 0

    print(f"loading base {args.base}")
    model = AutoModelForCausalLM.from_pretrained(args.base, dtype=torch.bfloat16, device_map="cpu")
    print(f"applying adapter {args.adapter}")
    model = PeftModel.from_pretrained(model, args.adapter)
    print("merging")
    model = model.merge_and_unload()

    out.mkdir(parents=True, exist_ok=True)
    print(f"saving to {out}")
    model.save_pretrained(out, safe_serialization=True)
    AutoTokenizer.from_pretrained(args.base).save_pretrained(out)
    # The chat template lives beside the tokenizer and the eval depends on it prefilling <think>.
    for name in ("chat_template.jinja",):
        src = Path(args.adapter) / name
        if src.exists():
            shutil.copy(src, out / name)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
