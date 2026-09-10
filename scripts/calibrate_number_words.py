#!/usr/bin/env python3
"""Calibrate the per-source `number_words` budget for this model.

ReasonIF's word limit is model-specific: upstream ships `number_of_words_reference.json` with,
per model and per source, the **20th percentile** of that model's *unconstrained* reasoning
length. A budget calibrated on another model would make the instruction either trivial or
impossible, so METR calibrated their own and so do we.

    scripts/serve_vllm.sh &                       # in another shell
    python scripts/calibrate_number_words.py

Writes `data/word_limits_<model>.json` (used via `--word-limits` in run_baseline.py) and appends
the same numbers into a copy of the upstream reference file for easy side-by-side reading.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

from cotctl.datasets import load_reasonif  # noqa: E402
from cotctl.eval import reasonif_calibration_requests  # noqa: E402
from cotctl.inference import RolloutStore, SamplingParams, VLLMClient, run_sync, wait_for_server  # noqa: E402

log = logging.getLogger("calibrate")


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolation percentile (numpy's default), without importing numpy."""
    if not values:
        return 0.0
    vs = sorted(values)
    if len(vs) == 1:
        return vs[0]
    pos = (pct / 100.0) * (len(vs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(vs) - 1)
    return vs[lo] + (vs[hi] - vs[lo]) * (pos - lo)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(REPO / "configs" / "calibration.yaml"))
    ap.add_argument("--out-dir", default=str(REPO / "results" / "calibration"))
    ap.add_argument("--model", default=None, help="override the served model id (e.g. 'ft')")
    ap.add_argument("--limit", type=int, default=None, help="debug: only the first N questions")
    ap.add_argument("--repeats", type=int, default=None)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    import yaml

    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
    model_name = args.model or cfg["model"]["served_name"]
    repeats = args.repeats if args.repeats is not None else int(cfg["calibration"].get("repeats", 1))
    pct = float(cfg["calibration"].get("percentile", 20))
    drop_truncated = bool(cfg["calibration"].get("drop_truncated", False))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    served = wait_for_server(cfg["server"]["base_url"])
    log.info("server ready, serving %s (requesting %s)", served, model_name)

    samples = load_reasonif()
    if args.limit:
        samples = samples[: args.limit]
    requests = reasonif_calibration_requests(samples)
    if repeats > 1:  # distinct mode strings keep the store keys unique
        requests = [
            type(r)(sample_id=r.sample_id, mode=f"calibration_{i}", prompt=r.prompt, meta=r.meta)
            for i in range(repeats)
            for r in requests
        ]

    sampling = SamplingParams(**{k: v for k, v in cfg["sampling"].items()})
    client = VLLMClient(model_name, cfg["server"]["base_url"], concurrency=cfg["server"]["concurrency"])

    store = RolloutStore(out_dir / "calibration_rollouts.jsonl")
    with store:
        run_sync(client, requests, sampling, store, desc="calibration")

    # --- aggregate -------------------------------------------------------
    per_source: dict[str, list[int]] = {}
    per_source_truncated: dict[str, int] = {}
    n_trunc = n_bad = 0
    for r in store.read_all():
        if r.get("error"):
            continue
        if r.get("think_status") != "ok":
            n_bad += 1
            continue
        if r.get("truncated"):
            n_trunc += 1
            if drop_truncated:
                continue
        source = (r.get("meta") or {}).get("source")
        if source:
            per_source.setdefault(source, []).append(len(re.findall(r"\w+", r.get("reasoning") or "")))
            if r.get("truncated"):
                per_source_truncated[source] = per_source_truncated.get(source, 0) + 1

    # Truncated rollouts are right-censored at max_tokens: we know the reasoning was at least
    # this long, not how long it would have been. Dropping them removes the top tail, so the
    # p-th percentile of what remains is really the (p * retained_fraction)-th percentile of the
    # true distribution -- a systematically *tighter* word limit than intended. Because the
    # target percentile here is low (20th) and every censored rollout sits far above it, keeping
    # them at their censored length gives the correct p20: only their count matters, not their
    # exact values. So drop_truncated defaults to false.
    limits = {src: int(percentile(vals, pct)) for src, vals in sorted(per_source.items())}
    for src, vals in sorted(per_source.items()):
        censored = per_source_truncated.get(src, 0)
        # p20 is only identifiable while the uncensored share (100 - censored%) exceeds 20.
        if vals and 100 * censored / len(vals) >= (100 - pct):
            log.warning(
                "%s: %.0f%% of rollouts are censored, which reaches the p%g target -- the limit "
                "for this source is a lower bound, not a percentile",
                src, 100 * censored / len(vals), pct,
            )
    stats = {
        src: {
            "n": len(vals),
            "p20": int(percentile(vals, 20)),
            "median": int(percentile(vals, 50)),
            "p80": int(percentile(vals, 80)),
            "mean": round(sum(vals) / len(vals), 1),
            "max": max(vals),
            "n_truncated": per_source_truncated.get(src, 0),
            "pct_truncated": round(100 * per_source_truncated.get(src, 0) / len(vals), 1),
        }
        for src, vals in sorted(per_source.items())
    }

    short = model_name.split("/")[-1]
    out_json = REPO / "data" / f"word_limits_{short}.json"
    out_json.write_text(json.dumps({short: limits}, indent=2) + "\n", encoding="utf-8")
    (out_dir / "calibration_stats.json").write_text(
        json.dumps(
            {
                "model": model_name,
                "percentile": pct,
                "drop_truncated": drop_truncated,
                "n_truncated": n_trunc,
                "truncated_dropped": drop_truncated,
                "n_unusable_think": n_bad,
                "limits": limits,
                "per_source": stats,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"\nnumber_words limits (p{pct:g} of unconstrained reasoning length) for {model_name}:")
    print(f"{'source':<10}{'n':>6}{'p20':>8}{'median':>9}{'p80':>8}{'max':>8}")
    for src, s in stats.items():
        print(f"{src:<10}{s['n']:>6}{s['p20']:>8}{s['median']:>9}{s['p80']:>8}{s['max']:>8}")
    verb = "dropped" if drop_truncated else "kept (right-censored)"
    print(f"\ntruncated: {n_trunc} {verb}; {n_bad} unusable think block")
    print(f"wrote {out_json.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
