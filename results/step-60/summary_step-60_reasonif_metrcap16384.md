# step-60_reasonif_metrcap16384

### step-60_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 35 | 5.7 | 0.7–10.7 | 83.7 | 85.7 | 28.6 | 10363 |
| english_capital | 43 | 30 | 0.0 | 0.0–0.0 | 94.9 | 96.7 | 30.2 | 6109 |
| json_format | 47 | 31 | 0.0 | 0.0–0.0 | 92.9 | 90.3 | 34.0 | 11677 |
| no_comma | 56 | 35 | 0.0 | 0.0–0.0 | 88.9 | 94.3 | 37.5 | 8911 |
| number_words | 53 | 35 | 11.4 | 4.5–18.3 | 79.6 | 88.6 | 34.0 | 9120 |
| reasoning_language | 52 | 36 | 22.2 | 13.3–31.1 | 90.7 | 83.3 | 30.8 | 8726 |

**Macro-average compliance: 6.6 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 14 | 14 | 85.7 | 73.7–97.7 | 2412.2 | 372.7 |
| non-compliant | 188 | 187 | 92.0 | 89.4–94.5 | 3098.3 | 263.2 |
| ungradeable | 98 | 60 | 76.7 | 69.7–83.7 | 12117.8 | 370.6 |

Accuracy gap (non-compliant − compliant): **+6.3 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 213–1418 | 927 | 95.0 | 8.3 | 0.0 |
| 2 | 60 | 1486–3335 | 2331 | 91.7 | 8.3 | 0.0 |
| 3 | 60 | 3336–6014 | 4359 | 86.4 | 6.7 | 0.0 |
| 4 | 60 | 6114–10662 | 8285 | 86.4 | 0.0 | 63.3 |
| 5 | 60 | 10774–23157 | 13861 | 69.6 | — | 100.0 |
