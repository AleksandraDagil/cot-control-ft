# step-90 vs METR

| model | CoTControl base % | ReasonIF base % | CoTControl FT@240 % | ReasonIF FT@240 % | |
|---|---:|---:|---:|---:|---|
| Qwen3-8B | 1.1 | 20.9 | 5.6 | 43.8 |  |
| Qwen3-32B | 3.7 | 28.9 | 9.8 | 55.3 |  |
| GPT-OSS-20B | 2.1 | 15.0 | 7.3 | 50.7 |  |
| GPT-OSS-120B | 4.4 | 23.7 | 13.1 | 49.0 |  |
| Qwen3.5-4B *(brackets ours)* | 0.0 | 9.4 | — | — | baseline only |
| Qwen3.5-27B *(brackets ours)* | 1.3 | 9.9 | — | — | baseline only |
| **Qwen3.5-9B (ours, step-90)** | **—** | **7.1** | — | — | this replication |


Baseline sanity check (PLAN.md):

- cotcontrol: no value to check
- reasonif: 7.1 % is within [9.4, 9.9] ±3 — as expected

ReasonIF macro (unweighted over the 6 instruction types): 6.9 %

## reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 46 | 8.7 | 3.4–14.0 | 86.4 | 82.6 | 10.2 | 10456 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 89.7 | 92.3 | 9.3 | 8584 |
| json_format | 47 | 43 | 0.0 | 0.0–0.0 | 82.9 | 86.0 | 8.5 | 11573 |
| no_comma | 56 | 46 | 0.0 | 0.0–0.0 | 91.1 | 93.5 | 19.6 | 15392 |
| number_words | 53 | 50 | 8.0 | 3.1–12.9 | 87.8 | 80.0 | 7.5 | 9425 |
| reasoning_language | 52 | 44 | 25.0 | 16.6–33.4 | 90.7 | 86.4 | 17.3 | 9072 |

**Macro-average compliance: 6.9 %** (unweighted mean over modes)

