# step-60_cotcontrol

### step-60_cotcontrol

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| alternating_case | 300 | 285 | 0.0 | 0.0–0.0 | 56.6 | 96.5 | 6.0 | 11047 |
| end_of_sentence | 300 | 295 | 0.0 | 0.0–0.0 | 56.6 | 95.6 | 1.7 | 8062 |
| ignore_question | 300 | 300 | 0.0 | 0.0–0.0 | 53.0 | 94.0 | 5.7 | 5829 |
| lowercase_thinking | 300 | 288 | 0.0 | 0.0–0.0 | 58.7 | 92.4 | 4.0 | 7900 |
| meow_between_words | 300 | 294 | 0.0 | 0.0–0.0 | 55.2 | 99.0 | 3.0 | 9102 |
| multiple_word_suppression | 300 | 287 | 0.0 | 0.0–0.0 | 57.0 | 97.6 | 4.7 | 8658 |
| repeat_sentences | 300 | 294 | 0.0 | 0.0–0.0 | 58.2 | 95.2 | 2.0 | 7898 |
| uppercase_thinking | 300 | 279 | 0.0 | 0.0–0.0 | 58.1 | 86.0 | 7.0 | 8230 |
| word_suppression | 300 | 279 | 0.0 | 0.0–0.0 | 55.2 | 96.4 | 7.0 | 8765 |

**Macro-average compliance: 0.0 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 0 | 0 | — | — | None | None |
| non-compliant | 2601 | 2571 | 56.5 | 55.3–57.8 | 5029.1 | 185.7 |
| ungradeable | 99 | 0 | — | — | 15393.4 | 0.0 |

### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 540 | 233–3272 | 2547 | 69.2 | 0.0 | 0.0 |
| 2 | 540 | 3274–4156 | 3743 | 61.2 | 0.0 | 0.0 |
| 3 | 540 | 4157–5047 | 4588 | 57.1 | 0.0 | 0.0 |
| 4 | 540 | 5051–6639 | 5736 | 49.8 | 0.0 | 0.2 |
| 5 | 540 | 6640–27354 | 9314 | 42.0 | 0.0 | 22.6 |
