# Accidental base-model replicates

Eight ReasonIF runs and one 2,700-rollout CoTControl run that were **intended** to evaluate
fine-tuned checkpoints but in fact evaluated the **base model**, because vLLM silently ignored
the LoRA adapters (see `METHODOLOGY.md`). Directory names retain the checkpoint labels the runs
were given (`step-30_…`, `step-60_…`); **none of them are checkpoint results.**

Recovered from git `da47243` after the mislabelled `results/step-*/` directories were deleted.
Only the summary JSON/MD survived — the raw rollout JSONLs were gitignored and are gone, so
these cannot be re-graded and no per-rollout or length-conditional analysis is possible on them.

## What they are good for

An unplanned control: eight independent measurements of the same model on the *same* 300
prompts at temperature 1.0. That is a direct empirical estimate of run-to-run noise, which we
had no budget to collect deliberately.

## ReasonIF, 8 replicates

| run | micro % | macro % | gradeable | trunc % | accuracy % |
|---|---:|---:|---:|---:|---:|
| step-30 | 5.6 | 5.4 | 267 | 11.3 | 88.6 |
| step-60 | 6.4 | 6.3 | 266 | 13.0 | 88.1 |
| step-90 | 7.1 | 6.9 | 268 | 12.3 | 88.1 |
| step-120 | 8.4 | 8.1 | 263 | 14.0 | 87.5 |
| step-150 | 7.0 | 6.7 | 271 | 11.3 | 86.8 |
| step-180 | 6.5 | 6.3 | 263 | 12.7 | 89.7 |
| step-210 | 6.4 | 6.4 | 267 | 12.3 | 87.4 |
| step-final | 5.7 | 5.5 | 262 | 14.0 | 86.8 |
| **original baseline** | **5.7** | **5.7** | 262 | 14.0 | 88.1 |

    micro compliance   mean 6.63   sd 0.82   range 5.62 - 8.37  (2.75 pp)
    macro compliance   mean 6.45   sd 0.78   range 5.42 - 8.05  (2.63 pp)
    accuracy           mean 87.88  sd 0.90   range 86.79 - 89.66

## Per instruction

| instruction | mean % | sd | min | max | range | original |
|---|---:|---:|---:|---:|---:|---:|
| end_checker | 5.6 | 3.23 | 2.1 | 11.6 | **9.5** | 2.2 |
| english_capital | 0.0 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 |
| json_format | 0.0 | 0.00 | 0.0 | 0.0 | 0.0 | 0.0 |
| no_comma | 0.3 | 0.69 | 0.0 | 2.1 | 2.1 | 0.0 |
| number_words | 9.9 | 1.58 | 8.0 | 12.2 | 4.2 | 8.3 |
| reasoning_language | 23.0 | 1.17 | 21.4 | 25.0 | 3.6 | 23.8 |

## CoTControl, 1 replicate (2,700 rollouts)

    macro 0.00 %   micro 0.00 %   gradeable 2601   accuracy 56.5 %
    all 9 modes at exactly 0.0 %
    original baseline: macro 0.00 %, accuracy 55.6 %

## What this tells us

**The overall rate is more stable than a binomial CI implies.** Observed run-to-run sd is
0.82 pp against a binomial prediction of 1.52 pp at p=0.066, n=266. That is the paired design
working: reusing the same 300 questions removes question-selection variance, leaving only
sampling variance. It is evidence the pairing is worth what it costs.

**Per-instruction rates are not stable at all.** `end_checker` ranged 2.1 % to 11.6 % across
runs of an identical model — a 9.5 pp spread, consistent with binomial noise at ~45 gradeable
rollouts per instruction. **A per-instruction difference below roughly 10 pp is not
interpretable from a single run.** This matters directly for reading the real P4 results.

**Our published baseline may be ~1 pp low by luck.** The original run reported 5.7 % micro; the
replicate mean is 6.63 % and the original sits at the bottom of the observed range. Any uplift
measured against it is correspondingly flattered. Worth stating in the write-up.

**The CoTControl floor is real.** A second independent 2,700-rollout measurement also lands on
exactly 0.0 % across all nine modes. Zero is the model's actual behaviour, not one unlucky draw.

**Truncation is stable** (11.3-14.0 %), so the cap is not a fluctuating source of selection
between runs.
