# step-60 vs METR

| model | CoTControl base % | ReasonIF base % | CoTControl FT@240 % | ReasonIF FT@240 % | |
|---|---:|---:|---:|---:|---|
| Qwen3-8B | 1.1 | 20.9 | 5.6 | 43.8 |  |
| Qwen3-32B | 3.7 | 28.9 | 9.8 | 55.3 |  |
| GPT-OSS-20B | 2.1 | 15.0 | 7.3 | 50.7 |  |
| GPT-OSS-120B | 4.4 | 23.7 | 13.1 | 49.0 |  |
| Qwen3.5-4B *(brackets ours)* | 0.0 | 9.4 | — | — | baseline only |
| Qwen3.5-27B *(brackets ours)* | 1.3 | 9.9 | — | — | baseline only |
| **Qwen3.5-9B (ours, step-60)** | **—** | **23.7** | — | — | this replication |


Baseline sanity check (PLAN.md):

- cotcontrol: no value to check
- reasonif: 23.7 % is OUTSIDE [9.4, 9.9] ±3 (METR's Qwen3.5-4B / Qwen3.5-27B) — investigate before trusting the run

ReasonIF macro (unweighted over the 6 instruction types): 22.8 %

## reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 47 | 23.4 | 15.5–31.3 | 82.2 | 51.1 | 8.2 | 8721 |
| english_capital | 43 | 38 | 15.8 | 8.2–23.4 | 92.1 | 57.9 | 11.6 | 8057 |
| json_format | 47 | 42 | 2.4 | 0.0–5.4 | 92.9 | 47.6 | 10.6 | 10561 |
| no_comma | 56 | 47 | 27.7 | 19.3–36.0 | 93.5 | 51.1 | 17.9 | 11461 |
| number_words | 53 | 52 | 42.3 | 33.5–51.1 | 80.0 | 40.4 | 5.7 | 8166 |
| reasoning_language | 52 | 44 | 25.0 | 16.6–33.4 | 93.0 | 52.3 | 17.3 | 9167 |

**Macro-average compliance: 22.8 %** (unweighted mean over modes)

