# step-30_reasonif_metrcap16384

### step-30_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 35 | 2.9 | 0.0–6.5 | 80.0 | 91.4 | 28.6 | 10022 |
| english_capital | 43 | 32 | 0.0 | 0.0–0.0 | 94.9 | 87.5 | 25.6 | 8181 |
| json_format | 47 | 28 | 0.0 | 0.0–0.0 | 94.9 | 89.3 | 40.4 | 11838 |
| no_comma | 56 | 31 | 0.0 | 0.0–0.0 | 87.2 | 96.8 | 44.6 | 12304 |
| number_words | 53 | 36 | 11.1 | 4.4–17.8 | 85.7 | 83.3 | 32.1 | 9850 |
| reasoning_language | 52 | 37 | 24.3 | 15.3–33.4 | 90.9 | 86.5 | 28.8 | 8737 |

**Macro-average compliance: 6.4 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 14 | 14 | 92.9 | 84.0–100.0 | 3311.8 | 326.6 |
| non-compliant | 185 | 183 | 90.2 | 87.3–93.0 | 3096.8 | 249.1 |
| ungradeable | 101 | 66 | 83.3 | 77.5–89.2 | 11525.3 | 362.7 |

Accuracy gap (non-compliant − compliant): **-2.7 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 245–1536 | 995 | 95.0 | 6.7 | 0.0 |
| 2 | 60 | 1538–3343 | 2313 | 90.0 | 3.3 | 0.0 |
| 3 | 60 | 3360–6149 | 4639 | 91.4 | 10.2 | 1.7 |
| 4 | 60 | 6155–10153 | 7936 | 83.1 | 10.0 | 66.7 |
| 5 | 60 | 10288–19738 | 13286 | 76.9 | — | 100.0 |
