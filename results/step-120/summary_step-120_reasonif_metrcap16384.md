# step-120_reasonif_metrcap16384

### step-120_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 33 | 15.2 | 7.2–23.2 | 82.9 | 97.0 | 32.7 | 10341 |
| english_capital | 43 | 31 | 0.0 | 0.0–0.0 | 89.7 | 87.1 | 27.9 | 8625 |
| json_format | 47 | 29 | 0.0 | 0.0–0.0 | 90.2 | 89.7 | 38.3 | 10795 |
| no_comma | 56 | 33 | 0.0 | 0.0–0.0 | 91.3 | 100.0 | 41.1 | 11007 |
| number_words | 53 | 35 | 14.3 | 6.7–21.9 | 84.8 | 85.7 | 34.0 | 8264 |
| reasoning_language | 52 | 34 | 23.5 | 14.2–32.9 | 86.4 | 88.2 | 34.6 | 10024 |

**Macro-average compliance: 8.8 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 18 | 17 | 94.1 | 86.8–100.0 | 2907.4 | 379.3 |
| non-compliant | 177 | 177 | 89.8 | 86.9–92.7 | 2926.6 | 244.7 |
| ungradeable | 105 | 63 | 79.4 | 72.8–85.9 | 12037.8 | 356.0 |

Accuracy gap (non-compliant − compliant): **-4.3 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 281–1345 | 860 | 96.6 | 8.3 | 0.0 |
| 2 | 60 | 1346–3161 | 2197 | 86.7 | 10.0 | 0.0 |
| 3 | 60 | 3179–6014 | 4904 | 86.7 | 8.5 | 1.7 |
| 4 | 60 | 6105–11032 | 8345 | 86.0 | 12.5 | 73.3 |
| 5 | 60 | 11206–20844 | 14553 | 71.4 | — | 100.0 |
