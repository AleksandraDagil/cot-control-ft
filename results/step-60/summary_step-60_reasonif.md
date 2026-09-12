# step-60_reasonif

### step-60_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 47 | 23.4 | 15.5–31.3 | 82.2 | 51.1 | 8.2 | 8721 |
| english_capital | 43 | 38 | 15.8 | 8.2–23.4 | 92.1 | 57.9 | 11.6 | 8057 |
| json_format | 47 | 42 | 2.4 | 0.0–5.4 | 92.9 | 47.6 | 10.6 | 10561 |
| no_comma | 56 | 47 | 27.7 | 19.3–36.0 | 93.5 | 51.1 | 17.9 | 11461 |
| number_words | 53 | 52 | 42.3 | 33.5–51.1 | 80.0 | 40.4 | 5.7 | 8166 |
| reasoning_language | 52 | 44 | 25.0 | 16.6–33.4 | 93.0 | 52.3 | 17.3 | 9167 |

**Macro-average compliance: 22.8 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 64 | 64 | 95.3 | 91.9–98.7 | 1145.5 | 232.8 |
| non-compliant | 206 | 200 | 86.5 | 83.4–89.6 | 5265.3 | 418.0 |
| ungradeable | 30 | 0 | — | — | 15068.1 | 0.0 |

Accuracy gap (non-compliant − compliant): **-8.8 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 60–400 | 212 | 95.0 | 66.7 | 0.0 |
| 2 | 60 | 407–2146 | 1048 | 95.0 | 23.3 | 0.0 |
| 3 | 60 | 2161–5921 | 3821 | 90.0 | 8.3 | 0.0 |
| 4 | 60 | 6054–10807 | 7771 | 76.3 | 8.3 | 1.7 |
| 5 | 60 | 10855–22070 | 13332 | 84.0 | 0.0 | 58.3 |
