# step-final_reasonif

### step-final_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 46 | 2.2 | 0.0–4.9 | 82.2 | 87.0 | 6.1 | 10103 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 89.7 | 84.6 | 11.6 | 7086 |
| json_format | 47 | 40 | 0.0 | 0.0–0.0 | 90.0 | 85.0 | 14.9 | 14328 |
| no_comma | 56 | 44 | 0.0 | 0.0–0.0 | 88.4 | 93.2 | 21.4 | 10900 |
| number_words | 53 | 49 | 8.2 | 3.2–13.2 | 81.6 | 83.7 | 9.4 | 9295 |
| reasoning_language | 52 | 44 | 22.7 | 14.6–30.8 | 90.5 | 86.4 | 19.2 | 8841 |

**Macro-average compliance: 5.5 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 15 | 14 | 85.7 | 73.7–97.7 | 4050.5 | 317.2 |
| non-compliant | 247 | 244 | 86.9 | 84.1–89.7 | 4702.0 | 356.5 |
| ungradeable | 38 | 0 | — | — | 14742.3 | 0.0 |

Accuracy gap (non-compliant − compliant): **+1.2 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 369–1404 | 882 | 95.0 | 6.7 | 0.0 |
| 2 | 60 | 1426–3250 | 2121 | 88.3 | 6.7 | 0.0 |
| 3 | 60 | 3261–5610 | 4433 | 86.4 | 8.3 | 0.0 |
| 4 | 60 | 5682–10835 | 7942 | 85.0 | 0.0 | 1.7 |
| 5 | 60 | 10959–20852 | 14231 | 63.2 | 9.1 | 68.3 |
