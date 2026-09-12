# step-90_reasonif

### step-90_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 46 | 8.7 | 3.4–14.0 | 86.4 | 82.6 | 10.2 | 10456 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 89.7 | 92.3 | 9.3 | 8584 |
| json_format | 47 | 43 | 0.0 | 0.0–0.0 | 82.9 | 86.0 | 8.5 | 11573 |
| no_comma | 56 | 46 | 0.0 | 0.0–0.0 | 91.1 | 93.5 | 19.6 | 15392 |
| number_words | 53 | 50 | 8.0 | 3.1–12.9 | 87.8 | 80.0 | 7.5 | 9425 |
| reasoning_language | 52 | 44 | 25.0 | 16.6–33.4 | 90.7 | 86.4 | 17.3 | 9072 |

**Macro-average compliance: 6.9 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 19 | 19 | 94.7 | 88.2–100.0 | 3701.0 | 392.4 |
| non-compliant | 249 | 242 | 87.6 | 84.9–90.3 | 5104.3 | 395.2 |
| ungradeable | 32 | 0 | — | — | 14923.5 | 0.0 |

Accuracy gap (non-compliant − compliant): **-7.1 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 195–1749 | 963 | 93.3 | 6.7 | 0.0 |
| 2 | 60 | 1767–3565 | 2381 | 98.3 | 11.7 | 1.7 |
| 3 | 60 | 3583–6133 | 4706 | 86.7 | 8.3 | 0.0 |
| 4 | 60 | 6162–10594 | 8027 | 79.3 | 3.4 | 1.7 |
| 5 | 60 | 10718–23140 | 13764 | 75.0 | 3.4 | 58.3 |
