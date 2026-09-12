# step-210_reasonif_metrcap16384

### step-210_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 36 | 8.3 | 2.4–14.2 | 84.4 | 83.3 | 26.5 | 9523 |
| english_capital | 43 | 29 | 0.0 | 0.0–0.0 | 89.2 | 96.6 | 32.6 | 7765 |
| json_format | 47 | 27 | 0.0 | 0.0–0.0 | 88.1 | 88.9 | 42.6 | 11079 |
| no_comma | 56 | 35 | 0.0 | 0.0–0.0 | 90.0 | 97.1 | 37.5 | 13586 |
| number_words | 53 | 34 | 14.7 | 6.9–22.5 | 85.1 | 94.1 | 35.8 | 9118 |
| reasoning_language | 52 | 34 | 26.5 | 16.8–36.2 | 87.8 | 88.2 | 34.6 | 9197 |

**Macro-average compliance: 8.3 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 17 | 17 | 82.4 | 70.5–94.2 | 2979.4 | 352.5 |
| non-compliant | 178 | 178 | 89.9 | 87.0–92.8 | 2934.4 | 246.1 |
| ungradeable | 105 | 67 | 82.1 | 76.1–88.1 | 11616.4 | 410.2 |

Accuracy gap (non-compliant − compliant): **+7.5 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 296–1515 | 868 | 100.0 | 6.7 | 0.0 |
| 2 | 60 | 1519–3246 | 2679 | 83.3 | 11.7 | 0.0 |
| 3 | 60 | 3256–5672 | 4525 | 86.7 | 8.5 | 1.7 |
| 4 | 60 | 5851–10331 | 7993 | 83.3 | 6.2 | 73.3 |
| 5 | 60 | 10335–21178 | 14064 | 77.3 | — | 100.0 |
