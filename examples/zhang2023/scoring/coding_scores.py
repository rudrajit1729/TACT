#!/usr/bin/env python3
"""
Score the TACT-Lite (L) and TACT-Full (LJA) coding with the final codebook against Zhang et al.'s reference
labels on the 192 evaluation threads, counting a code only where it reached consensus. It reports recall,
precision and F1 with 95% bootstrap intervals, the same by research question, per-code alpha among the AI
coders, and the share of TACT-Lite consensus assignments that TACT-Full's screening showed the AI coders.

  python3 examples/zhang2023/scoring/coding_scores.py

Reads results/<cond>/consensus.csv, results/<cond>_eval/summary.json, results/screening/screening_plan.json,
codebooks/approved_codebook.json, mapping/mapping_approved.json, data/splits.json and
labels/reference_labels.csv. Writes results/coding_scores.json and prints a table.
"""
from __future__ import annotations
import csv, json, random, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DIM, CODEBOOK, MAP, RESULTS, read_json, load_mapping, evaluation_threads, reference_labels  # noqa: E402

COND = {"L": "TACT-Lite", "LJA": "TACT-Full"}


def consensus_pairs(cond, ev):
    with (RESULTS / cond / "consensus.csv").open(newline="", encoding="utf-8") as fh:
        return [(r["uid"], r["code"]) for r in csv.DictReader(fh) if r["uid"] in ev and r["code"].startswith("T")]


def score(pairs, mp, rq, lab, units):
    labels = {(u, c) for u in units for c in lab.get(u, ())}
    reached = {(u, cat) for u, cid in pairs if u in units for cat in mp.get(cid, ())}
    hit = len(labels & reached)
    sq = [(u, cid) for u, cid in pairs if u in units and mp.get(cid) and lab.get(u)
          and any(x[:2] == DIM.get(rq.get(cid)) for x in lab[u])]
    agq = sum(1 for u, cid in sq if mp[cid] & lab[u])
    R = hit / len(labels) if labels else 0
    P = agq / len(sq) if sq else 0
    return {"recall": R, "precision": P, "f1": 2 * R * P / (R + P) if R + P else 0,
            "matched": "%d/%d" % (hit, len(labels)), "agreeing": "%d/%d" % (agq, len(sq))}


def boot(pairs, mp, rq, lab, ev, n=1000):
    units = sorted(u for u in ev if lab.get(u))
    rng = random.Random(20260930)
    by_u = defaultdict(list)
    for u, c in pairs:
        by_u[u].append(c)
    vals = {k: [] for k in ("recall", "precision", "f1")}
    for _ in range(n):
        lab2, pairs2 = {}, []
        for i, u in enumerate(rng.choice(units) for _ in units):
            key = "%s#%d" % (u, i)          # a thread drawn twice counts twice
            lab2[key] = lab[u]
            pairs2 += [(key, c) for c in by_u.get(u, [])]
        s = score(pairs2, mp, rq, lab2, set(lab2))
        for k in vals:
            vals[k].append(s[k])
    return {k: [round(sorted(v)[25], 3), round(sorted(v)[974], 3)] for k, v in vals.items()}


def main():
    ev = evaluation_threads()
    mp = load_mapping(MAP["approved"])
    rq = {c["id"]: c.get("rq", "") for c in read_json(CODEBOOK["approved"])["codes"]}
    lab183 = reference_labels(ev)
    covered = set().union(*mp.values())
    lab182 = {u: {x for x in cs if x in covered} for u, cs in lab183.items()}
    lab182 = {u: cs for u, cs in lab182.items() if cs}
    out = {"mapping": MAP["approved"].name, "conditions": {}}
    print("%-10s %-11s %7s %7s %6s  %-8s %-8s %s" % ("condition", "labels", "recall", "prec", "F1", "matched", "agreeing", "95% interval (recall; F1)"))
    for cond, name in COND.items():
        pairs = consensus_pairs(cond, ev)
        res = {}
        for lname, lab in (("covered", lab182), ("all", lab183)):
            s = score(pairs, mp, rq, lab, ev)
            s["ci95"] = boot(pairs, mp, rq, lab, ev)
            res[lname] = s
            print("%-10s %-11s %7.3f %7.3f %6.3f  %-8s %-8s %.2f-%.2f; %.2f-%.2f" % (
                name, "%s (%s)" % (lname, s["matched"].split("/")[1]), s["recall"], s["precision"], s["f1"],
                s["matched"], s["agreeing"], s["ci95"]["recall"][0], s["ci95"]["recall"][1], s["ci95"]["f1"][0], s["ci95"]["f1"][1]))
        res["per_rq"] = {}
        for q, dim in DIM.items():
            lq = {u: {x for x in cs if x.startswith(dim)} for u, cs in lab182.items()}
            lq = {u: cs for u, cs in lq.items() if cs}
            s = score([(u, c) for u, c in pairs if rq.get(c) == q], mp, rq, lq, ev)
            res["per_rq"][q] = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}
            print("%-10s   %-9s %7.3f %7.3f %6.3f  %-8s %s" % ("", q, s["recall"], s["precision"], s["f1"], s["matched"], s["agreeing"]))
        sm = read_json(RESULTS / ("%s_eval" % cond) / "summary.json")
        res["alpha"] = {k: sm.get(k) for k in ("alpha_median", "alpha_min", "alpha_max", "n_codes")}
        out["conditions"][cond] = res
    shown = read_json(RESULTS / "screening" / "screening_plan.json")["shown"]
    lp = set(consensus_pairs("L", ev))
    out["screening"] = {"share_of_lite_consensus_shown": round(sum(1 for u, c in lp if c in shown.get(u, [])) / len(lp), 3),
                        "codes_shown_per_thread": round(sum(len(v) for v in shown.values()) / len(shown), 1)}
    print("screening: %(share_of_lite_consensus_shown).3f of TACT-Lite's consensus assignments shown; "
          "%(codes_shown_per_thread).1f codes shown per thread" % out["screening"])
    (RESULTS / "coding_scores.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
