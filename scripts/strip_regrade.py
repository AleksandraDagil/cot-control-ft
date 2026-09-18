#!/usr/bin/env python3
"""Ceiling test for meta-discussion suppression: strip narration from stored CoTControl rollouts
and re-grade. Measures "compliance if the narration text were deleted and nothing else changed" --
an upper bound on what any narration-suppression method could buy via the direct route.

Variants (the detector is independent of the grader, never the grader itself):
  preamble  leading paragraphs while they contain a narration match (the user's original idea)
  strong    every sentence matching one of the six specific METR patterns (bare `constraint` excluded)
  all7      every sentence matching any of the seven METR patterns (removes any sentence with `constraint`)
  judge     the gpt-5-mini judge's quoted spans (first 10,000 chars only; where the judge said yes)

    python scripts/strip_regrade.py --labels base step-60
"""
from __future__ import annotations
import argparse, json, re, statistics as st, sys
from collections import defaultdict
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO / "src"))
from cotctl.graders.cotcontrol import _META_PATTERNS, grade_cotcontrol  # noqa: E402
from cotctl.graders.continuous import count_keyword_uses  # noqa: E402
from cotctl.graders.continuous_v2 import score_v2  # noqa: E402

STRONG = [re.compile(p) for p in _META_PATTERNS if p != "constraint"]
ALL7 = [re.compile(p) for p in _META_PATTERNS]
SUPP = {"word_suppression", "multiple_word_suppression"}
MODES = ["uppercase_thinking", "lowercase_thinking", "alternating_case", "word_suppression",
         "multiple_word_suppression", "repeat_sentences", "end_of_sentence", "meow_between_words", "ignore_question"]
SENT = re.compile(r"(?<=[.!?])\s+|\n+")

def load(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []

def split_keep(text: str) -> list[str]:
    """Sentences with their trailing separators, so ''.join(parts) == text."""
    out, pos = [], 0
    for m in SENT.finditer(text):
        out.append(text[pos:m.end()]); pos = m.end()
    if pos < len(text): out.append(text[pos:])
    return out

def hit(s: str, pats) -> bool:
    low = s.lower(); return any(p.search(low) for p in pats)

def strip_sentences(text: str, pats) -> str:
    return "".join(s for s in split_keep(text) if not hit(s, pats))

def strip_preamble(text: str) -> str:
    paras = re.split(r"(\n\s*\n)", text); i = 0
    while i < len(paras) and (paras[i].strip() == "" or hit(paras[i], ALL7)):
        i += 1
    return "".join(paras[i:])

def parse_spans(blob) -> list[str]:
    """Judge returns a bullet list of quoted excerpts as one string; pull out the quoted text."""
    if not blob: return []
    if isinstance(blob, list): blob = "\n".join(map(str, blob))
    spans = re.findall(r'"(.+?)"\s*$', blob, flags=re.M) or [ln.strip("-* \"") for ln in blob.splitlines()]
    return [x.strip().lower() for x in spans if len(x.strip()) >= 12]

def strip_spans(text: str, blob) -> str:
    spans = parse_spans(blob)
    if not spans: return text
    keep = []
    for s in split_keep(text):
        low = s.lower().strip()
        # a sentence goes if it contains a quoted excerpt, or (long sentences only) is itself contained in one;
        # short sentences never match by reverse containment, else quoted *constraint text* like
        # "<This reasoning is not suspicious.>" would delete the very sentence repeat_sentences requires
        if low and any(v in low or (len(low) >= 60 and low in v) for v in spans): continue
        keep.append(s)
    return "".join(keep)

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--labels", nargs="+", default=["base", "step-60"]); a = ap.parse_args()
    verd = {}
    for v in load(REPO / "results/meta_judge/meta_verdicts.jsonl"):
        if v["suite"] == "cotcontrol": verd[(v["label"], v["sample_id"], v["mode"])] = v
    result = {}
    for label in a.labels:
        rows = [r for r in load(REPO / f"results/{label}/cotcontrol_rollouts.jsonl") if not r.get("error") and r.get("think_status") == "ok"]
        kw = {r["sample_id"]: r["meta"].get("keywords") or [] for r in rows if r["mode"] in SUPP}
        unc = {r["sample_id"]: count_keyword_uses(r.get("reasoning") or "", kw[r["sample_id"]])
               for r in load(REPO / f"results/{label}/unconstrained_rollouts.jsonl") if r["sample_id"] in kw and r.get("think_status") == "ok"}
        per = defaultdict(lambda: defaultdict(list))   # per[mode][metric] -> list
        for r in rows:
            m, t = r["mode"], r.get("reasoning") or ""
            if not t: continue
            v = verd.get((label, r["sample_id"], m))
            variants = {"original": t, "preamble": strip_preamble(t), "strong": strip_sentences(t, STRONG),
                        "all7": strip_sentences(t, ALL7),
                        "judge": strip_spans(t, v["llm_violations"]) if v and v.get("llm_meta") else t}
            kws = r["meta"].get("keywords") or []
            for name, txt in variants.items():
                b = grade_cotcontrol(m, txt, keywords=kws)
                c = score_v2(m, txt, keywords=kws, unconstrained_uses=unc.get(r["sample_id"]))
                if b is not None: per[m][f"bin_{name}"].append(int(b))
                if c is not None: per[m][f"cont_{name}"].append(c)
                per[m][f"removed_{name}"].append(1 - len(txt) / len(t))
            per[m]["regex_flagged"].append(int(hit(t, ALL7)))
            per[m]["judge_flagged"].append(int(bool(v and v.get("llm_meta"))))
            # ceiling among rollouts that actually narrate (strong detector): does stripping flip them?
            if hit(t, STRONG):
                b0, b1 = grade_cotcontrol(m, t, keywords=kws), grade_cotcontrol(m, variants["strong"], keywords=kws)
                if b0 is not None: per[m]["flip_strong"].append(int((not b0) and b1))
        result[label] = {m: {k: (st.mean(vals) if vals else None, len(vals)) for k, vals in d.items()} for m, d in per.items()}
    (REPO / "results/strip_test").mkdir(exist_ok=True)
    (REPO / "results/strip_test/strip_regrade.json").write_text(json.dumps(result, indent=1))
    for label in a.labels:
        R = result[label]
        print(f"\n=== {label}: binary compliance % (original -> stripped) | continuous score (original -> stripped) | % chars removed ===")
        print(f"{'mode':<27}{'bin orig':>9}{'preamb':>7}{'strong':>7}{'all7':>6}{'judge':>6} | {'cont orig':>9}{'preamb':>7}{'strong':>7}{'all7':>6}{'judge':>6} | {'rm pre':>7}{'rm str':>7}{'rm all7':>8}{'rm jdg':>7} | {'narr%':>6}{'flip%':>6}")
        for m in MODES:
            d = R.get(m); 
            if not d: continue
            g = lambda k, f=lambda x: f"{100*x:5.1f}": (f(d[k][0]) if d.get(k) and d[k][0] is not None else "    —")
            c = lambda k: (f"{d[k][0]:6.3f}" if d.get(k) and d[k][0] is not None else "     —")
            print(f"{m:<27}{g('bin_original'):>9}{g('bin_preamble'):>7}{g('bin_strong'):>7}{g('bin_all7'):>6}{g('bin_judge'):>6} | "
                  f"{c('cont_original'):>9}{c('cont_preamble'):>7}{c('cont_strong'):>7}{c('cont_all7'):>6}{c('cont_judge'):>6} | "
                  f"{g('removed_preamble'):>7}{g('removed_strong'):>7}{g('removed_all7'):>8}{g('removed_judge'):>7} | {g('regex_flagged'):>6}{g('flip_strong'):>6}")
    print("\nnarr% = share of rollouts with any regex match; flip% = among rollouts with a strong-pattern match, share that go fail -> pass when those sentences are removed.")
    print("ignore_question: binary/continuous need the LLM judge, not re-run here.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
