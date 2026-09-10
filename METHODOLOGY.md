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

## Audit of the completed runs (2026-09-10)

Checked after the fact, because several risky things had happened: two sessions writing the
same tree, a calibration killed and restarted twice, and code changed mid-run.

**Clean.** All three rollout stores: 0 unparsable lines, 0 duplicate `(sample_id, mode)` keys,
0 recorded errors, 0 empty reasoning traces. Re-grading the stored ReasonIF rollouts with
current code reproduces the on-disk summary byte-identically, so nothing is stale. ReasonIF word
limits verified applied in both prompt text and grader args on all 53 `number_words` rows.
CoTControl prompts verified to carry their control value and `Requirement:` clause, with no row
lacking keywords or options. `git fsck` clean.

**Two log errors, both false alarms.** vLLM logs a WARNING-level `Traceback` for an optional
Numba import (it rejects NumPy 2.5); the server is unaffected. One client `APIConnectionError`
retried and succeeded, which is why the store records zero errors.

**One real mislabel, no effect on results.** 15 of 900 calibration rollouts had
`truncated=True` with `think_status="ok"`: the model closed `</think>` and *then* hit the cap
mid-answer, so the reasoning is complete and its word count exact. Classifying on `truncated`
alone counted them as right-censored. p20 is unchanged for every source (verified by direct
recomputation) because censoring affects only the rank count, never the ordering, and
identifiability still held with the lower count. The classification is now
`truncated AND status == "unclosed"`.

**Mixed censoring levels, by construction.** gpqa and amc censored observations were recorded at
a 16384 cap and restored rather than regenerated, because only their rank matters for a low
percentile; aime's were regenerated at 32768. Harmless here — p20 sits far below the smallest
censored value in every source, which `identifiable()` checks — but it is a real detail of how
the numbers were produced and belongs in the write-up.

**Known outstanding.** The in-flight baseline imported the pre-fix scoring code, so its
CoTControl accuracy must be regenerated with `--grade-only` after it finishes. Compliance is
unaffected, since it never reads the gold answer.

**Tuning note.** vLLM reports that `--kv-cache-memory=10127396352` (9.43 GiB) would fully use
the GPU against the 8.5 GiB currently allocated, roughly 11 % more KV and so ~11 % more
throughput. Not worth restarting mid-run; worth setting for the P4 checkpoint evals.
