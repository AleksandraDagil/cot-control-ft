# step-150_reasonif

### step-150_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 46 | 6.5 | 1.9–11.2 | 82.6 | 87.0 | 6.1 | 10326 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 87.2 | 100.0 | 9.3 | 8685 |
| json_format | 47 | 43 | 0.0 | 0.0–0.0 | 88.1 | 81.4 | 10.6 | 12234 |
| no_comma | 56 | 47 | 0.0 | 0.0–0.0 | 88.9 | 95.7 | 17.9 | 11529 |
| number_words | 53 | 50 | 12.0 | 6.1–17.9 | 87.8 | 76.0 | 7.5 | 9309 |
| reasoning_language | 52 | 46 | 21.7 | 13.9–29.5 | 86.4 | 87.0 | 15.4 | 7937 |

**Macro-average compliance: 6.7 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 19 | 19 | 84.2 | 73.5–94.9 | 3863.7 | 369.2 |
| non-compliant | 252 | 246 | 87.0 | 84.2–89.7 | 5094.1 | 347.3 |
| ungradeable | 29 | 0 | — | — | 14820.4 | 0.0 |

Accuracy gap (non-compliant − compliant): **+2.8 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 297–1582 | 874 | 95.0 | 8.3 | 0.0 |
| 2 | 60 | 1616–3185 | 2223 | 81.7 | 5.0 | 0.0 |
| 3 | 60 | 3191–6436 | 4434 | 85.0 | 13.3 | 0.0 |
| 4 | 60 | 6575–10855 | 8286 | 84.5 | 3.4 | 1.7 |
| 5 | 60 | 10909–21393 | 12976 | 88.9 | 3.1 | 55.0 |
