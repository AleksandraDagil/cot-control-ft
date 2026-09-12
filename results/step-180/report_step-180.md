# step-180 vs METR

| model | CoTControl base % | ReasonIF base % | CoTControl FT@240 % | ReasonIF FT@240 % | |
|---|---:|---:|---:|---:|---|
| Qwen3-8B | 1.1 | 20.9 | 5.6 | 43.8 |  |
| Qwen3-32B | 3.7 | 28.9 | 9.8 | 55.3 |  |
| GPT-OSS-20B | 2.1 | 15.0 | 7.3 | 50.7 |  |
| GPT-OSS-120B | 4.4 | 23.7 | 13.1 | 49.0 |  |
| Qwen3.5-4B *(brackets ours)* | 0.0 | 9.4 | — | — | baseline only |
| Qwen3.5-27B *(brackets ours)* | 1.3 | 9.9 | — | — | baseline only |
| **Qwen3.5-9B (ours, step-180)** | **—** | **6.5** | — | — | this replication |


Baseline sanity check (PLAN.md):

- cotcontrol: no value to check
- reasonif: 6.5 % is within [9.4, 9.9] ±3 — as expected

ReasonIF macro (unweighted over the 6 instruction types): 6.3 %

## reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 44 | 2.3 | 0.0–5.2 | 86.4 | 84.1 | 10.2 | 10495 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 94.9 | 76.9 | 9.3 | 7730 |
| json_format | 47 | 41 | 0.0 | 0.0–0.0 | 87.2 | 82.9 | 14.9 | 11585 |
| no_comma | 56 | 48 | 2.1 | 0.0–4.7 | 89.6 | 91.7 | 14.3 | 14026 |
| number_words | 53 | 48 | 10.4 | 4.8–16.1 | 89.6 | 85.4 | 9.4 | 9247 |
| reasoning_language | 52 | 43 | 23.3 | 15.0–31.5 | 90.7 | 93.0 | 17.3 | 7867 |

**Macro-average compliance: 6.3 %** (unweighted mean over modes)

