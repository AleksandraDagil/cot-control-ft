#!/usr/bin/env python3
"""Strip-and-regrade with LLM-labelled narration over the FULL trace, all nine CoTControl modes.

Stage A  one gpt-5-mini call per rollout (no character cap) listing every narration sentence verbatim
Stage B  delete sentence units matching (a) the LLM list, (b) METR's seven regexes, (c) their union
Stage C  re-grade: binary (METR graders) + continuous v2, 8 modes locally; ignore_question via the
         judge on the ORIGINAL and the UNION-stripped trace (binary triple-check + count prompt)

    python scripts/strip_llm.py --labels base step-60 [--limit N] [--concurrency 16]
Single event loop, one LLMJudge, everything cached in results/strip_llm/judge_cache.jsonl.
"""
from __future__ import annotations
import argparse, asyncio, json, os, re, statistics as st, sys, time
from collections import defaultdict
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO / "src"))
from dotenv import load_dotenv; load_dotenv(REPO / ".env", override=True)
import importlib.util
spec = importlib.util.spec_from_file_location("sr", REPO / "scripts/strip_regrade.py"); sr = importlib.util.module_from_spec(spec); spec.loader.exec_module(sr)
from cotctl.graders.cotcontrol import grade_cotcontrol, detect_meta_discussion
from cotctl.graders.continuous import count_keyword_uses
from cotctl.graders.continuous_v2 import score_v2, score_ignore_question
from cotctl.judge import LLMJudge
OUT = REPO / "results/strip_llm"; OUT.mkdir(parents=True, exist_ok=True)
MODES = sr.MODES

def norm(s: str) -> str: return re.sub(r"\s+", " ", s).strip().lower()

def strip_llm_units(text: str, sents: list[str]) -> tuple[str, int]:
    """Delete units that contain an LLM-listed sentence, or (>= 60 chars) are contained in one."""
    ns = [norm(x) for x in sents if len(norm(x)) >= 12]
    if not ns: return text, 0
    keep, removed = [], 0
    for u in sr.split_keep(text):
        nu = norm(u)
        if nu and any(v in nu or (len(nu) >= 60 and nu in v) for v in ns): removed += 1; continue
        keep.append(u)
    return "".join(keep), removed

def strip_union(text: str, sents: list[str]) -> str:
    ns = [norm(x) for x in sents if len(norm(x)) >= 12]
    keep = []
    for u in sr.split_keep(text):
        nu = norm(u)
        if sr.hit(u, sr.ALL7): continue
        if nu and any(v in nu or (len(nu) >= 60 and nu in v) for v in ns): continue
        keep.append(u)
    return "".join(keep)

def load(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else []

async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", nargs="+", default=["base", "step-60"])
    ap.add_argument("--limit", type=int, default=None, help="debug: rollouts per label")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--model", default=os.environ.get("JUDGE_MODEL", "gpt-5-mini"))
    a = ap.parse_args()
    judge = LLMJudge(model=a.model, cache_path=OUT / "judge_cache.jsonl", concurrency=a.concurrency)
    print(f"judge {a.model} @ {judge.base_url}", flush=True)
    summary = {}
    for label in a.labels:
        t0 = time.time()
        rows = [r for r in load(REPO / f"results/{label}/cotcontrol_rollouts.jsonl") if not r.get("error") and r.get("think_status") == "ok" and r.get("reasoning")]
        if a.limit: rows = rows[: a.limit]
        kw = {r["sample_id"]: r["meta"].get("keywords") or [] for r in rows if r["mode"] in sr.SUPP}
        unc = {r["sample_id"]: count_keyword_uses(r.get("reasoning") or "", kw[r["sample_id"]])
               for r in load(REPO / f"results/{label}/unconstrained_rollouts.jsonl") if r["sample_id"] in kw and r.get("think_status") == "ok"}
        graded = {(g["sample_id"], g["mode"]): g for g in load(REPO / f"results/{label}/graded_{label}_cotcontrol.jsonl")}
        # ---- Stage A: narration lists on the full trace
        print(f"[{label}] stage A: narration lists for {len(rows)} rollouts", flush=True)
        verd = await judge.judge_many("narration_full", [(r["prompt"], r["reasoning"]) for r in rows], desc=f"{label} narration")
        with open(OUT / f"narration_{label}.jsonl", "w", encoding="utf-8") as f:
            for r, v in zip(rows, verd):
                f.write(json.dumps({"sample_id": r["sample_id"], "mode": r["mode"], "has_narration": v.compliant,
                                    "sentences": json.loads(v.detail) if v.detail else [], "error": v.error}, ensure_ascii=False) + "\n")
        errs = sum(v.error is not None for v in verd); print(f"[{label}] stage A done: {errs} errors, {time.time()-t0:.0f}s", flush=True)
        # ---- Stage B+C
        per = defaultdict(lambda: defaultdict(list)); iq_items_union, iq_items_orig, iq_rows = [], [], []
        for r, v in zip(rows, verd):
            m, t, kws = r["mode"], r["reasoning"], r["meta"].get("keywords") or []
            sents = json.loads(v.detail) if v.detail else []
            llm_txt, n_llm_units = strip_llm_units(t, sents)
            variants = {"original": t, "llm": llm_txt, "regex": sr.strip_sentences(t, sr.ALL7), "union": strip_union(t, sents)}
            per[m]["llm_has_narration"].append(int(bool(v.compliant))); per[m]["llm_n_sentences"].append(len(sents))
            per[m]["llm_units_matched"].append(n_llm_units); per[m]["llm_error"].append(int(v.error is not None))
            per[m]["regex_has_narration"].append(int(detect_meta_discussion(t)))
            for name, txt in variants.items():
                per[m][f"removed_{name}"].append(1 - len(txt) / len(t))
                if m == "ignore_question": continue
                b = grade_cotcontrol(m, txt, keywords=kws); c = score_v2(m, txt, keywords=kws, unconstrained_uses=unc.get(r["sample_id"]))
                if b is not None: per[m][f"bin_{name}"].append(int(b))
                if c is not None: per[m][f"cont_{name}"].append(c)
            if m != "ignore_question":
                b0, b1 = grade_cotcontrol(m, t, keywords=kws), grade_cotcontrol(m, variants["union"], keywords=kws)
                per[m]["flip_fail_to_pass"].append(int((not b0) and b1)); per[m]["flip_pass_to_fail"].append(int(b0 and not b1))
            else:
                iq_rows.append((r, variants["union"])); iq_items_union.append((r["prompt"], variants["union"])); iq_items_orig.append((r["prompt"], t))
        # ---- ignore_question via judge
        if iq_rows:
            print(f"[{label}] ignore_question: {len(iq_rows)} rollouts -> binary(union) + count(original, union)", flush=True)
            b_union = await judge.judge_many("ignore_question", iq_items_union, desc=f"{label} iq binary union")
            c_orig = await judge.judge_many("ignore_count", iq_items_orig, desc=f"{label} iq count orig")
            c_union = await judge.judge_many("ignore_count", iq_items_union, desc=f"{label} iq count union")
            with open(OUT / f"ignore_question_{label}.jsonl", "w", encoding="utf-8") as f:
                for (r, _), bu, co, cu in zip(iq_rows, b_union, c_orig, c_union):
                    g = graded.get((r["sample_id"], "ignore_question")); b0 = None if g is None else g["compliant"]
                    rec = {"sample_id": r["sample_id"], "bin_original": b0, "bin_union": bu.compliant, "bin_union_error": bu.error,
                           "count_original": json.loads(co.detail) if co.detail else None, "count_original_error": co.error,
                           "count_union": json.loads(cu.detail) if cu.detail else None, "count_union_error": cu.error}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    m = "ignore_question"
                    if b0 is not None: per[m]["bin_original"].append(int(b0))
                    if bu.compliant is not None: per[m]["bin_union"].append(int(bu.compliant))
                    if b0 is not None and bu.compliant is not None:
                        per[m]["flip_fail_to_pass"].append(int((not b0) and bu.compliant)); per[m]["flip_pass_to_fail"].append(int(b0 and not bu.compliant))
                    for name, cv in (("original", co), ("union", cu)):
                        if cv.detail:
                            d = json.loads(cv.detail); sc = score_ignore_question(d["violating"], d["total"])
                            if sc is not None: per[m][f"cont_{name}"].append(sc)
                    per[m]["iq_errors"].append(int(bool(bu.error or co.error or cu.error)))
        summary[label] = {m: {k: {"mean": st.mean(v), "n": len(v)} for k, v in d.items() if v} for m, d in per.items()}
        print(f"[{label}] done in {time.time()-t0:.0f}s", flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    for label in a.labels:
        S = summary[label]
        print(f"\n=== {label}: binary % / continuous, original -> stripped (llm | regex | union) ===")
        print(f"{'mode':<27}{'n':>5}{'llm%':>6}{'rgx%':>6} | {'bin o':>6}{'llm':>6}{'rgx':>6}{'union':>6} | {'cont o':>7}{'llm':>7}{'rgx':>7}{'union':>7} | {'rm llm':>7}{'rm rgx':>7}{'rm un':>7} | {'f->p':>5}{'p->f':>5}")
        for m in MODES:
            d = S.get(m)
            if not d: continue
            g = lambda k, f=lambda x: f"{100*x:5.1f}": (f(d[k]["mean"]) if k in d else "    —")
            c = lambda k: (f"{d[k]['mean']:6.3f}" if k in d else "     —")
            print(f"{m:<27}{d['removed_original']['n']:>5}{g('llm_has_narration'):>6}{g('regex_has_narration'):>6} | {g('bin_original'):>6}{g('bin_llm'):>6}{g('bin_regex'):>6}{g('bin_union'):>6} | "
                  f"{c('cont_original'):>7}{c('cont_llm'):>7}{c('cont_regex'):>7}{c('cont_union'):>7} | {g('removed_llm'):>7}{g('removed_regex'):>7}{g('removed_union'):>7} | "
                  f"{(str(int(round(d['flip_fail_to_pass']['mean']*d['flip_fail_to_pass']['n']))) if 'flip_fail_to_pass' in d else '—'):>5}{(str(int(round(d['flip_pass_to_fail']['mean']*d['flip_pass_to_fail']['n']))) if 'flip_pass_to_fail' in d else '—'):>5}")
    print("\nwrote results/strip_llm/summary.json")
    return 0

if __name__ == "__main__": raise SystemExit(asyncio.run(main()))
