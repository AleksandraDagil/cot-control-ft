# cot-control-ft

Independent replication of METR's *Fine-tuning experiments on CoT controllability*
(https://metr.org/blog/2026-04-01-fine-tuning-cot-controllability/) on **Qwen3.5-9B**, single RTX 5090.

Own pipeline; the two upstream eval suites (ReasonIF, CoTControl) are reimplemented in `src/cotctl/graders/`
and `src/cotctl/prompts.py` and kept byte-compatible via parity tests against pinned upstream clones.
See `PLAN.md` for the full recipe, decisions and phases.

## Layout

```
src/cotctl/          prompts, datasets, graders, inference, eval, sft/, train/, analysis/
data/upstream/       vendored ReasonIF json + CoTControl CSVs (provenance in SOURCES.md)
tests/               parity tests (need ./ref clones, see below)
scripts/             CLI entrypoints
configs/             run configs
```

## Setup (CPU-side / tests)

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]"
# reference clones used only by tests (gitignored)
mkdir -p ref && cd ref && \
  git clone --depth 1 https://github.com/ykwon0407/reasonIF.git && \
  git clone --depth 1 https://github.com/YuehHanChen/CoTControl.git && \
  git clone --depth 1 https://github.com/keing1/cot_controllability.git && cd ..
pytest
```

## Setup (GPU host)

Blackwell (sm_120) needs a CUDA 12.8+ torch; Qwen3.5 needs transformers `main` and a vLLM nightly:

```bash
uv pip install -e ".[dev,gpu]" --torch-backend=cu128
uv pip install -U "transformers @ git+https://github.com/huggingface/transformers"
uv pip install -U vllm --extra-index-url https://wheels.vllm.ai/nightly
cp .env.example .env   # OPENAI_API_KEY
```
