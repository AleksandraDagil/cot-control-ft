# step-210_reasonif

### step-210_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 46 | 6.5 | 1.9–11.2 | 84.4 | 82.6 | 6.1 | 9523 |
| english_capital | 43 | 38 | 0.0 | 0.0–0.0 | 89.2 | 94.7 | 14.0 | 7765 |
| json_format | 47 | 42 | 0.0 | 0.0–0.0 | 88.1 | 85.7 | 10.6 | 11079 |
| no_comma | 56 | 50 | 0.0 | 0.0–0.0 | 90.0 | 86.0 | 10.7 | 13586 |
| number_words | 53 | 49 | 10.2 | 4.7–15.7 | 85.1 | 83.7 | 11.3 | 9118 |
| reasoning_language | 52 | 42 | 21.4 | 13.3–29.5 | 87.8 | 90.5 | 21.2 | 9197 |

**Macro-average compliance: 6.4 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 17 | 17 | 82.4 | 70.5–94.2 | 2979.4 | 352.5 |
| non-compliant | 250 | 245 | 87.8 | 85.1–90.4 | 4993.9 | 347.5 |
| ungradeable | 33 | 0 | — | — | 14956.3 | 0.0 |

Accuracy gap (non-compliant − compliant): **+5.4 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 296–1515 | 868 | 100.0 | 6.7 | 0.0 |
| 2 | 60 | 1519–3246 | 2679 | 83.3 | 11.7 | 0.0 |
| 3 | 60 | 3256–5672 | 4525 | 86.7 | 8.3 | 0.0 |
| 4 | 60 | 5851–10331 | 7993 | 83.3 | 1.7 | 0.0 |
| 5 | 60 | 10335–21178 | 14064 | 77.3 | 0.0 | 61.7 |
