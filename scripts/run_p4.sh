#!/usr/bin/env bash
# P4: evaluate fine-tuned checkpoints.
#
# Adapters are served MERGED, not via --enable-lora: vLLM silently ignored the LoRA adapters
# and served the base model, costing ~24 GPU-hours of results that were the base model plus
# sampling noise (METHODOLOGY.md). Merged weights leave nothing to silently skip.
#
# scripts/verify_adapter.py must pass before any eval runs through a server.
set -uo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
LIMITS=data/word_limits_Qwen3.5-9B.json
CKPT="${CKPT:-step-60}"
MERGED="results/merged/$CKPT"
log() { echo "[$(date -Is)] $*"; }

log "=== ReasonIF on $CKPT (merged) ==="
python scripts/run_baseline.py --label "$CKPT" --model "$MERGED" --suites reasonif --word-limits "$LIMITS" \
  2>&1 | grep -vE "HTTP Request" | tail -22

log "=== CoTControl 300/mode on $CKPT (merged) ==="
python scripts/run_baseline.py --label "$CKPT" --model "$MERGED" --suites cotcontrol --word-limits "$LIMITS" \
  2>&1 | grep -vE "HTTP Request" | tail -30

log "=== done $CKPT ==="
