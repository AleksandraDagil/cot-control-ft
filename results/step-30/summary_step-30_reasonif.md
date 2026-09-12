# step-30_reasonif

### step-30_reasonif

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 47 | 2.1 | 0.0–4.8 | 80.0 | 89.4 | 4.1 | 10022 |
| english_capital | 43 | 39 | 0.0 | 0.0–0.0 | 94.9 | 89.7 | 9.3 | 8181 |
| json_format | 47 | 40 | 0.0 | 0.0–0.0 | 94.9 | 85.0 | 14.9 | 11838 |
| no_comma | 56 | 47 | 0.0 | 0.0–0.0 | 87.2 | 91.5 | 16.1 | 12304 |
| number_words | 53 | 49 | 8.2 | 3.2–13.2 | 85.7 | 85.7 | 7.5 | 9850 |
| reasoning_language | 52 | 45 | 22.2 | 14.3–30.2 | 90.9 | 86.7 | 15.4 | 8737 |

**Macro-average compliance: 5.4 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 15 | 15 | 86.7 | 75.4–97.9 | 3737.9 | 342.1 |
| non-compliant | 252 | 248 | 88.7 | 86.1–91.3 | 4896.1 | 326.1 |
| ungradeable | 33 | 0 | — | — | 14952.8 | 0.0 |

Accuracy gap (non-compliant − compliant): **+2.0 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 245–1536 | 995 | 95.0 | 6.7 | 0.0 |
| 2 | 60 | 1538–3343 | 2313 | 90.0 | 3.3 | 0.0 |
| 3 | 60 | 3360–6149 | 4639 | 91.4 | 10.0 | 0.0 |
| 4 | 60 | 6155–10153 | 7936 | 83.1 | 5.0 | 0.0 |
| 5 | 60 | 10288–19738 | 13286 | 76.9 | 0.0 | 56.7 |
