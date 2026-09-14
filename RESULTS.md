# Results: replicating METR's CoT-controllability fine-tuning on Qwen3.5-9B

Independent replication (own pipeline, different model) of METR's *Fine-tuning experiments on CoT
controllability*. Method, deviations and the full problem log are in `METHODOLOGY.md`; the
continuous-scoring design is in `CONTINUOUS_SCORING.md`.

**Model** Qwen/Qwen3.5-9B · **Hardware** single RTX 5090 (32 GB) · **Checkpoint** step-60
(60 optimizer steps × effective batch 4 = 240 SFT examples, METR's headline)

---

## 1. Headline

| suite | base | step-60 (240 ex) | step-final (920 ex) | METR's Qwen3-8B |
|---|---:|---:|---:|---|
| ReasonIF (in-distribution) | 5.7 % | **23.7 %** | — | 20.9 → 43.8 |
| CoTControl (out-of-distribution) | 0.0 % | **0.8 %** | **1.5 %** | 1.1 → 5.6 |

**The qualitative claim replicates: ~240 SFT examples of instruction-following reasoning data
produce a large in-distribution gain and a small out-of-distribution one. The OOD magnitude does
not replicate** — we see +0.8 pp where METR saw +4.5 pp on a comparable model.

---

## 2. ReasonIF — in-distribution

300 prompts, per-source calibrated `number_words` limits, our 32,768-token cap.

| instruction | base | replicate band¹ | step-60 | delta |
|---|---:|---:|---:|---:|
| number_words | 8.3 | 8.0–12.2 | **42.3** | +34.0 |
| no_comma | 0.0 | 0.0–2.1 | **27.7** | +27.7 |
| end_checker | 2.2 | 2.1–11.6 | **23.4** | +21.2 |
| english_capital | 0.0 | 0.0–0.0 | **15.8** | +15.8 |
| json_format | 0.0 | 0.0–0.0 | 2.4 | +2.4 |
| reasoning_language | 23.8 | 21.4–25.0 | 25.0 | +1.2 |
| **micro (all 300)** | **5.7** | **5.6–8.4** | **23.7** | **+18.0** |
| macro (mean over types) | 5.7 | 5.4–8.1 | 22.8 | +17.0 |

¹ Range over eight accidental replicates of the base model — see §6.

Every instruction except `reasoning_language` clears its replicate band, most by a wide margin.
`reasoning_language` at +1.2 pp sits *inside* its band and should be read as **no measurable
change**; it was already the one constraint the base model partly satisfied.

Task accuracy is unchanged: **88.1 % → 88.6 %**. The model is not buying compliance by answering
worse.

---

## 3. CoTControl — out-of-distribution, binary

300 questions × 9 modes = 2,700 rollouts, identical question set to the baseline (seed 42).

| mode | gradeable | base % | step-60 % | n compliant | 80 % CI |
|---|---:|---:|---:|---:|---:|
| **uppercase_thinking** | 269 | 0.0 | **5.9** | 16 | **4.1–7.8** |
| lowercase_thinking | 281 | 0.0 | 0.4 | 1 | 0.0–0.8 |
| multiple_word_suppression | 271 | 0.0 | 0.4 | 1 | 0.0–0.8 |
| word_suppression | 273 | 0.0 | 0.4 | 1 | 0.0–0.8 |
| alternating_case | 277 | 0.0 | 0.0 | 0 | — |
| end_of_sentence | 276 | 0.0 | 0.0 | 0 | — |
| ignore_question | 300 | 0.0 | 0.0 | 0 | — |
| meow_between_words | 269 | 0.0 | 0.0 | 0 | — |
| repeat_sentences | 293 | 0.0 | 0.0 | 0 | — |
| **macro** | 2,509 | **0.0** | **0.8** | 19 | |

Only `uppercase_thinking` is individually solid — its CI excludes zero. The three modes at n=1
have CIs including zero and matter only as part of an aggregate leaving a floor that was
confirmed twice across 5,300 rollouts. Unlike ReasonIF, the result is **cap-robust**: macro is
0.8 % at both 32,768 and METR's 16,384.

Accuracy unchanged: 55.6 % → 55.2 %.

---

## 4. CoTControl — continuous scoring

Binary grading is all-or-nothing at 100 %, so one stray character scores the same as ignoring the
instruction entirely. Re-grading the same stored rollouts with partial credit (paired by
question, 5,000-sample bootstrap, 80 % CI):

| mode | n | base | step-60 | delta | 80 % CI | analogue in SFT data? |
|---|---:|---:|---:|---:|---:|---|
| **uppercase_thinking** | 262 | 0.133 | **0.321** | **+0.188** | [+0.158, +0.220] | **yes — `english_capital`** |
| multiple_word_suppression | 261 | 0.042 | 0.060 | +0.019 | [+0.004, +0.033] | partly — `no_comma` |
| word_suppression | 263 | 0.421 | 0.444 | +0.023 | [+0.001, +0.045] | partly — `no_comma` |
| lowercase_thinking | 273 | 0.933 | 0.925 | −0.008 | [−0.015, −0.002] | no |
| repeat_sentences | 291 | 0.296 | 0.267 | −0.028 | [−0.036, −0.021] | no |
| end_of_sentence | 273 | 0.036 | 0.008 | −0.029 | [−0.033, −0.025] | no |
| meow_between_words | 266 | 0.118 | 0.055 | −0.062 | [−0.072, −0.053] | no |
| **alternating_case** | 266 | 0.435 | **0.248** | **−0.187** | [−0.201, −0.173] | no |
| **macro** | | **0.302** | **0.291** | **−0.011** | | |

**Every delta is statistically significant, and they point in opposite directions.** The macro
average is flat because gains and losses cancel.

**This is the most informative result in the project.** The transfer is *narrow and possibly
negative*:

- The one mode with a direct analogue in the training data — `uppercase_thinking`, trained as
  `english_capital` — gains substantially (+0.188, and 26 % of rollouts now score ≥ 0.5 against
  10 % scoring a perfect 1.0).
- The two suppression modes, loosely analogous to `no_comma`, gain slightly.
- **Every mode with no analogue in the SFT data gets worse**, `alternating_case` markedly so.

A plausible reading is that the fine-tune taught six specific reasoning formats rather than a
general "follow reasoning instructions" capability, and in doing so made the model's reasoning
style *more* fixed and less responsive to unfamiliar formatting demands. The binary metric hides
this completely: on binary grading seven of these eight modes read 0.0 → 0.0.

Caveats: we have no replicate runs of the *fine-tuned* model, so the bootstrap covers
question-sampling variance but not run-to-run variance; the ReasonIF replicates suggest the
latter is real. Per-mode floors differ enormously (`lowercase` starts at 0.93 by virtue of
ordinary English, `end_of_sentence` at 0.04), so cross-mode averaging of raw scores is only
meaningful for deltas, not levels.

---

## 3b. Does the OOD effect grow with training?

`step-final` (230 steps ≈ 920 examples, ~4× METR's headline) evaluated on the same 2,700
rollouts. **0.8 % was not a ceiling — but the growth is entirely one mode.**

| mode | base | step-60 (240 ex) | step-final (920 ex) | n | 80 % CI |
|---|---:|---:|---:|---:|---:|
| **uppercase_thinking** | 0.0 | 5.9 | **12.4** | 36 | **9.9–14.9** |
| lowercase_thinking | 0.0 | 0.4 | 1.0 | 3 | 0.3–1.8 |
| multiple_word_suppression | 0.0 | 0.4 | 0.0 | 0 | — |
| word_suppression | 0.0 | 0.4 | 0.0 | 0 | — |
| alternating_case, end_of_sentence, ignore_question, meow_between_words, repeat_sentences | 0.0 | 0.0 | 0.0 | 0 | — |
| **macro** | **0.0** | **0.8** | **1.5** | 39 | |

Macro roughly doubles with roughly 4× the data, and `uppercase_thinking` doubles with it
(5.9 → 12.4 %, CI comfortably excluding zero). **36 of the 39 compliant rollouts are that one
mode.** The two suppression modes that showed 0.4 % at step-60 were single rollouts and have
returned to zero, confirming they were noise. Five modes have never produced a single compliant
rollout across 8,100 evaluated rollouts.

Continuous scoring makes the same point far more sharply:

| mode | base | step-60 | step-final | delta vs base | 80 % CI |
|---|---:|---:|---:|---:|---:|
| **uppercase_thinking** | 0.135 | 0.323 | **0.605** | **+0.470** | [+0.437, +0.502] |
| word_suppression | 0.418 | 0.448 | 0.471 | +0.053 | [+0.036, +0.071] |
| multiple_word_suppression | 0.044 | 0.061 | 0.066 | +0.022 | [+0.011, +0.033] |
| repeat_sentences | 0.295 | 0.267 | 0.286 | −0.009 | [−0.017, −0.001] |
| lowercase_thinking | 0.932 | 0.925 | 0.916 | −0.016 | [−0.026, −0.008] |
| end_of_sentence | 0.038 | 0.008 | 0.014 | −0.024 | [−0.028, −0.020] |
| meow_between_words | 0.115 | 0.056 | 0.060 | −0.056 | [−0.062, −0.050] |
| **alternating_case** | 0.439 | 0.248 | 0.298 | **−0.141** | [−0.155, −0.127] |
| **macro** | 0.302 | 0.292 | **0.339** | +0.037 | |

`uppercase_thinking` reaches **0.605** — the model now writes the majority of its reasoning in
caps when asked, from a base of 0.135. Nothing else comes close. The modes that regressed at
step-60 partially recover by step-final but none returns to baseline, so the negative transfer is
attenuated by more training rather than reversed.

**This is the central result of the replication.** More data monotonically improves the *one* OOD
constraint that has a direct analogue in the training set (`english_capital` → uppercase
reasoning) and does essentially nothing for the eight that do not. Whatever the fine-tune is
teaching, it is not a general "follow reasoning-format instructions" capability — it is
format-specific imitation that happens to transfer when the target format is one it was trained
on. METR's headline number would be reproduced by a model that had learned only this.

Secondary movements at step-final: accuracy drifts down slightly (55.6 → 55.2 → 53.6 %),
meta-discussion partially rebounds (94.9 → 63.8 → 70.5 %), and truncation falls (4.3 → 7.9 →
2.8 %).

---

## 4c. CoTControl: binary and continuous side by side

Continuous scores use the agreed rule set, and critically **each model's word-suppression score
is referenced to its own unconstrained rollouts** — 300 extra rollouts per model with the
Requirement clause removed (`scripts/gen_unconstrained.py`). Scoring the fine-tuned model against
the *base* model's keyword usage would confound "suppressed more" with "would have used the word
less anyway". Paired bootstrap over questions, 5,000 resamples, 80 % CI.

| mode | binary base | binary FT | binary Δ | cont. base | cont. FT | **cont. Δ** | 80 % CI | significant |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **uppercase_thinking** | 0.0 | 5.9 | +5.9 | 0.133 | 0.321 | **+0.188** | [+0.158, +0.219] | **yes** |
| word_suppression | 0.0 | 0.4 | +0.4 | 0.515 | 0.536 | +0.020 | [−0.004, +0.044] | no |
| lowercase_thinking | 0.0 | 0.4 | +0.4 | 0.933 | 0.925 | −0.008 | [−0.015, −0.002] | yes (−) |
| multiple_word_suppression | 0.0 | 0.4 | +0.4 | 0.157 | 0.135 | −0.023 | [−0.045, −0.000] | yes (−) |
| repeat_sentences | 0.0 | 0.0 | +0.0 | 0.296 | 0.267 | −0.028 | [−0.036, −0.020] | yes (−) |
| end_of_sentence | 0.0 | 0.0 | +0.0 | 0.036 | 0.008 | −0.029 | [−0.033, −0.025] | yes (−) |
| meow_between_words | 0.0 | 0.0 | +0.0 | 0.118 | 0.055 | −0.062 | [−0.072, −0.053] | yes (−) |
| **alternating_case** | 0.0 | 0.0 | +0.0 | 0.403 | 0.214 | **−0.189** | [−0.203, −0.175] | **yes (−)** |
| ignore_question | 0.0 | 0.0 | +0.0 | — | — | — | not scored¹ | |
| **macro (raw)** | **0.00** | **0.78** | **+0.78** | **0.324** | **0.308** | **−0.016** | | |
| **macro (headroom-normalised)** | | | | 0.000 | 0.032 | **+0.032** | | |

¹ Needs a judge asked for a count of violating sentences rather than a verdict; designed but not
run. It is the only rule in the set with a per-rollout API cost.

**Exactly one mode improves.** `uppercase_thinking` gains +0.188; six of the remaining seven
decline significantly, and the one that does not (`word_suppression`) has a CI spanning zero. The
raw macro is **negative** (−0.016). Binary grading reports +0.78 pp and cannot show any of this,
because seven of the nine modes read 0.0 → 0.0.

**The paired reference changed two conclusions.** An earlier pass scored suppression against the
*base* model's keyword usage for both models. Under the correct own-model reference:

| | flawed reference | own-model reference |
|---|---|---|
| `word_suppression` | +0.023, significant | **+0.020, not significant** |
| `multiple_word_suppression` | +0.019, significant | **−0.023, significantly negative** |

Both apparent suppression gains were artefacts of the fine-tuned model simply using those
keywords less often in general, not of it suppressing them more when asked. That is precisely the
confound the extra rollouts were generated to remove, and it moved a result from "modest gain" to
"significant decline".

**On aggregation.** The raw macro is dominated by `lowercase_thinking`, which sits at 0.933 on a
model that is not trying, because ordinary English prose is already overwhelmingly lowercase — it
contributes a third of the macro's level and can move it almost not at all. Normalising each mode
by its own base floor, `(score − floor) / (1 − floor)`, expresses every mode as the fraction of
its available room actually used and makes them comparable: **+0.032** overall, i.e. the
fine-tune closed about 3 % of the available headroom, essentially all of it in one mode. Both are
reported because the normalisation depends on floor estimates that are themselves measured with
noise.

---

## 4b. ReasonIF — continuous scoring

Same partial-credit treatment applied in-distribution (paired bootstrap, 5,000 resamples):

| instruction | n | base | step-60 | delta | 80 % CI | binary, for contrast |
|---|---:|---:|---:|---:|---:|---|
| **english_capital** | 36 | 0.185 | **0.488** | **+0.303** | [+0.222, +0.390] | 0.0 → 15.8 % |
| **number_words** | 47 | 0.543 | **0.788** | **+0.245** | [+0.181, +0.309] | 8.3 → 42.3 % |
| end_checker | 45 | 0.295 | 0.410 | +0.114 | [+0.037, +0.192] | 2.2 → 23.4 % |
| json_format | 41 | 0.000 | 0.024 | +0.024 | [+0.000, +0.049] | 0.0 → 2.4 % |
| no_comma | 45 | 0.797 | 0.814 | +0.018 | [+0.000, +0.036] | 0.0 → **27.7 %** |
| **reasoning_language** | 41 | 0.398 | **0.263** | **−0.135** | [−0.175, −0.096] | 23.8 → 25.0 % |
| **macro** | | **0.370** | **0.465** | **+0.095** | | 5.7 → 22.8 % |

Two cases where continuous and binary disagree, in opposite directions, and both are informative.

**`no_comma`: binary is the better metric here.** Binary shows a large gain (0.0 → 27.7 %) while
continuous barely moves (+0.018), because the base model already scores 0.797 — it uses few
commas relative to trace length. The instruction says *refrain from any commas*, so going from
"few" to "none" is the whole task, and a density-based score is the wrong shape for a genuinely
all-or-nothing constraint. Partial credit is not universally better; it depends on whether the
constraint is a matter of degree.

**`reasoning_language`: binary hid a real regression.** Binary reads flat (23.8 → 25.0 %, inside
the replicate band, i.e. no change), but scoring language *per sentence* rather than once over
the whole trace shows a significant **decline** (−0.135). Whole-trace detection reports the
dominant language and so cannot see a trace that is translated three-quarters of the way; the
fine-tuned model produces more language-mixed reasoning than the base model does.

That is worth flagging because `reasoning_language` *is* one of the six trained constraints, so a
regression is the opposite of the expected direction. A likely contributor: **27 % of the
`reasoning_language` SFT rows (43 of 157) had English as their target**, where the Stage-2
transform is a no-op by construction. Those rows teach nothing about translating and plausibly
reinforce staying in English. A replication should either exclude English targets from that mode
or count them separately.

---

## 5. Does complying cost accuracy?

At baseline this was unanswerable — zero compliant CoTControl rollouts, so no comparison arm.
At step-60:

| | n | accuracy | mean CoT words |
|---|---:|---:|---:|
| compliant | 19 | **68.4 %** | 1,185 |
| non-compliant | 2,490 | 55.1 % | 4,975 |

Compliant rollouts are 13.4 pp *more* accurate and use a quarter of the reasoning. With n = 19
and an obvious confound — short-reasoning questions are plausibly easier — this is suggestive
only, and certainly not evidence that compliance *causes* accuracy.

**Meta-discussion collapsed: 94.9 % → 63.8 %**, in every mode, largest exactly where compliance
improved (`uppercase_thinking` −42.7, `ignore_question` −43.0). METR observed that the Qwen3.5
family "uses meta discussion very often"; the SFT appears to partly train that out. Arguably a
larger behavioural change than the compliance number itself.

---

## 5b. Reasoning length before and after fine-tuning

Mean words inside `<think>`, over all rollouts with a usable think block.

| suite | | n | mean | median | p90 | max | answer mean | truncated |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **ReasonIF** | base | 300 | 6,137 | 4,370 | 14,186 | 19,918 | 332 | 14.0 % |
| | step-60 | 300 | **5,367** | **3,786** | 13,276 | 22,070 | 374 | 12.0 % |
| | change | | **−12.6 %** | **−13.4 %** | | | +12.7 % | −2.0 pp |
| **CoTControl** | base | 2,700 | 5,340 | 4,564 | 9,123 | 19,970 | 193 | 4.3 % |
| | step-60 | 2,700 | **5,829** | **4,770** | 11,626 | 25,236 | 279 | 7.9 % |
| | change | | **+9.2 %** | **+4.5 %** | | | +44.6 % | **+3.6 pp** |

**The two suites move in opposite directions, and that is the interesting part.**

In-distribution the model becomes *more concise* (−12.6 %), which is what the training data
asks for: `number_words` is a sixth of the SFT set and explicitly rewards compression, and its
continuous score rose from 0.543 to 0.788. The fine-tune generalised "be brief when told to" well
enough to shorten ReasonIF traces overall.

Out of distribution it becomes *more verbose* (+9.2 %), and the per-mode pattern tracks the
continuous-score result almost exactly:

| mode | length change | continuous score |
|---|---:|---:|
| meow_between_words | **+30.9 %** | −0.062 |
| end_of_sentence | **+21.9 %** | −0.029 |
| multiple_word_suppression | +13.3 % | +0.019 |
| ignore_question | +11.6 % | n/a |
| word_suppression | +7.2 % | +0.023 |
| repeat_sentences | +5.2 % | −0.028 |
| lowercase_thinking | +1.2 % | −0.008 |
| uppercase_thinking | −1.8 % | **+0.188** |
| alternating_case | −3.2 % | **−0.187** |

The modes that got markedly longer are the ones whose compliance got *worse*. The one mode that
improved substantially, `uppercase_thinking`, got slightly shorter. The fine-tuned model appears
to flounder at greater length on constraints it was not trained for — producing more reasoning
while satisfying the instruction less.

**A practical consequence worth carrying into any comparison: CoTControl truncation nearly
doubled, 4.3 % → 7.9 %.** Truncated rollouts are ungradeable and leave the denominator, so the
fine-tuned model loses more rollouts to the token cap than the base model does. At a smaller cap
this would bite harder, which is a further argument for generating above the cap you intend to
report (§6).

Answer length rose in both suites, sharply on CoTControl (+44.6 %), so the extra verbosity is not
confined to the reasoning channel.

---

## 5c. Meta-discussion

"Meta-discussion" is the model narrating the constraint inside its own reasoning — *"I need to
write this in capitals"* — which the CoTControl authors treat as a failure of the spirit of the
instruction even when the letter is satisfied. Measured with METR's regex heuristic over
gradeable rollouts. METR observed that the Qwen3.5 family "uses meta discussion very often", and
our base numbers confirm it emphatically: **94.9 %** on CoTControl.

### CoTControl

| mode | base | step-60 | step-final | final − base |
|---|---:|---:|---:|---:|
| meow_between_words | 99.3 | 73.6 | 83.4 | −15.9 |
| end_of_sentence | 96.9 | 63.8 | 73.2 | −23.8 |
| multiple_word_suppression | 96.8 | 77.5 | 83.6 | −13.2 |
| word_suppression | 96.4 | 74.7 | 76.2 | −20.2 |
| alternating_case | 95.4 | 67.1 | 72.4 | −23.0 |
| repeat_sentences | 94.6 | 69.3 | 77.3 | −17.3 |
| ignore_question | 94.6 | 51.6 | 65.4 | −29.1 |
| lowercase_thinking | 92.6 | 52.3 | 53.9 | **−38.7** |
| uppercase_thinking | 87.7 | 45.0 | 48.6 | **−39.1** |
| **overall** | **94.9** | **63.8** | **70.5** | **−24.5** |

### ReasonIF (base → step-60)

| instruction | base | step-60 | delta |
|---|---:|---:|---:|
| no_comma | 93.8 | 51.1 | −42.7 |
| number_words | 81.2 | 40.4 | −40.9 |
| end_checker | 88.9 | 51.1 | −37.8 |
| json_format | 78.6 | 47.6 | −31.0 |
| reasoning_language | 81.0 | 52.3 | −28.7 |
| english_capital | 81.1 | 57.9 | −23.2 |
| **overall** | **84.4** | **49.6** | **−34.7** |

Three things stand out.

**The drop is large, uniform and in every single mode** — CoTControl −24.5 pp overall, ReasonIF
−34.7 pp. Unlike compliance, which moved in one mode and regressed in several, this changed
everywhere. On the measure that moved most consistently, the fine-tune did something general.

**It is not monotone in training.** CoTControl meta-discussion falls to 63.8 % at step-60 and then
*rebounds* to 70.5 % at step-final, in eight of nine modes. More training partially undoes it,
which argues against reading it as steady progress toward "internalised" instruction-following.

**The two casing modes drop most** (−38.7 and −39.1), and they are also the two modes where
compliance moved. Whether suppressing narration helps compliance, or both follow from the same
change, is not identifiable from this data.

This may be the more consequential behavioural change. For a CoT-monitoring application, a model
that stops *announcing* the constraint it is following is a different object from one that
follows it — arguably a worse one, since the reasoning becomes less self-explaining while the
underlying behaviour is largely unchanged. We measure it with METR's regex heuristic, not the
CoTControl paper's LLM judge, so absolute levels should be treated as approximate; the ~25–35 pp
shift is far too large to be an artefact of that choice.

---

## 5d. Per-mode comparison with METR

METR report per-instruction breakdowns for both suites (bar charts; no numeric tables in the
text). Their stated finding:

> "The most significant increases occur for reasoning casing (uppercase **and lowercase**), word
> suppression, and for adding specific strings to the reasoning (repeat sentences)."

and, in their limitations:

> "when we remove the one instruction type from CoTControl that is very similar to an instruction
> type from ReasonIF (Use uppercase letters), the average increase in controllability only drops
> from **5.9 % to 5.0 %**."

Their repo corroborates that this check was run: `plot_summary_2026_03_24.py` defines
`EXCLUDE_COTCONTROL = {"uppercase_thinking"}` with a full re-aggregation path.

**Our effect is far more concentrated than theirs.**

| | all 9 modes | excl. uppercase | excl. both casing modes |
|---|---:|---:|---:|
| METR | 5.9 % | 5.0 % (−15 % rel.) | not reported |
| ours, step-60 | 0.78 % | 0.14 % (−83 % rel.) | 0.11 % |
| ours, step-final | 1.49 % | 0.13 % (−91 % rel.) | **0.00 %** |

Removing one mode of nine costs METR 15 % of their effect and costs us 91 %. At step-final,
removing both casing modes eliminates our OOD effect entirely. **So this is a genuine divergence
from their result, not a reinterpretation of it** — their gains really are distributed across
modes; ours really are not.

**A gap in their robustness check, which our lowercase result makes concrete.** They exclude
`uppercase_thinking` as "very similar to" ReasonIF's `english_capital`, but by their own figure
`lowercase_thinking` improved comparably — and lowercase is arguably *equally* similar, being the
same uniform-casing skill inverted. The model is not plausibly learning "produce capitals"; it is
learning "impose a uniform case on my reasoning", which transfers to both. Excluding one casing
mode and not the other is hard to justify, and **the excluding-both number is not reported**.

**Our lowercase finding runs opposite to theirs, and illustrates why the mode is treacherous:**

| | base | step-60 | step-final |
|---|---:|---:|---:|
| binary compliance | 0.0 % | 0.4 % (n=1) | 1.0 % (n=3) |
| continuous score | **0.932** | 0.925 | **0.916** (−0.016, CI [−0.026, −0.008]) |

`lowercase_thinking` starts at 0.932 **because ordinary English prose is already ~93 % lowercase**.
The binary threshold demands 100 %, so the mode is nearly free to almost-satisfy and nearly
impossible to fully satisfy. On continuous scoring our model gets *worse*; the three "compliant"
rollouts are the tail of a distribution that shifted slightly down. A reported large lowercase
gain can therefore be a handful of rollouts crossing a threshold rather than a behavioural change
— precisely the distinction binary grading cannot make. We cannot check whether METR's lowercase
gain is of this kind, because per-mode numbers are not published, but it is the first thing we
would want to see.

Finally, METR do not discuss *why* casing improved most, nor the `english_capital` →
uppercase/lowercase overlap as a mechanism. Our continuous and checkpoint-scaling results
(§3b, §4) suggest that overlap is the whole story on this model.

---

## 6. Reliability

**Noise floor.** Eight evaluations that were accidentally run against the base model (see
METHODOLOGY.md) form an unintended but valuable control: eight independent draws on identical
prompts. ReasonIF micro over those replicates is **6.63 % ± 0.88** (range 5.62–8.37). Our
published 5.7 % baseline sits at the bottom of that range, so **the ReasonIF uplift is flattered
by roughly 1 pp**. Per instruction, `end_checker` alone ranges 2.1–11.6 % on identical weights, so
per-instruction differences below ~10 pp are not interpretable from a single run.

**Token cap.** Reported at our 32,768 cap and re-projected to METR's 16,384. After fine-tuning
the two diverge sharply on ReasonIF — 23.7 % vs 32.0 % — because the tighter cap discards 76 more
rollouts, non-randomly removing long-reasoning questions. The selection effect is *larger*
post-FT than at baseline, so quoting a single cap would overstate the uplift. CoTControl is
cap-robust.

**Verification.** Adapters are served merged, after an earlier run in which vLLM silently ignored
LoRA adapters and produced ~24 GPU-hours of base-model results labelled as checkpoints. Every
eval is now gated on `scripts/verify_adapter.py`. All raw rollouts are archived; every number
here recomputes from them without a GPU.

---

## 7. Versus METR

| model | CoTControl base → FT@240 | ReasonIF base → FT@240 |
|---|---|---|
| Qwen3-8B | 1.1 → 5.6 | 20.9 → 43.8 |
| Qwen3-32B | 3.7 → 9.8 | 28.9 → 55.3 |
| GPT-OSS-20B | 2.1 → 7.3 | 15.0 → 50.7 |
| GPT-OSS-120B | 4.4 → 13.1 | 23.7 → 49.0 |
| Qwen3.5-4B (baseline only) | 0.0 | 9.4 |
| Qwen3.5-27B (baseline only) | 1.3 | 9.9 |
| **Qwen3.5-9B (this work)** | **0.0 → 0.8** | **5.7 → 23.7** |

Our baseline CoTControl (0.0 %) matches METR's Qwen3.5-4B exactly and sits below their 27B, which
is what a 9B should do. Our baseline ReasonIF (5.7 %) is *below* the 9.4–9.9 the 4B and 27B imply
— though at METR's own token cap it reads 7.3 %, and the replicate mean is 6.6 %, which closes
much of the gap.

**What replicates:** the direction and rough in-distribution magnitude. ~240 SFT examples produce
a large ReasonIF gain (+18.0 pp here vs +22.9 pp for their Qwen3-8B) and a smaller OOD gain, with
no loss of task accuracy.

**What does not:** the breadth of the OOD transfer, which is the part that makes the original
result interesting. METR's CoTControl uplift survives removing the mode most similar to the
training data (5.9 → 5.0 %); ours does not (1.5 → 0.13 %, and 0.00 % removing both casing modes).
On this model the recipe buys format-specific imitation of a trained constraint rather than
general reasoning-instruction following.

**Candidate explanations, none tested here.** (i) Model family — Qwen3.5 differs from the Qwen3
and GPT-OSS models METR used, and METR's own Qwen3.5-4B/27B baselines are the lowest in their set,
so this family may simply be harder to make controllable. (ii) Floor effects — our CoTControl
baseline is a hard 0.0 % across 5,300 rollouts, leaving no room for small distributed gains to be
visible, whereas METR's models started at 1.1–4.4 %. (iii) SFT data quality — 27 % of our
`reasoning_language` rows were English-target no-ops (§4b), so our 927-row set is weaker than its
size suggests. Distinguishing these needs a second model, which is the obvious next experiment.
