# base_cotcontrol

### base_cotcontrol

| mode | n | gradeable | compliance % | 80% CI | accuracy % | meta % | trunc % | med tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| alternating_case | 300 | 281 | 0.0 | 0.0–0.0 | 54.5 | 95.4 | 6.3 | 11156 |
| end_of_sentence | 300 | 295 | 0.0 | 0.0–0.0 | 55.4 | 96.9 | 2.0 | 8002 |
| ignore_question | 300 | 300 | 0.0 | 0.0–0.0 | 52.0 | 94.6 | 2.0 | 5865 |
| lowercase_thinking | 300 | 285 | 0.0 | 0.0–0.0 | 58.3 | 92.6 | 6.0 | 7866 |
| meow_between_words | 300 | 296 | 0.0 | 0.0–0.0 | 56.6 | 99.3 | 2.3 | 8496 |
| multiple_word_suppression | 300 | 284 | 0.0 | 0.0–0.0 | 56.7 | 96.8 | 5.3 | 8714 |
| repeat_sentences | 300 | 296 | 0.0 | 0.0–0.0 | 53.6 | 94.6 | 1.7 | 7880 |
| uppercase_thinking | 300 | 284 | 0.0 | 0.0–0.0 | 56.9 | 87.7 | 6.0 | 8281 |
| word_suppression | 300 | 279 | 0.0 | 0.0–0.0 | 57.0 | 96.4 | 7.0 | 8498 |

**Macro-average compliance: 0.0 %** (unweighted mean over modes)


### Accuracy by compliance status

| compliance | n | answered | accuracy % | 80% CI | mean CoT words | mean answer words |
|---|---:|---:|---:|---:|---:|---:|
| compliant | 0 | 0 | — | — | None | None |
| non-compliant | 2600 | 2579 | 55.6 | 54.4–56.9 | 4951.4 | 192.1 |
| ungradeable | 100 | 0 | — | — | 15439.2 | 0.0 |

### Accuracy by CoT length (quintiles)

| CoT-length bin | n | words (min–max) | median | accuracy % | compliance % | trunc % |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 540 | 373–3296 | 2643 | 69.1 | 0.0 | 0.0 |
| 2 | 540 | 3299–4138 | 3748 | 61.8 | 0.0 | 0.2 |
| 3 | 540 | 4139–4983 | 4566 | 53.4 | 0.0 | 0.2 |
| 4 | 540 | 4984–6500 | 5568 | 49.7 | 0.0 | 0.0 |
| 5 | 540 | 6506–19970 | 9156 | 41.3 | 0.0 | 21.1 |
