# Where we match METR, and where we deviate

Verified against the pinned clones in `ref/` (SHAs in `data/upstream/SOURCES.md`), not from
memory. Each claim below cites the file it came from.

## `number_words` calibration

**The 20th percentile is ReasonIF's rule, not a choice of ours.**

- `reasonIF/src/instructions/instruction_checker.py:90` — `# default value is set to GPT-OSS-120B's 20-th percentile.`
- `cot_controllability/scripts/runs/calibrate_word_count.py:61` — `PERCENTILE = 20  # 20th percentile, matching ReasonIF paper`

The `number_words` instruction reads *"respond with less than N words"*, and N is set per model
per source to the 20th percentile of that model's own unconstrained reasoning length. At p20 the
model's natural output already fits about one time in five, so the constraint is a real squeeze
but not impossible. At the median it would be free; at p5, unachievable.

**Procedure — we match METR step for step** (`calibrate_word_count.py`): all 300 ReasonIF
questions with the constraint stripped, `n_runs` default 3 (our `repeats: 3`), word count via
`RegexpTokenizer(r"\w+")` (our `re.findall(r"\w+")` is the same tokenizer), then the 20th
percentile per source.

**Truncation — our first attempt diverged from METR; the fix moved us back onto their method.**

METR's aggregation (`calibrate_word_count.py:176-194`) skips errors, skips empty reasoning, and
otherwise counts the words. There is **no truncation check at all**: a rollout cut off at the
token cap is included at its truncated length. That is equivalent to treating it as
right-censored for the purpose of a *low* percentile, because a truncated rollout is long and
occupies a top rank either way — p20 never depends on the exact values up there.

Our original `drop_truncated: true` was our own invention and was wrong. It discards the longest
rollouts, so the p-th percentile of the survivors is roughly the (p x retained_fraction)-th
percentile of the true distribution. Measured on Qwen3.5-9B:

| source | drop-truncated | censored-aware (= METR) | error |
|---|---:|---:|---:|
| aime | 2702 | **7451** | 2.8x too small |
| amc | 2867 | 4249 | 1.5x |
| gpqa | 2904 | 3478 | 1.2x |

We add one thing METR does not have: `identifiable()` checks that p20 actually falls below the
smallest censored observation. Where censoring is heavy enough that p20 lands *inside* the
censored region, METR's code would silently emit a too-low number; ours flags it as a lower
bound. This is not hypothetical — at a 16384 cap, 85 % of aime rollouts were censored and its
p20 genuinely sat above the cap.

## Token caps

| | METR | ours | note |
|---|---:|---:|---|
| calibration `max_tokens` | 28000 | 32768 | `calibrate_word_count.py:106`; ours ~17 % higher |
| eval `max_tokens` | 16384 | 32768 | `scripts/runs/run_eval.py:55` CLI default; ours 2x |

METR also used a far larger cap for calibration than for evaluation (28000 vs 16384) — the same
asymmetry we arrived at independently, for the same reason: an unconstrained length distribution
cannot be measured through a tight cap.

**The eval cap is our one real deviation.** Justified by measurement, not preference: at 16384
this model truncates 33 % of ReasonIF rollouts and 15 % of CoTControl rollouts, and the
truncation is not random — it removes the long-reasoning questions, which are the ones least
likely to comply. Measured directly on our own ReasonIF baseline:

| cap | gradeable | truncation | compliance |
|---|---:|---:|---:|
| 32768 (ours) | 262/300 | 14.0 % | **5.7 %** |
| 16384 (METR) | 193/300 | 35.7 % | **7.3 %** |

The tighter cap *raises* apparent compliance by 1.6 pp while discarding 69 more rollouts. So the
deviation is not a free choice of power over comparability — we report both, via
`eval.apply_token_cap`, which re-projects stored rollouts to any cap at zero GPU cost. Worth
noting in the write-up that METR's published numbers may carry the same inflation if their
models truncated at all.

## Other deviations already recorded in PLAN.md

- MMLU-Pro prompts include answer choices (upstream CoTControl behaviour); METR's loader read
  only `answer_options` and so dropped them.
- Word suppression uses bare keywords, no synonyms (METR's variant).
- Meta-discussion measured with METR's regex heuristic; the CoTControl paper uses an LLM judge.
- Editor/judge LLM reached through OpenRouter rather than the OpenAI API directly.
