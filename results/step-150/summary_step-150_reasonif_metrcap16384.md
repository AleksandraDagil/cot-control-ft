# step-150_reasonif_metrcap16384

### step-150_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 34 | 8.8 | 2.6–15.1 | 82.6 | 85.3 | 30.6 | 10326 |
| english_capital | 43 | 32 | 0.0 | 0.0–0.0 | 87.2 | 100.0 | 25.6 | 8685 |
| json_format | 47 | 29 | 0.0 | 0.0–0.0 | 88.1 | 86.2 | 38.3 | 12234 |
| no_comma | 56 | 31 | 0.0 | 0.0–0.0 | 88.9 | 100.0 | 44.6 | 11529 |
| number_words | 53 | 34 | 14.7 | 6.9–22.5 | 87.8 | 85.3 | 35.8 | 9309 |
| reasoning_language | 52 | 34 | 26.5 | 16.8–36.2 | 86.4 | 88.2 | 34.6 | 7937 |

**Macro-average compliance: 8.3 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 17 | 17 | 82.4 | 70.5–94.2 | 3139.5 | 336.5 |
| non-compliant | 177 | 177 | 87.6 | 84.4–90.7 | 2944.4 | 249.5 |
| ungradeable | 106 | 71 | 85.9 | 80.6–91.2 | 11437.6 | 421.3 |

Accuracy gap (non-compliant − compliant): **+5.2 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 297–1582 | 874 | 95.0 | 8.3 | 0.0 |
| 2 | 60 | 1616–3185 | 2223 | 81.7 | 5.0 | 0.0 |
| 3 | 60 | 3191–6436 | 4434 | 85.0 | 13.6 | 1.7 |
| 4 | 60 | 6575–10855 | 8286 | 84.5 | 6.7 | 75.0 |
| 5 | 60 | 10909–21393 | 12976 | 88.9 | — | 100.0 |
