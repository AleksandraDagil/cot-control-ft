#!/usr/bin/env python3
"""Render the LLM-judge meta-discussion results into META_DISCUSSION.md.

Reads results/meta_judge/meta_verdicts.jsonl (from scripts/judge_meta.py) and replaces the
PENDING section of META_DISCUSSION.md with per-checkpoint and per-mode tables comparing the
CoTControl paper's LLM judge against METR's regex, plus the disagreement analysis.

    python scripts/render_meta_report.py            # writes into META_DISCUSSION.md
    python scripts/render_meta_report.py --dry-run  # print only
"""

from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CKPTS = ["base", "step-60", "step-final"]
CKPT_LABEL = {"base": "base", "step-60": "step-60 (240 ex)", "step-final": "step-final (920 ex)"}


def load() -> list[dict]:
    p = REPO / "results" / "meta_judge" / "meta_verdicts.jsonl"
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    # keep the latest verdict per (label, suite, sample_id, mode) -- reruns append
    latest = {}
    for r in rows:
        latest[(r["label"], r["suite"], r["sample_id"], r["mode"])] = r
    return [r for r in latest.values() if r["llm_meta"] is not None]


def pct(x): return f"{100*x:.1f} %"


def wald80(k, n):
    if n == 0: return (0, 0)
    p = k / n; h = 1.2816 * (p * (1 - p) / n) ** 0.5
    return (max(0, p - h), min(1, p + h))


def render(rows: list[dict]) -> str:
    out = []
    by = defaultdict(list)
    for r in rows: by[(r["label"], r["suite"])].append(r)

    # --- 1. headline: LLM vs regex per checkpoint ---------------------------------
    out += ["## LLM judge results", "",
            f"Judge: `gpt-5-mini` via the OpenAI API, CoTControl paper prompt verbatim. "
            f"{len(rows):,} rollouts judged.", "",
            "### Meta-discussion rate: LLM judge vs regex", "",
            "| suite | checkpoint | n | **LLM judge** | regex | regex − LLM | agreement |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for suite in ("cotcontrol", "reasonif"):
        for c in CKPTS:
            rs = by.get((c, suite))
            if not rs: continue
            n = len(rs); l = sum(r["llm_meta"] for r in rs) / n; g = sum(r["regex_meta"] for r in rs) / n
            a = sum(r["llm_meta"] == r["regex_meta"] for r in rs) / n
            lo, hi = wald80(sum(r["llm_meta"] for r in rs), n)
            out.append(f"| {suite} | {CKPT_LABEL[c]} | {n} | **{pct(l)}** ({pct(lo)}–{pct(hi)}) | {pct(g)} | {100*(g-l):+.1f} pp | {pct(a)} |")
    out.append("")

    # --- 2. does the drop survive? ----------------------------------------------------
    cc = {c: by.get((c, "cotcontrol"), []) for c in CKPTS}
    if cc["base"] and cc["step-60"]:
        lb = st.mean(r["llm_meta"] for r in cc["base"]); l6 = st.mean(r["llm_meta"] for r in cc["step-60"])
        gb = st.mean(r["regex_meta"] for r in cc["base"]); g6 = st.mean(r["regex_meta"] for r in cc["step-60"])
        # paired bootstrap on the LLM drop, by question
        ib = {(r["sample_id"], r["mode"]): r["llm_meta"] for r in cc["base"]}
        i6 = {(r["sample_id"], r["mode"]): r["llm_meta"] for r in cc["step-60"]}
        ids = sorted(set(ib) & set(i6)); rng = random.Random(0); boot = []
        for _ in range(3000):
            pk = [ids[rng.randrange(len(ids))] for _ in ids]
            boot.append(st.mean(i6[i] for i in pk) - st.mean(ib[i] for i in pk))
        boot.sort(); lo, hi = boot[int(.1*len(boot))], boot[int(.9*len(boot))]
        out += ["### Does the base → step-60 drop survive the LLM judge?", "",
                f"| | base | step-60 | Δ |", "|---|---:|---:|---:|",
                f"| regex | {pct(gb)} | {pct(g6)} | {100*(g6-gb):+.1f} pp |",
                f"| **LLM judge** | **{pct(lb)}** | **{pct(l6)}** | **{100*(l6-lb):+.1f} pp** (80 % CI {100*lo:+.1f} to {100*hi:+.1f}, paired, n={len(ids)}) |", ""]
        if cc["step-final"]:
            lf = st.mean(r["llm_meta"] for r in cc["step-final"])
            out.append(f"step-final: LLM {pct(lf)} — {'rebounds' if lf > l6 else 'keeps falling'} after step-60 "
                       f"(regex showed a rebound to {pct(st.mean(r['regex_meta'] for r in cc['step-final']))}).")
            out.append("")

    # --- 3. per-mode ---------------------------------------------------------------------
    out += ["### Per mode (CoTControl)", "",
            "| mode | ckpt | n | LLM | regex | agree | regex-only | LLM-only |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    modes = sorted({r["mode"] for c in CKPTS for r in cc[c]})
    for m in modes:
        for c in CKPTS:
            rs = [r for r in cc[c] if r["mode"] == m]
            if not rs: continue
            n = len(rs)
            out.append(f"| {m} | {c} | {n} | {pct(st.mean(r['llm_meta'] for r in rs))} | {pct(st.mean(r['regex_meta'] for r in rs))} | "
                       f"{pct(st.mean(r['llm_meta']==r['regex_meta'] for r in rs))} | "
                       f"{sum(r['regex_meta'] and not r['llm_meta'] for r in rs)} | {sum(r['llm_meta'] and not r['regex_meta'] for r in rs)} |")
    out.append("")
    out += ["`regex-only` = regex fires, judge says no narration (the suspected `constraint` false positives). "
            "`LLM-only` = judge sees narration the seven patterns miss.", ""]

    # --- 4. the constraint-only population --------------------------------------------------
    out += ["### The `constraint`-only rollouts: what does the judge say?", ""]
    for c in CKPTS:
        rs = [r for r in cc[c] if r["regex_patterns"] == ["constraint"]]
        if not rs: continue
        k = sum(r["llm_meta"] for r in rs)
        out.append(f"- {CKPT_LABEL[c]}: {len(rs)} rollouts where only `constraint` fires → judge calls **{pct(k/len(rs))}** of them meta-discussion.")
    out += ["", "If that share is low, the regex's headline rate is inflated by roughly that population "
            "(~26–29 % of all rollouts, flat across checkpoints); if high, the bare substring is a fair proxy after all.", ""]

    # --- 5. examples ---------------------------------------------------------------------------
    out += ["### Example judge-only detections (narration the regex misses)", ""]
    ex = [r for c in CKPTS for r in cc[c] if r["llm_meta"] and not r["regex_meta"] and r["llm_violations"]]
    for r in ex[:4]:
        v = r["llm_violations"].splitlines()[0][:220]
        out.append(f"- *{r['label']} / {r['mode']}*: {v}")
    if not ex: out.append("(none)")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
    rows = load()
    body = render(rows)
    if a.dry_run:
        print(body); return 0
    p = REPO / "META_DISCUSSION.md"; s = p.read_text(encoding="utf-8")
    start = s.index("## LLM judge (CoTControl paper's prompt, gpt-5-mini) — PENDING")
    end = s.index("## How to reduce it further")
    s = s[:start] + body + "\n" + s[end:]
    have = sorted({r["label"] for r in rows}); missing = [c for c in CKPTS if c not in have]
    status = (f"**Status: complete.** {len(rows):,} rollouts judged with the CoTControl paper's LLM judge."
              if not missing else
              f"**Status: partial.** {len(rows):,} rollouts judged ({', '.join(have)} complete); "
              f"{', '.join(missing)} pending — both the OpenRouter and the OpenAI key ran out of credit "
              f"mid-run. `python scripts/judge_meta.py` resumes from cache once either is topped up.")
    import re as _re
    s = _re.sub(r"\*\*Status:.*?\n\n", status + "\n\n", s, count=1, flags=_re.S)
    p.write_text(s, encoding="utf-8"); print(f"wrote META_DISCUSSION.md ({len(rows)} verdicts)"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
