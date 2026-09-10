# Execution host (skynet 3)

Recorded at P0, 2026-09-09.

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 5090, 32 GB (sm_120 / Blackwell) |
| Driver | 595.84 |
| CUDA (driver max) | 13.2 |
| System CUDA toolkit | none (`nvcc` absent) — torch ships its own cu128 runtime |
| Python | 3.12.3 (`/usr/bin/python3.12`), venv via uv 0.8.4 |
| RAM | 188 GB |
| Disk | `/` 1.8 T, ~115 G free at P0 |

Model weights (~19.3 GB bf16) + the cu128 wheel set are the bulk of the disk use; keep an eye on
free space before adding checkpoints (`results/ckpts/`).

## Reference clones (`ref/`, gitignored)

Cloned fresh on this host; SHAs match the pins already recorded in `data/upstream/SOURCES.md`,
so the vendored data and the parity tests refer to the same upstream revisions:

- `ref/reasonIF` — 706b953feb9408a802e1ad6972c10ad7fbad3da8
- `ref/CoTControl` — 5d78aeffe0152ba087c2d31cd07712d029c64785
- `ref/cot_controllability` — 9d2c4eccb7d8b91371f23bc1e04fef1bd75f38fa

`pytest` → 495 passed with these clones present.

## GPU stack (installed P0)

| package | version |
|---|---|
| torch | 2.13.0+cu130 (`torch.version.cuda` 13.0) |
| vLLM | 0.29.0 |
| transformers | 5.18.0.dev0 (git main @ 4815a0a) |
| peft | 0.20.0 |

`torch.cuda.is_available()` True, `get_device_capability()` == `(12, 0)` (sm_120).

**The README's `--torch-backend=cu128` recipe does not resolve.** The current vLLM nightly
requires `torch==2.13.0`, which the cu128 index does not carry; PyPI's torch 2.13.0 is a CUDA 13
build (`nvidia-*-cu13`), supported by driver 595.84 / CUDA 13.2. Install order that works is in
the README — transformers main goes **last**, or vLLM pins it back to the PyPI release.

Verified before first launch:

- `Qwen3_5ForConditionalGeneration` is in `ModelRegistry.get_supported_archs()`.
- `--reasoning-parser qwen3` resolves to `vllm.parser.engine.adapters.Qwen3ParserReasoningAdapter`
  (registered lazily, so `ReasoningParserManager.reasoning_parsers` reads empty until resolution).
- `--disable-log-requests` was removed in vLLM 0.29; `scripts/serve_vllm.sh` uses
  `--no-enable-log-requests`.

## Judge LLM

OpenRouter (`https://openrouter.ai/api/v1`), model `openai/gpt-5-mini` — upstream's and METR's
judge, reached through an OpenAI-compatible gateway. Key lives in `.env` (`OPENROUTER_API_KEY`,
gitignored). `src/cotctl/judge.py` falls back to a direct `OPENAI_API_KEY` if that is what is set.
Verified live: a "thinking about my cat" trace judged compliant, an actual solution judged
non-compliant.

## P0 smoke test (2026-09-10)

`scripts/smoke_test.py --batch 32` — all checks passed against the live server.

- `<think>` parsing: reasoning ~7.9k chars, answer ~450 chars, tags stripped by the parser.
- CoTControl-shaped MCQ: think block closed, `ANSWER: A` extractable.
- Throughput: **~2,325 output tok/s at batch 32** (32 rollouts, 1024-token cap, 14.0 s).
  Projected whole-project inference (17,000 rollouts x ~6k tokens): **~12 GPU-hours**.
- KV cache 7.25 GiB / 208,200 tokens; max concurrency 8.47x at 24,576 tokens per request.

### Two launch problems worth remembering

**FlashInfer would not build for sm_120.** It failed first with `"FlashInfer requires GPUs with
sm75 or higher"` on an sm_120 card — misleading: the arch check reports on whichever nvcc it
finds, and `get_cuda_path()` resolved `/usr/local/cuda`, a **CUDA 12.8** system toolkit (nvcc
present, just not on PATH). sm_120 needs >= 12.9, so the target-arch set came back empty.
Pointing `CUDA_HOME` at the venv's cu13 tree fixed detection (CUDA 13.4, arch `(12, '0f')`),
but then Ninja failed: FlashInfer 0.6.18 bundles CCCL headers that reject nvcc 13.4-rc
("CUDA compiler and CUDA toolkit headers are incompatible"). Attention already runs on
FLASH_ATTN and only the *sampler* wanted FlashInfer, so `serve_vllm.sh` sets
`VLLM_USE_FLASHINFER_SAMPLER=0` and uses vLLM's native top-k/top-p. Same sampling semantics.
Revisit if `nvidia-cuda-nvcc` is ever pinned back to 13.0.x.

**vLLM 0.29 renamed the reasoning field.** The qwen3 parser puts the think block on
`message.reasoning`, not `message.reasoning_content`. Reading only the old name made every
rollout look like `think_status="missing"` with the reasoning landing in `content` — which
would have silently zeroed every compliance rate. `cotctl.inference.reasoning_field` now reads
whichever is populated.

**Truncation is the thing to watch.** Qwen3.5-9B spends ~3-4k tokens reasoning on even a
trivial MCQ, and hit the cap mid-`<think>` at 2048. Rollouts that truncate inside the think
block are `think_status="unclosed"` and are excluded from compliance rates, so the truncation
rate is reported alongside every result.
