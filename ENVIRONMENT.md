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
