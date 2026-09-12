# step-120_reasonif

### step-120_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 43 | 11.6 | 5.4–17.9 | 82.9 | 95.3 | 14.3 | 10341 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 89.7 | 87.2 | 9.3 | 8625 |
| json_format | 47 | 41 | 0.0 | 0.0–0.0 | 90.2 | 87.8 | 12.8 | 10795 |
| no_comma | 56 | 46 | 0.0 | 0.0–0.0 | 91.3 | 93.5 | 19.6 | 11007 |
| number_words | 53 | 49 | 12.2 | 6.2–18.2 | 84.8 | 81.6 | 11.3 | 8264 |
| reasoning_language | 52 | 45 | 24.4 | 16.2–32.7 | 86.4 | 86.7 | 15.4 | 10024 |

**Macro-average compliance: 8.1 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 22 | 21 | 95.2 | 89.3–100.0 | 4019.6 | 427.6 |
| non-compliant | 241 | 236 | 86.9 | 84.0–89.7 | 4892.5 | 324.1 |
| ungradeable | 37 | 0 | — | — | 15317.9 | 0.0 |

Accuracy gap (non-compliant − compliant): **-8.4 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 281–1345 | 860 | 96.6 | 8.3 | 0.0 |
| 2 | 60 | 1346–3161 | 2197 | 86.7 | 10.0 | 0.0 |
| 3 | 60 | 3179–6014 | 4904 | 86.7 | 8.3 | 0.0 |
| 4 | 60 | 6105–11032 | 8345 | 86.0 | 8.6 | 3.3 |
| 5 | 60 | 11206–20844 | 14553 | 71.4 | 4.0 | 66.7 |
