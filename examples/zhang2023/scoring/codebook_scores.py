#!/usr/bin/env python3
"""
Score the TACT-Lite and TACT-Full candidate codebooks and the final codebook against Zhang et al.'s
reference labels on the 192 evaluation threads: recall, precision, F1 and categories per code, where a
code counts for every thread it cites as evidence.

  python3 examples/zhang2023/scoring/codebook_scores.py

Reads codebooks/, mapping/mapping_*.json and mapping/alt_mapping_*.json, data/splits.json and
labels/reference_labels.csv. Writes results/codebook_scores.json and prints a table.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (DIM, CODEBOOK, MAP, ALT_MAP, RESULTS, read_json, load_mapping,  # noqa: E402
                   evaluation_threads, reference_labels)


def score(codes, mp, lab, ev):
    rq = {c["id"]: c.get("rq", "") for c in codes}
    pairs = [(u, c["id"]) for c in codes for u in c["units"] if u in ev]
    gold = {(u, k) for u, ks in lab.items() for k in ks}
    hit = gold & {(u, k) for u, c in pairs for k in mp.get(c, ())}
    sq = [(u, c) for u, c in pairs if mp.get(c) and any(x[:2] == DIM.get(rq[c]) for x in lab.get(u, ()))]
    ag = sum(1 for u, c in sq if mp[c] & lab[u])
    R, P = len(hit) / len(gold), ag / len(sq)
    return R, P, 2 * R * P / (R + P), "%d/%d" % (len(hit), len(gold)), "%d/%d" % (ag, len(sq))


def main():
    ev = evaluation_threads()
    lab = reference_labels(ev)
    rows = [("TACT-Lite candidate", "lite", MAP["lite"]), ("TACT-Full candidate", "full", MAP["full"]),
            ("Approved", "approved", MAP["approved"]),
            ("TACT-Lite candidate, alternative mapping", "lite", ALT_MAP["lite"]),
            ("TACT-Full candidate, alternative mapping", "full", ALT_MAP["full"])]
    out = []
    print("%-42s %5s %7s %7s %6s %8s  %-9s %s" % ("codebook", "codes", "recall", "prec", "F1", "breadth", "matched", "agreeing"))
    for name, book, mpath in rows:
        codes = read_json(CODEBOOK[book])["codes"]
        mp = load_mapping(mpath)
        breadth = sum(len(v) for v in mp.values()) / len(mp)
        R, P, F, a, b = score(codes, mp, lab, ev)
        out.append({"codebook": name, "mapping": mpath.name, "codes": len(codes), "recall": round(R, 3),
                    "precision": round(P, 3), "f1": round(F, 3), "categories_per_code": round(breadth, 2),
                    "unmapped_codes": sum(1 for v in mp.values() if not v), "matched": a, "agreeing": b})
        print("%-42s %5d %7.3f %7.3f %6.3f %8.2f  %-9s %s" % (name, len(codes), R, P, F, breadth, a, b))
    (RESULTS / "codebook_scores.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
