# Would suppressing meta-discussion help compliance? A strip-and-regrade ceiling test

**Question.** If the model stopped narrating the constraint ("the instruction says…", "Constraint 1:
do not use the word X"), would its reasoning comply more often? This matters for deciding whether
to spend effort on anti-meta-discussion steering.

**Method.** Take the stored CoTControl rollouts (base and step-60, 2,700 each), delete the narration
sentences, re-grade with the unchanged binary graders and the continuous v2 scores. This measures
*compliance if the narration text were removed and nothing else changed* — an upper bound on what
any narration-suppression method could buy through the direct route (the narration itself being
the violating text). The detector that picks sentences is independent of the grader, so the test
cannot become "delete the violating sentences".

Four stripping variants:

| variant | what is removed | note |
|---|---|---|
| `preamble` | leading paragraphs, while each contains a narration match | the original "strip the first few sentences" idea |
| `strong` | every sentence matching one of the six specific METR patterns (bare `constraint` excluded) | precise, whole trace |
| `all7` | every sentence matching any of the seven METR patterns, i.e. any sentence containing `constraint` | deliberately over-generous |
| `judge` | the gpt-5-mini judge's quoted excerpts (first 10,000 chars, where it said yes) | paper's detector |

Script: `scripts/strip_regrade.py`; raw numbers: `results/strip_test/strip_regrade.json`. Runs in
90 s on CPU, no API calls. `ignore_question` needs the LLM judge for both scores and is not re-run.

## Result: the ceiling is zero

**Binary compliance does not change under any variant, at either checkpoint.** Among rollouts that
narrate (strong pattern present), the share that flips fail → pass when narration is deleted is
**0.0 % in all eight gradeable modes, base and step-60.**

![Continuous score, unchanged vs all narration deleted](figures/strip_dumbbell.png)

Continuous scores (higher = more compliant; `orig` = unchanged trace):

| mode | base orig | base `strong` | base `all7` | base `judge` | step-60 orig | step-60 `strong` | step-60 `all7` | step-60 `judge` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| uppercase_thinking | 0.135 | 0.136 | 0.143 | 0.136 | 0.319 | 0.319 | 0.319 | 0.319 |
| lowercase_thinking | 0.932 | 0.932 | 0.931 | 0.932 | 0.925 | 0.925 | 0.925 | 0.925 |
| alternating_case | 0.407 | 0.408 | 0.419 | 0.409 | 0.217 | 0.218 | 0.223 | 0.218 |
| word_suppression | 0.497 | 0.499 | **0.537** | 0.507 | 0.536 | 0.538 | 0.554 | 0.541 |
| multiple_word_suppression | 0.149 | 0.150 | 0.169 | 0.159 | 0.146 | 0.147 | 0.159 | 0.155 |
| repeat_sentences | 0.295 | 0.295 | 0.295 | 0.297 | 0.267 | 0.267 | 0.266 | 0.266 |
| end_of_sentence | 0.039 | 0.039 | 0.042 | 0.039 | 0.008 | 0.008 | 0.008 | 0.008 |
| meow_between_words | 0.117 | 0.118 | 0.127 | 0.118 | 0.055 | 0.055 | 0.058 | 0.055 |

The largest movement anywhere is word_suppression at base under the over-generous `all7` variant:
+0.040, which recovers 8 % of the available headroom. Every other cell recovers 0–2 %.

How much text the variants remove (share of characters): `preamble` 0–1.7 %, `strong` 0.3–1.2 %,
`all7` 1.7–9.8 %, `judge` 0.3–1.9 %. Narration is one or two sentences in a trace of ~25,000
characters.

## Why: the violation is the body, not the narration

![Where the violation lives vs where the narration lives](figures/strip_where_violation_lives.png)

For six modes with a countable violation unit (lowercase letters, uppercase letters, non-alternating
words, forbidden-word uses, sentences not ending in the target), the share of violations inside
narration sentences tracks the share of text those sentences occupy: 2–9 % in both cases. Narration
is not where the violations concentrate. (`results/strip_test/violation_location.json`)

Two direct measurements at base:

- **word_suppression**: of all forbidden-word uses in a trace, only ~15 % sit inside narration
  sentences (spot-checked: 4/23, 6/26, 4/43). The model keeps using the word throughout its
  ordinary reasoning.
- **uppercase_thinking**: 5.5 % of the lowercase letters (the violation) sit inside narration
  sentences. The other 94.5 % are the body, written in normal case.

The continuous scores say the same thing at the population level: base uppercase 0.135 means
86 % of letters are lowercase; end_of_sentence 0.039 means 96 % of sentences do not end in the
target word. Deleting a couple of narration sentences cannot move that.

## What this does and does not say about steering

- **It rules out the direct mechanism.** "The model fails because the narration sentence itself
  breaks the constraint" is false for this model on these modes. Steering that only removed
  narration, leaving the body as it is, would buy nothing.
- **It is consistent with the natural experiment already in hand.** Fine-tuning cut narration by
  31–50 pp (see `META_DISCUSSION.md`) while binary compliance moved 0.0 → 0.8 pp and the
  continuous net went negative.
- **It cannot rule out an indirect effect.** Steering changes the whole generation, not just the
  narration. A model steered away from *thinking about* the constraint might comply less (if the
  narration is scaffolding) or more (if narration is a symptom of a mode where the model
  "discusses instead of does"). This test holds the body fixed, so it is silent on that. The
  honest reading is: there is no cheap win here, and a steering experiment would be testing the
  indirect hypothesis only, with a prior set by the null above and by the fine-tuning result.
- **The `preamble` variant would have been a null for the wrong reason.** Narration is not a
  preamble: at base the first regex hit is at median char 447, but at step-60 it is at 6,635 and
  38 % of narrating traces first narrate past 10,000 chars. `preamble` removed 0 % of the text in
  most modes. Whole-trace sentence detection is the right instrument.

## Caveats

- The strong patterns also catch discussion of the *answer-format* instruction ("the instruction
  says 'ANSWER: X'"), which is not constraint narration. That over-removes, which only makes the
  ceiling more generous; the null stands.
- The `judge` variant is limited to the judge's 10,000-char window and to rollouts it flagged.
- `ignore_question` is not covered. It is the one mode where narration ("the user asks about X")
  is plausibly the violation itself; testing it costs ~600 judge calls (< $1) on stripped traces.
- This is Qwen3.5-9B. A model whose failures *were* concentrated in a narration preamble would
  show a non-zero ceiling here; the test is cheap enough to run on any model before steering it.
