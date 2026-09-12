# step-180_reasonif_metrcap16384

### step-180_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 30 | 3.3 | 0.0–7.5 | 86.4 | 90.0 | 38.8 | 10495 |
| english_capital | 43 | 32 | 0.0 | 0.0–0.0 | 94.9 | 71.9 | 25.6 | 7730 |
| json_format | 47 | 29 | 0.0 | 0.0–0.0 | 87.2 | 86.2 | 38.3 | 11585 |
| no_comma | 56 | 31 | 3.2 | 0.0–7.3 | 89.6 | 100.0 | 44.6 | 14026 |
| number_words | 53 | 32 | 15.6 | 7.4–23.9 | 89.6 | 93.8 | 39.6 | 9247 |
| reasoning_language | 52 | 34 | 26.5 | 16.8–36.2 | 90.7 | 91.2 | 34.6 | 7867 |

**Macro-average compliance: 8.1 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 16 | 16 | 93.8 | 86.0–100.0 | 2806.4 | 373.6 |
| non-compliant | 172 | 171 | 94.2 | 91.9–96.5 | 2799.6 | 234.5 |
| ungradeable | 112 | 74 | 78.4 | 72.2–84.5 | 11669.5 | 355.1 |

Accuracy gap (non-compliant − compliant): **+0.4 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 132–1304 | 808 | 98.3 | 8.3 | 0.0 |
| 2 | 60 | 1308–3121 | 2269 | 95.0 | 8.3 | 0.0 |
| 3 | 60 | 3186–6609 | 4440 | 89.8 | 8.8 | 5.0 |
| 4 | 60 | 6690–11175 | 8860 | 76.7 | 9.1 | 81.7 |
| 5 | 60 | 11254–21458 | 14213 | 86.4 | — | 100.0 |
