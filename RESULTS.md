# Results: replicating METR's CoT-controllability fine-tuning on Qwen3.5-9B

Independent replication (own pipeline, different model) of METR's *Fine-tuning experiments on CoT
controllability*. Method, deviations and the full problem log are in `METHODOLOGY.md`; the
continuous-scoring design is in `CONTINUOUS_SCORING.md`.

**Model** Qwen/Qwen3.5-9B · **Hardware** single RTX 5090 (32 GB) · **Checkpoint** step-60
(60 optimizer steps × effective batch 4 = 240 SFT examples, METR's headline)

---

## 1. Headline

| suite | base | step-60 | METR's Qwen3-8B for scale |
|---|---:|---:|---|
| ReasonIF (in-distribution) | 5.7 % | **23.7 %** | 20.9 → 43.8 |
| CoTControl (out-of-distribution) | 0.0 % | **0.8 %** | 1.1 → 5.6 |

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

The ReasonIF uplift is comparable to METR's in magnitude (+18.0 pp vs +22.9 pp). The CoTControl
uplift is roughly five times smaller. Given the continuous analysis, the most likely explanation
is that on this model 240 examples buy format-specific imitation rather than general
instruction-following — and the OOD modes that happen to resemble a trained format are the only
ones that move.
