# step-150 vs METR

| model | CoTControl base % | ReasonIF base % | CoTControl FT@240 % | ReasonIF FT@240 % | |
|---|---:|---:|---:|---:|---|
| Qwen3-8B | 1.1 | 20.9 | 5.6 | 43.8 |  |
| Qwen3-32B | 3.7 | 28.9 | 9.8 | 55.3 |  |
| GPT-OSS-20B | 2.1 | 15.0 | 7.3 | 50.7 |  |
| GPT-OSS-120B | 4.4 | 23.7 | 13.1 | 49.0 |  |
| Qwen3.5-4B *(brackets ours)* | 0.0 | 9.4 | — | — | baseline only |
| Qwen3.5-27B *(brackets ours)* | 1.3 | 9.9 | — | — | baseline only |
| **Qwen3.5-9B (ours, step-150)** | **—** | **7.0** | — | — | this replication |


Baseline sanity check (PLAN.md):

- cotcontrol: no value to check
- reasonif: 7.0 % is within [9.4, 9.9] ±3 — as expected

ReasonIF macro (unweighted over the 6 instruction types): 6.7 %

## reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 46 | 6.5 | 1.9–11.2 | 82.6 | 87.0 | 6.1 | 10326 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 87.2 | 100.0 | 9.3 | 8685 |
| json_format | 47 | 43 | 0.0 | 0.0–0.0 | 88.1 | 81.4 | 10.6 | 12234 |
| no_comma | 56 | 47 | 0.0 | 0.0–0.0 | 88.9 | 95.7 | 17.9 | 11529 |
| number_words | 53 | 50 | 12.0 | 6.1–17.9 | 87.8 | 76.0 | 7.5 | 9309 |
| reasoning_language | 52 | 46 | 21.7 | 13.9–29.5 | 86.4 | 87.0 | 15.4 | 7937 |

**Macro-average compliance: 6.7 %** (unweighted mean over modes)

