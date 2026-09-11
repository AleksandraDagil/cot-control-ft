#!/usr/bin/env bash
# P4: evaluate the fine-tuned checkpoints against the identical baseline question sets.
#
# Scope (chosen 2026-09-11): ReasonIF on every checkpoint, because it is cheap (~1.5 h) and is
# the in-distribution metric where the effect should be largest; CoTControl at full 300/mode on
# step-60 only, which is METR's headline (60 steps x batch 4 = 240 examples) and the expensive
# OOD number at ~12.5 h.
#
# Comparisons are paired: the same 300 ReasonIF prompts and the same 300 CoTControl questions
# as the baseline, with the same calibrated word limits, so base-vs-checkpoint differences are
# not confounded by sampling.
set -uo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

LIMITS=data/word_limits_Qwen3.5-9B.json
CKPTS=(step-30 step-60 step-90 step-120 step-150 step-180 step-210 step-final)
log() { echo "[$(date -Is)] $*"; }

for c in "${CKPTS[@]}"; do
  log "=== ReasonIF on $c ==="
  python scripts/run_baseline.py --label "$c" --model "$c" --suites reasonif --word-limits "$LIMITS" \
    2>&1 | grep -vE "HTTP Request" | tail -20
done

log "=== CoTControl (300/mode) on step-60 ==="
python scripts/run_baseline.py --label step-60 --model step-60 --suites cotcontrol --word-limits "$LIMITS" \
  2>&1 | grep -vE "HTTP Request" | tail -30

log "=== P4 generation complete ==="
