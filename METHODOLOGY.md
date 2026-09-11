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

## Problems found, and what each one did

Every issue hit across P0-P2, in rough order of how much damage it would have done if it had
gone unnoticed. "Silent" means it would have produced plausible-looking wrong numbers rather
than an error.

### Silent, results-changing

**1. vLLM 0.29 renamed the reasoning field.** The qwen3 parser puts the think block on
`message.reasoning`; we read only `message.reasoning_content`. Every rollout came back
`think_status="missing"` with the reasoning text landing in `content`, which would have made
*every compliance rate zero* and looked like a real finding about the model. Caught by the P0
smoke test on the first real request. Fixed by `inference.reasoning_field()`, which reads
either name; regression-tested at the wire level against a stub server.

**2. CoTControl gold answers are text, not letters, in 2 of 3 datasets.** `hle` stores a bare
letter, but `gpqa` and `mmlu_pro_mini` store the answer *text*. `score_answer` compared the
extracted letter against `correct[:1]`, so a gold of "The compounds allow ..." became "T".
This hit 184 of our 300 drawn questions and put accuracy at 7.9 percent, below chance for
multiple choice. Caught by noticing that number was impossible, not by a test. Fixed with
`datasets.answer_letter()`, which resolves gold to an option letter at load time (all 1214
upstream rows resolve) and returns None -- unscorable -- when it cannot, rather than scoring
the row wrong. Effect on stored rollouts: accuracy 15.2 -> 58.9 percent (gpqa 78.7, mmlu_pro
84.8, hle 15.4). Compliance was never affected, as it does not read the gold answer.

**3. Dropping truncated rollouts biased the word-limit calibration.** `drop_truncated: true`
discarded the longest rollouts, so the 20th percentile of the survivors was roughly the
(20 x retained_fraction)-th percentile of the truth. aime came out at 2702 words against 7451
actual, a 2.8x error that would have made that instruction near-impossible and driven its
baseline to a spurious 0 percent. This was our own invention: METR applies no truncation
check at all, so the fix moved us back onto their method, plus an `identifiable()` guard they
lack. See the calibration section above.

**4. `.gitignore` was swallowing every deliverable.** The entry `results/` makes git skip the
directory outright, so the `!results/**/summary*.json` negations below it never fired. Every
summary and report the project had produced was untracked -- it would have looked fine until
the repo was cloned elsewhere and found empty. Now `results/**` with directory re-inclusion.
`calibration_stats.json` matched no negation either and needed its own.

**5. A 16384 token cap silently selected which questions counted.** Not a bug, but the same
class of problem: truncated rollouts are ungradeable and leave the compliance denominator, and
truncation is not random -- it removes the long-reasoning questions, which are the ones least
likely to comply. Measured on our own ReasonIF baseline: the tighter cap reads 7.3 percent
against 5.7, while discarding 69 more rollouts. Handled by raising the cap and reporting both
via `apply_token_cap`.

### Caught before they could affect anything

**6. `meta_rate` divided by the wrong denominator.** The numerator counted rollouts with usable
reasoning; the denominator was the compliance-gradeable count. Those sets differ in both
directions: an `ignore_question` rollout with no reasoning is compliance-False but not
meta-scorable, and one whose judge call failed is the reverse. Now tracks `n_meta_scored`.

**7. Errored rollouts skewed the token median.** They report 0 completion tokens and were being
included. Now excluded.

**8. Two duplicate METR reference modules with incompatible units.** Both sessions working this
repo wrote one; one took fractions and scaled internally, the other took percentages, and both
were live-imported. Consolidated into `cotctl.analysis.metr` with the unit documented.

**9. A tautological check in the smoke test.** `"," not in reasoning or True` can never fail.
Replaced with a real `grade_reasonif` call.

**10. Empty answers would have poisoned the SFT data.** 4 stage-1 rollouts had a blank answer;
training on `<think>...</think>` followed by nothing teaches the model to emit no answer at
all. Guarded in `build_sft.py`.

**11. Censoring mislabel in the calibration.** 15 of 900 rollouts had `truncated=True` with
`think_status="ok"` -- the model closed the think block and *then* hit the cap mid-answer, so
the reasoning is complete and its word count exact rather than a lower bound. Now classified as
`truncated AND unclosed`. p20 is unchanged for every source, verified by recomputation.

**12. PLAN's SFT pool count was wrong.** PLAN assumed "1000 rows, drop ~5, -> ~953". METR's
filter removes 4, and their `plan_assignments` then deduplicates, removing 59 more. The
effective pool is 937. The "drop ~5" was right; the total was not.

### Environment and tooling

**13. The README install recipe does not resolve.** `--torch-backend=cu128` cannot satisfy the
vLLM nightly's `torch==2.13.0`. PyPI's torch 2.13.0 is a CUDA 13 build, fine on this driver.
README now records what works, with transformers main installed last.

**14. FlashInfer refused sm_120 with a misleading error.** `"FlashInfer requires GPUs with sm75
or higher"` on a 5090. The arch check reports on whichever nvcc `CUDA_HOME` resolves, and
`/usr/local/cuda` here is a CUDA 12.8 toolkit (nvcc present, just off PATH) while sm_120 needs
>= 12.9. Pointing at the venv's cu13 tree fixed detection, after which FlashInfer 0.6.18's
bundled CCCL headers rejected nvcc 13.4-rc. Only the sampler wanted FlashInfer -- attention is
on FLASH_ATTN -- so `serve_vllm.sh` sets `VLLM_USE_FLASHINFER_SAMPLER=0`.

**15. `--disable-log-requests` was removed in vLLM 0.29.** Now `--no-enable-log-requests`.

**16. A dangling `ref` symlink** pointed at the previous machine's scratchpad, so the clone step
silently did nothing (the `cd` failed and short-circuited the `&&` chain).

### Process problems

**17. Two sessions shared one working tree and branch.** A commit from the other session landed
mid-edit and was later swept into a history squash; both sessions independently found and fixed
the *same* censoring bug minutes apart; and at one point both were a keystroke away from
concurrent appends to the same JSONL, where rollout lines far exceed the 4096-byte atomic-write
boundary and would have interleaved into corruption rather than merely racing. No data was
actually lost. Resolved by the user stopping the second session.

**18. Roughly two GPU-hours wasted by over-correcting.** When stripping censored rollouts for
regeneration at the higher cap, all 210 were removed when only aime's 97 needed it -- for gpqa
and amc the p20 rank already fell inside the completed data, so a rollout censored at 16384
already carried everything the percentile needed. Caught after ~10 minutes; 106 were restored.

**19. Two false alarms from bad verification code, not bad data.** A probe of the
`fast_langdetect` 80-character truncation reported "156/156 translations failing" -- it was
passing an argument the installed version does not accept, so every call raised and returned an
error sentinel. A later check reported "answer leaked into the prompt" for all 927 SFT rows --
it was matching the literal string `<answer>`, which the ReasonIF template legitimately contains
in its instruction. Both were the checker's fault. Worth recording because a verification script
that is itself wrong is more dangerous than no check.

### Known and accepted

**20. `fast_langdetect` truncates input to 80 characters by default.** Real, and it applies to
the `reasoning_language` and `english_capital` graders in the eval too. Harmless here: all 156
translated SFT traces are detected as their target language, because a translated trace opens in
that language. Recorded because a library bump could change the default.

**21. Mixed censoring levels in the calibration.** gpqa and amc censored observations sit at a
16384 cap, aime's at 32768, because the former were restored rather than regenerated. Harmless
for a rank-based low percentile -- p20 falls far below the smallest censored value in every
source -- but a real detail of how the numbers were produced.

**22. Baseline compliance of exactly zero leaves the accuracy cross-tab one-armed.** With no
compliant CoTControl rollout at baseline, whether complying costs accuracy cannot be answered
from this run. It becomes answerable after fine-tuning.

## Verification status (2026-09-11)

Full re-verification of every artifact, all checks passing: SFT dataset (927 rows, unique
row_idx and question_id, all six modes, well-formed `<think>` turns, 100 percent passing their
own canonical grader, prompts stating the same constraint the grader checked, modes and
question ids matching the plan); baseline (300 ReasonIF unique, 2700 CoTControl as 300
questions x 9 modes with the identical question set in every mode, zero errors, summaries
reproducing on a fresh re-grade, accuracy reflecting the letter fix); calibration (900
rollouts, limits matching the stats file, all p20 identifiable, and the limits actually used by
the baseline run).
