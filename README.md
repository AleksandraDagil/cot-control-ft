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

### Actual install on skynet 3 (2026-09-09)

The `--torch-backend=cu128` recipe above does not resolve: the current vLLM nightly requires
`torch==2.13.0`, which is not on the cu128 index. PyPI's torch 2.13.0 is a **CUDA 13** build,
which the host driver (595.84 / CUDA 13.2) supports, so let vLLM pick the torch version:

```bash
uv pip install -e ".[dev,gpu]"
uv pip install -U vllm --extra-index-url https://wheels.vllm.ai/nightly \
  --prerelease=allow --index-strategy unsafe-best-match
uv pip install -U "transformers @ git+https://github.com/huggingface/transformers"  # last
```

Resulting stack: torch 2.13.0+cu130, vLLM 0.29.0, transformers 5.18.0.dev0, peft 0.20.0,
`torch.cuda.get_device_capability() == (12, 0)`.

## Running an eval

```bash
scripts/serve_vllm.sh &                      # base model, or: scripts/serve_vllm.sh path/to/adapter
python scripts/calibrate_number_words.py     # once per model -> data/word_limits_<model>.json
python scripts/run_baseline.py --label base --word-limits data/word_limits_Qwen3.5-9B.json
```

Both are resumable: rollouts are keyed by `(sample_id, mode)` in a JSONL and judge verdicts are
cached by prompt hash, so an interrupted run continues where it stopped. `--grade-only` re-grades
stored rollouts without any inference.
