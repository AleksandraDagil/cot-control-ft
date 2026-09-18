#!/usr/bin/env python3
"""Figures for META_DISCUSSION.md, from results/meta_judge/meta_verdicts.jsonl.

Static PNGs (markdown cannot host a hover layer), light surface baked in. Palette and rules
from the dataviz skill's reference instance: categorical slots 1-2 for judge/regex, the
sequential blue ramp (ordinal steps 250/450/650) for base -> step-60 -> step-final, hairline
solid gridlines, text in ink tokens never series colour, legend whenever >= 2 series, bars
capped thin with a surface gap. Both palettes were run through validate_palette.js and pass.
"""
from __future__ import annotations
import json, statistics as st
from collections import defaultdict
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

REPO = Path(__file__).resolve().parents[1]; OUT = REPO / "figures"; OUT.mkdir(exist_ok=True)
SURF, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
JUDGE, REGEX, REGEX10 = "#2a78d6", "#eb6834", "#1baf7a"  # categorical slots 1, 2, 3 (first three validate all-pairs)
CAP = json.load(open(REPO/"results/meta_judge/cap_analysis.json"))   # regex re-run on the judge's 10,000-char window
RAMP = {"base": "#86b6ef", "step-60": "#2a78d6", "step-final": "#104281"}  # ordinal 250/450/650
CK = ["base", "step-60", "step-final"]; CKL = {"base": "base", "step-60": "step-60\n(240 ex)", "step-final": "step-final\n(920 ex)"}
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": BASE, "axes.facecolor": SURF, "figure.facecolor": SURF,
    "savefig.facecolor": SURF, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False})

rows = [json.loads(l) for l in open(REPO/"results/meta_judge/meta_verdicts.jsonl") if l.strip()]
latest = {}
for r in rows: latest[(r["label"], r["suite"], r["sample_id"], r["mode"])] = r
rows = [r for r in latest.values() if r["llm_meta"] is not None]
by = defaultdict(list)
for r in rows: by[(r["label"], r["suite"])].append(r)
def rate(rs, k): return 100 * st.mean(r[k] for r in rs) if rs else None

def style(ax, ymax=100, ylabel="% of rollouts"):
    ax.set_axisbelow(True); ax.yaxis.grid(True, color=GRID, lw=1); ax.set_ylim(0, ymax)
    ax.spines["left"].set_visible(False); ax.spines["bottom"].set_color(BASE); ax.tick_params(length=0)
    ax.set_ylabel(ylabel, color=INK2)

# ---- Fig 1: judge vs regex, per checkpoint, two panels ------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=150, sharey=True)
for ax, suite, title in zip(axes, ("cotcontrol", "reasonif"), ("CoTControl (2,700/ckpt)", "ReasonIF (300/ckpt)")):
    cks = [c for c in CK if by.get((c, suite))]; x = range(len(cks)); w = 0.17
    series = ((-0.2, "llm_meta", JUDGE, "LLM judge (first 10,000 chars of trace)"),
              (0.0, "regex_10k", REGEX10, "METR regex, same 10,000-char window"),
              (0.2, "regex_meta", REGEX, "METR regex, full trace"))
    for off, key, col, lab in series:
        vals = [100 * CAP["summary"][f"{c}/{suite}"]["regex_10k"] if key == "regex_10k" else rate(by[(c, suite)], key) for c in cks]
        ax.bar([i + off for i in x], vals, width=w, color=col, label=lab, zorder=3)
        for i, v in zip(x, vals): ax.text(i + off, v + 1.5, f"{v:.0f}", ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xticks(list(x)); ax.set_xticklabels([CKL[c] for c in cks], color=INK2); ax.set_title(title, loc="left", color=INK, fontsize=11)
    style(ax, ylabel="meta-discussion, % of rollouts" if suite == "cotcontrol" else "")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, frameon=False, loc="upper left", bbox_to_anchor=(0.01, 0.93), ncol=3, fontsize=8.5, columnspacing=1.4)
fig.suptitle("Meta-discussion rate: on the same 10,000-char window the judge and the regex nearly agree", x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.86)); fig.savefig(OUT/"meta_judge_vs_regex.png"); plt.close(fig)

# ---- Fig 2: per-mode LLM-judge rate across checkpoints (connected dots) ---------------------
cc = {c: by[(c, "cotcontrol")] for c in CK}
modes = sorted({r["mode"] for r in cc["base"]}, key=lambda m: -rate([r for r in cc["base"] if r["mode"] == m], "llm_meta"))
fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=150)
ys = list(range(len(modes)))[::-1]
for y, m in zip(ys, modes):
    pts = [rate([r for r in cc[c] if r["mode"] == m], "llm_meta") for c in CK]
    ax.plot(pts, [y]*3, color=GRID, lw=2, zorder=2)
    for c, p in zip(CK, pts): ax.scatter(p, y, s=64, color=RAMP[c], edgecolor=SURF, linewidth=2, zorder=4)
ax.set_yticks(ys); ax.set_yticklabels(modes, color=INK2); ax.set_xlim(0, 100)
ax.xaxis.grid(True, color=GRID, lw=1); ax.set_axisbelow(True); ax.spines["left"].set_color(BASE); ax.spines["bottom"].set_color(BASE); ax.tick_params(length=0)
ax.set_xlabel("meta-discussion, % of rollouts (LLM judge)", color=INK2)
# direct-label only the extreme: largest base -> step-60 drop
drops = {m: rate([r for r in cc["base"] if r["mode"] == m], "llm_meta") - rate([r for r in cc["step-60"] if r["mode"] == m], "llm_meta") for m in modes}
mx = max(drops, key=drops.get); y = ys[modes.index(mx)]
b = rate([r for r in cc["base"] if r["mode"] == mx], "llm_meta"); s6 = rate([r for r in cc["step-60"] if r["mode"] == mx], "llm_meta")
ax.annotate(f"−{drops[mx]:.0f} pp", xy=((b+s6)/2, y), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9, color=INK2)
ax.legend(handles=[Line2D([0],[0], marker="o", ls="", ms=8, color=RAMP[c], markeredgecolor=SURF, label=CKL[c].replace("\n", " ")) for c in CK],
          frameon=False, loc="lower right", fontsize=9)
ax.set_title("Per mode: narration falls at step-60 in every mode, partly rebounds by step-final", loc="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(OUT/"meta_per_mode.png"); plt.close(fig)

# ---- Fig 3: the `constraint`-only population: what share does the judge call real? --------
fig, ax = plt.subplots(figsize=(5.2, 3.8), dpi=150)
share, pop = [], []
for c in CK:
    rs = [r for r in cc[c] if r["regex_patterns"] == ["constraint"]]
    share.append(100 * st.mean(r["llm_meta"] for r in rs)); pop.append(100 * len(rs) / len(cc[c]))
ax.bar(range(3), share, width=0.36, color=JUDGE, zorder=3)
for i, v in enumerate(share):
    ax.text(i, v + 1.5, f"{v:.0f}%", ha="center", va="bottom", fontsize=10, color=INK2)
ax.set_xticks(range(3))
ax.set_xticklabels([f"{CKL[c]}\n{p:.0f}% of rollouts" for c, p in zip(CK, pop)], color=INK2, fontsize=9)
style(ax, ymax=75, ylabel="judged genuine narration, %")
ax.set_title("Rollouts where only the bare `constraint` substring fires", loc="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(OUT/"meta_constraint_only.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig 4: disagreement is one-sided (step-60) --------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5.4), dpi=150)
pm = CAP["per_mode_step60"]
ri = [pm[m]["regex_only_in"] for m in modes]; rout = [pm[m]["regex_only_out"] for m in modes]; lo = [pm[m]["judge_only"] for m in modes]
h = 0.3
ax.barh([y + 0.17 for y in ys], ri, height=h, color=REGEX, label="regex fires, judge says no: match inside the judge's window", zorder=3)
ax.barh([y + 0.17 for y in ys], rout, left=[a + 1.2 for a in ri], height=h, color=BASE, label="regex fires, judge says no: match only beyond 10,000 chars (judge never saw it)", zorder=3)
ax.barh([y - 0.17 for y in ys], lo, height=h, color=JUDGE, label="judge fires, regex misses", zorder=3)
for y, a, b1, b2 in zip(ys, ri, rout, lo):
    ax.text(a + b1 + 3.5, y + 0.17, f"{a}+{b1}", va="center", fontsize=9, color=INK2); ax.text(b2 + 2, y - 0.17, str(b2), va="center", fontsize=9, color=INK2)
ax.set_yticks(ys); ax.set_yticklabels(modes, color=INK2); ax.xaxis.grid(True, color=GRID, lw=1); ax.set_axisbelow(True)
ax.spines["left"].set_color(BASE); ax.spines["bottom"].set_color(BASE); ax.tick_params(length=0); ax.set_xlim(0, 150)
ax.set_xlabel("rollouts (step-60, ~275 per mode)", color=INK2)
ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=1, fontsize=9)
ax.set_title("Most regex-only disagreements lie past the judge's 10,000-char window", loc="left", fontsize=11, color=INK, pad=58)
fig.tight_layout(); fig.savefig(OUT/"meta_disagreement.png"); plt.close(fig)

# ---- Fig 5: where narration first appears, per checkpoint, against the judge's 10k window -------
import re as _re
from cotctl.graders.cotcontrol import _META_PATTERNS as _PATS
fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)
for c in CK:
    text = {(r["sample_id"], r["mode"]): r.get("reasoning") or "" for r in map(json.loads, open(REPO/f"results/{c}/cotcontrol_rollouts.jsonl"))}
    pos = []
    for r in cc[c]:
        if not r["regex_meta"]: continue
        low = text[(r["sample_id"], r["mode"])].lower()
        pos.append(min(_re.search(p, low).start() for p in r["regex_patterns"]))
    pos.sort(); n = len(pos)
    ax.step(pos, [100 * (i + 1) / n for i in range(n)], where="post", color=RAMP[c], lw=2, label=f"{CKL[c].replace(chr(10), ' ')}  (median {pos[n//2]:,} chars)", zorder=3)
    beyond = 100 * sum(x >= 10000 for x in pos) / n
    ax.annotate(f"{beyond:.0f}% past the window", xy=(10000, 100 - beyond), xytext=(12, 0), textcoords="offset points", fontsize=9, color=INK2, va="center", bbox=dict(facecolor=SURF, edgecolor="none", pad=1.5), zorder=6)
ax.axvline(10000, color=BASE, lw=1, zorder=2); ax.text(10000, 2, " judge sees only the first 10,000 chars", fontsize=9, color=MUTED, va="bottom")
ax.set_xscale("log"); ax.set_xlim(50, 40000); ax.set_ylim(0, 100); ax.yaxis.grid(True, color=GRID, lw=1); ax.set_axisbelow(True)
ax.spines["left"].set_visible(False); ax.spines["bottom"].set_color(BASE); ax.tick_params(length=0)
ax.set_xlabel("character position of the first narration match (log scale)", color=INK2); ax.set_ylabel("% of narrating rollouts (cumulative)", color=INK2)
ax.legend(frameon=False, loc="upper left", fontsize=9)
ax.set_title("Fine-tuning moves narration later in the trace, past the judge's window", loc="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(OUT/"meta_first_hit_position.png"); plt.close(fig)
print("wrote", sorted(p.name for p in OUT.glob("meta_*.png")))
