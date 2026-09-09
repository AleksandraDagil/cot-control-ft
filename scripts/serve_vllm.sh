#!/usr/bin/env bash
# Serve Qwen3.5-9B for eval / SFT rollouts on the RTX 5090.
#
#   scripts/serve_vllm.sh                      # base model
#   scripts/serve_vllm.sh path/to/adapter      # base + one LoRA adapter (named "ft")
#
# --reasoning-parser qwen3 splits the <think> block into message.reasoning_content, which is
# what src/cotctl/inference.py reads. --enable-lora is always on so that base and post-FT evals
# run against an identically-configured server.
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

MODEL="${MODEL:-Qwen/Qwen3.5-9B}"
PORT="${PORT:-8000}"
MAX_LEN="${MAX_LEN:-24576}"
GPU_UTIL="${GPU_UTIL:-0.90}"
ADAPTER="${1:-}"

ARGS=(
  --model "$MODEL"
  --served-model-name "$MODEL"
  --port "$PORT"
  --max-model-len "$MAX_LEN"
  --gpu-memory-utilization "$GPU_UTIL"
  --dtype bfloat16
  --reasoning-parser qwen3
  --enable-lora
  --max-lora-rank 32
  --disable-log-requests
)

if [[ -n "$ADAPTER" ]]; then
  ARGS+=(--lora-modules "ft=$ADAPTER")
  echo "serving $MODEL + LoRA adapter 'ft' from $ADAPTER"
else
  echo "serving $MODEL (base)"
fi

exec vllm serve "${ARGS[@]}"
