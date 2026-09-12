# step-60_reasonif_metrcap16384

### step-60_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 35 | 31.4 | 21.4–41.5 | 82.2 | 45.7 | 28.6 | 8721 |
| english_capital | 43 | 29 | 20.7 | 11.0–30.3 | 92.1 | 44.8 | 32.6 | 8057 |
| json_format | 47 | 30 | 3.3 | 0.0–7.5 | 92.9 | 33.3 | 36.2 | 10561 |
| no_comma | 56 | 33 | 39.4 | 28.5–50.3 | 93.5 | 48.5 | 41.1 | 11461 |
| number_words | 53 | 36 | 61.1 | 50.7–71.5 | 80.0 | 30.6 | 32.1 | 8166 |
| reasoning_language | 52 | 31 | 29.0 | 18.6–39.5 | 93.0 | 45.2 | 40.4 | 9167 |

**Macro-average compliance: 30.8 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 62 | 62 | 95.2 | 91.7–98.7 | 961.2 | 222.4 |
| non-compliant | 132 | 132 | 92.4 | 89.5–95.4 | 2644.8 | 335.1 |
| ungradeable | 106 | 70 | 75.7 | 69.1–82.3 | 11332.9 | 405.5 |

Accuracy gap (non-compliant − compliant): **-2.7 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 60–400 | 212 | 95.0 | 66.7 | 0.0 |
| 2 | 60 | 407–2146 | 1048 | 95.0 | 23.3 | 0.0 |
| 3 | 60 | 2161–5921 | 3821 | 90.0 | 8.3 | 0.0 |
| 4 | 60 | 6054–10807 | 7771 | 76.3 | 21.4 | 76.7 |
| 5 | 60 | 10855–22070 | 13332 | 84.0 | — | 100.0 |
