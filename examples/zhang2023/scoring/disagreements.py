#!/usr/bin/env python3
"""
List the code-thread pairs that count against the precision of the TACT-Full candidate codebook: assignments
on evaluation threads Zhang et al. labeled for the same research question, where the code maps to none of
the categories they gave the thread. Pairs are grouped by research question, code and category.

  python3 examples/zhang2023/scoring/disagreements.py

Reads codebooks/candidate_full.json, mapping/mapping_full.json, mapping/categories.json, data/splits.json and
labels/reference_labels.csv. Writes results/disagreements_full.json and prints the counts.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DIM, CODEBOOK, MAP, CATEGORIES, RESULTS, read_json, load_mapping, evaluation_threads, reference_labels  # noqa: E402


def main():
    ev = evaluation_threads()
    lab = reference_labels(ev)
    zname = {c["id"]: c["name"] for c in read_json(CATEGORIES)["categories"]}
    book = read_json(CODEBOOK["full"])["codes"]
    mp = load_mapping(MAP["full"])
    cname = {c["id"]: c.get("name") or c.get("label") or c["id"] for c in book}
    rq = {c["id"]: c.get("rq", "") for c in book}
    n_sq = n_ag = 0
    dis = Counter()
    for c in book:
        for u in c["units"]:
            if u not in ev or not mp.get(c["id"]):
                continue
            same = {x for x in lab.get(u, ()) if x[:2] == DIM.get(rq[c["id"]])}
            if not same:
                continue
            n_sq += 1
            if mp[c["id"]] & lab[u]:
                n_ag += 1
            else:
                dis[(rq[c["id"]], cname[c["id"]], " / ".join(sorted(zname[x] for x in same)),
                     " / ".join(sorted(zname[x] for x in mp[c["id"]])))] += 1
    assert n_sq - n_ag == sum(dis.values())
    out = [{"rq": q, "council_code": cc, "zhang_category": zcat, "code_maps_to": m, "threads": n}
           for (q, cc, zcat, m), n in sorted(dis.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1]))]
    (RESULTS / "disagreements_full.json").write_text(json.dumps(
        {"pairs": n_sq, "agreeing": n_ag, "disagreeing": n_sq - n_ag, "rows": out}, indent=1))
    print("pairs scored %d, agreeing %d, counting against precision %d (%d table rows)" % (n_sq, n_ag, n_sq - n_ag, len(out)))
    for q in DIM:
        print("  %s %d" % (q, sum(r["threads"] for r in out if r["rq"] == q)))


if __name__ == "__main__":
    main()
