# step-60_reasonif

### step-60_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 44 | 4.5 | 0.5–8.6 | 83.7 | 88.6 | 12.2 | 10363 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 94.9 | 94.9 | 9.3 | 6109 |
| json_format | 47 | 43 | 0.0 | 0.0–0.0 | 92.9 | 83.7 | 10.6 | 11677 |
| no_comma | 56 | 46 | 0.0 | 0.0–0.0 | 88.9 | 91.3 | 19.6 | 8911 |
| number_words | 53 | 51 | 9.8 | 4.5–15.1 | 79.6 | 78.4 | 7.5 | 9120 |
| reasoning_language | 52 | 43 | 23.3 | 15.0–31.5 | 90.7 | 83.7 | 17.3 | 8726 |

**Macro-average compliance: 6.3 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 17 | 17 | 82.4 | 70.5–94.2 | 3500.5 | 404.7 |
| non-compliant | 249 | 244 | 88.5 | 85.9–91.1 | 4950.2 | 337.9 |
| ungradeable | 34 | 0 | — | — | 15049.3 | 0.0 |

Accuracy gap (non-compliant − compliant): **+6.2 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 213–1418 | 927 | 95.0 | 8.3 | 0.0 |
| 2 | 60 | 1486–3335 | 2331 | 91.7 | 8.3 | 0.0 |
| 3 | 60 | 3336–6014 | 4359 | 86.4 | 6.7 | 0.0 |
| 4 | 60 | 6114–10662 | 8285 | 86.4 | 5.1 | 1.7 |
| 5 | 60 | 10774–23157 | 13861 | 69.6 | 0.0 | 63.3 |
