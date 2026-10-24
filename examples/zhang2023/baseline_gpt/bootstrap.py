#!/usr/bin/env python3
"""Paired bootstrap over the labeled evaluation threads (1,000 resamples, seed 20260930): the share of resamples
in which TACT's final-coding F1 exceeds the single-model baseline's (182 reference labels).
  python3 examples/zhang2023/baseline_gpt/bootstrap.py   -> baseline_gpt/bootstrap.json"""
import json, sys, random
from pathlib import Path
from collections import defaultdict
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scoring"))
from paths import MAP, CODEBOOK, read_json, load_mapping, evaluation_threads, reference_labels  # noqa: E402
from coding_scores import score, consensus_pairs  # noqa: E402

tmp = load_mapping(MAP["approved"])
trq = {c["id"]: c["rq"] for c in read_json(CODEBOOK["approved"])["codes"]}
bo = read_json(HERE / "output.json"); brq = {c["id"]: c["rq"] for c in bo["codebook"]}
bmp = load_mapping(HERE / "mapping_baseline.json")
evs = evaluation_threads(); lab = reference_labels(evs); cov = set().union(*tmp.values())
L = {u: {x for x in cs if x in cov} for u, cs in lab.items()}; L = {u: cs for u, cs in L.items() if cs}
def by(p):
    d = defaultdict(list)
    for u, c in p: d[u].append(c)
    return d
B = by([(a["uid"], c) for a in bo["assignments"] if a["uid"] in evs for c in a.get("codes", []) if c in brq])
units = sorted(u for u in evs if L.get(u)); out = {}
for cond in ("L", "LJA"):
    rng = random.Random(20260930); T = by(consensus_pairs(cond, evs)); diffs = []
    for _ in range(1000):
        samp = [rng.choice(units) for _ in units]; l2, t2, b2 = {}, [], []
        for i, u in enumerate(samp):
            k = f"{u}#{i}"; l2[k] = L[u]; t2 += [(k, c) for c in T.get(u, [])]; b2 += [(k, c) for c in B.get(u, [])]
        diffs.append(score(t2, tmp, trq, l2, set(l2))["f1"] - score(b2, bmp, brq, l2, set(l2))["f1"])
    diffs.sort()
    out[cond] = {"share_tact_higher": sum(d > 0 for d in diffs) / 1000, "ci95": [round(diffs[25], 3), round(diffs[974], 3)]}
(HERE / "bootstrap.json").write_text(json.dumps(out, indent=1)); print(out)
