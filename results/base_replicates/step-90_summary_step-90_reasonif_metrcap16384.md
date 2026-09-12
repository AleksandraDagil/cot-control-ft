# step-90_reasonif_metrcap16384

### step-90_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 36 | 11.1 | 4.4–17.8 | 86.4 | 83.3 | 26.5 | 10456 |
| english_capital | 43 | 31 | 0.0 | 0.0–0.0 | 89.7 | 90.3 | 27.9 | 8584 |
| json_format | 47 | 29 | 0.0 | 0.0–0.0 | 82.9 | 89.7 | 38.3 | 11573 |
| no_comma | 56 | 31 | 0.0 | 0.0–0.0 | 91.1 | 93.5 | 44.6 | 15392 |
| number_words | 53 | 35 | 11.4 | 4.5–18.3 | 87.8 | 85.7 | 34.0 | 9425 |
| reasoning_language | 52 | 34 | 26.5 | 16.8–36.2 | 90.7 | 91.2 | 34.6 | 9072 |

**Macro-average compliance: 8.2 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 17 | 17 | 94.1 | 86.8–100.0 | 2958.9 | 367.8 |
| non-compliant | 179 | 178 | 90.4 | 87.6–93.3 | 3101.6 | 248.6 |
| ungradeable | 104 | 66 | 80.3 | 74.0–86.6 | 11666.9 | 529.8 |

Accuracy gap (non-compliant − compliant): **-3.7 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 195–1749 | 963 | 93.3 | 6.7 | 0.0 |
| 2 | 60 | 1767–3565 | 2381 | 98.3 | 11.9 | 1.7 |
| 3 | 60 | 3583–6133 | 4706 | 86.7 | 8.5 | 1.7 |
| 4 | 60 | 6162–10594 | 8027 | 79.3 | 5.6 | 70.0 |
| 5 | 60 | 10718–23140 | 13764 | 75.0 | — | 100.0 |
