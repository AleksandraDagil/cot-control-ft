# base_reasonif_metrcap16384

### base_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 36 | 2.8 | 0.0–6.3 | 82.5 | 91.7 | 26.5 | 9514 |
| english_capital | 43 | 26 | 0.0 | 0.0–0.0 | 97.1 | 76.9 | 39.5 | 6219 |
| json_format | 47 | 29 | 0.0 | 0.0–0.0 | 85.4 | 82.8 | 38.3 | 11544 |
| no_comma | 56 | 34 | 0.0 | 0.0–0.0 | 93.6 | 100.0 | 39.3 | 8881 |
| number_words | 53 | 34 | 11.8 | 4.7–18.8 | 83.0 | 85.3 | 35.8 | 9625 |
| reasoning_language | 52 | 34 | 26.5 | 16.8–36.2 | 88.1 | 82.4 | 34.6 | 8642 |

**Macro-average compliance: 6.8 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 14 | 14 | 100.0 | 100.0–100.0 | 2640.9 | 363.0 |
| non-compliant | 179 | 176 | 90.9 | 88.1–93.7 | 2868.7 | 240.2 |
| ungradeable | 107 | 62 | 77.4 | 70.6–84.2 | 12062.4 | 360.8 |

Accuracy gap (non-compliant − compliant): **-9.1 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 434–1487 | 847 | 91.5 | 10.0 | 0.0 |
| 2 | 60 | 1557–3178 | 2371 | 91.7 | 3.3 | 0.0 |
| 3 | 60 | 3216–6174 | 4384 | 87.9 | 6.8 | 1.7 |
| 4 | 60 | 6268–11164 | 8396 | 83.9 | 14.3 | 76.7 |
| 5 | 60 | 11184–19918 | 14216 | 78.9 | — | 100.0 |
