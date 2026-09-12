# step-180_reasonif

### step-180_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 44 | 2.3 | 0.0–5.2 | 86.4 | 84.1 | 10.2 | 10495 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 94.9 | 76.9 | 9.3 | 7730 |
| json_format | 47 | 41 | 0.0 | 0.0–0.0 | 87.2 | 82.9 | 14.9 | 11585 |
| no_comma | 56 | 48 | 2.1 | 0.0–4.7 | 89.6 | 91.7 | 14.3 | 14026 |
| number_words | 53 | 48 | 10.4 | 4.8–16.1 | 89.6 | 85.4 | 9.4 | 9247 |
| reasoning_language | 52 | 43 | 23.3 | 15.0–31.5 | 90.7 | 93.0 | 17.3 | 7867 |

**Macro-average compliance: 6.3 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 17 | 17 | 94.1 | 86.8–100.0 | 3217.9 | 387.1 |
| non-compliant | 246 | 244 | 89.3 | 86.8–91.9 | 4968.3 | 323.2 |
| ungradeable | 37 | 0 | — | — | 15040.5 | 0.0 |

Accuracy gap (non-compliant − compliant): **-4.8 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 132–1304 | 808 | 98.3 | 8.3 | 0.0 |
| 2 | 60 | 1308–3121 | 2269 | 95.0 | 8.3 | 0.0 |
| 3 | 60 | 3186–6609 | 4440 | 89.8 | 8.3 | 0.0 |
| 4 | 60 | 6690–11175 | 8860 | 76.7 | 3.3 | 0.0 |
| 5 | 60 | 11254–21458 | 14213 | 86.4 | 0.0 | 63.3 |
