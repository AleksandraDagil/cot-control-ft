# step-final_reasonif_metrcap16384

### step-final_reasonif_metrcap16384

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| end_checker | 49 | 39 | 2.6 | 0.0–5.8 | 82.2 | 87.2 | 20.4 | 10103 |
| english_capital | 43 | 30 | 0.0 | 0.0–0.0 | 89.7 | 86.7 | 30.2 | 7086 |
| json_format | 47 | 27 | 0.0 | 0.0–0.0 | 90.0 | 88.9 | 42.6 | 14328 |
| no_comma | 56 | 34 | 0.0 | 0.0–0.0 | 88.4 | 100.0 | 39.3 | 10900 |
| number_words | 53 | 35 | 11.4 | 4.5–18.3 | 81.6 | 94.3 | 34.0 | 9295 |
| reasoning_language | 52 | 36 | 22.2 | 13.3–31.1 | 90.5 | 86.1 | 30.8 | 8841 |

**Macro-average compliance: 6.0 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 13 | 13 | 84.6 | 71.8–97.4 | 2419.8 | 313.8 |
| non-compliant | 188 | 187 | 90.4 | 87.6–93.1 | 2978.4 | 248.4 |
| ungradeable | 99 | 58 | 75.9 | 68.7–83.1 | 12029.9 | 424.5 |

Accuracy gap (non-compliant − compliant): **+5.8 pp** (positive = complying cost accuracy)


### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 60 | 369–1404 | 882 | 95.0 | 6.7 | 0.0 |
| 2 | 60 | 1426–3250 | 2121 | 88.3 | 6.7 | 0.0 |
| 3 | 60 | 3261–5610 | 4433 | 86.4 | 8.3 | 0.0 |
| 4 | 60 | 5682–10835 | 7942 | 85.0 | 0.0 | 65.0 |
| 5 | 60 | 10959–20852 | 14231 | 63.2 | — | 100.0 |
