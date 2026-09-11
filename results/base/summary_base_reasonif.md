# base_reasonif

### base_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 45 | 2.2 | 0.0–5.0 | 82.5 | 88.9 | 8.2 | 9514 |
| english_capital | 43 | 37 | 0.0 | 0.0–0.0 | 97.1 | 81.1 | 16.3 | 6219 |
| json_format | 47 | 42 | 0.0 | 0.0–0.0 | 85.4 | 78.6 | 12.8 | 11544 |
| no_comma | 56 | 48 | 0.0 | 0.0–0.0 | 93.6 | 93.8 | 16.1 | 8881 |
| number_words | 53 | 48 | 8.3 | 3.2–13.4 | 83.0 | 81.2 | 11.3 | 9625 |
| reasoning_language | 52 | 42 | 23.8 | 15.4–32.2 | 88.1 | 81.0 | 19.2 | 8642 |

**Macro-average compliance: 5.7 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 15 | 15 | 93.3 | 85.1–100.0 | 3406.3 | 375.9 |
| non-compliant | 247 | 237 | 87.8 | 85.0–90.5 | 4905.1 | 328.1 |
| ungradeable | 38 | 0 | — | — | 15223.9 | 0.0 |

Accuracy gap (non-compliant − compliant): **-5.6 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 434–1487 | 847 | 91.5 | 10.0 | 0.0 |
| 2 | 60 | 1557–3178 | 2371 | 91.7 | 3.3 | 0.0 |
| 3 | 60 | 3216–6174 | 4384 | 87.9 | 6.7 | 0.0 |
| 4 | 60 | 6268–11164 | 8396 | 83.9 | 3.4 | 1.7 |
| 5 | 60 | 11184–19918 | 14216 | 78.9 | 4.3 | 68.3 |
