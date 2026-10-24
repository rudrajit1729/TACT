#!/usr/bin/env python3
"""
Build the pipeline's input, corpus.csv, from the 256 threads in data/, with a stratum column so that
`council.py prepare` with this folder's config draws the same split as data/splits.json.

  python3 examples/zhang2023/to_pipeline_csv.py [--out PATH]
  python3 examples/zhang2023/to_pipeline_csv.py --check WORKSPACE

Reads data/threads.csv and data/splits.json. Writes examples/zhang2023/corpus.csv (or --out) with uid, text,
stratum, link, so_question_id, created and author. --check compares a prepared workspace's split with
data/splits.json and exits 1 if the reserved threads, evaluation threads or blind-pass sample differ; the
held-out sample need not match.
"""
import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "corpus.csv"))
    ap.add_argument("--check", help="a prepared workspace whose data/splits.json is compared with the paper's split")
    a = ap.parse_args()
    src, spf = HERE / "data" / "threads.csv", HERE / "data" / "splits.json"
    csv.field_size_limit(10 ** 9)
    sp = json.loads(spf.read_text(encoding="utf-8"))
    if a.check:
        mine = json.loads((Path(a.check) / "data" / "splits.json").read_text())
        same_all = True
        for k in ("development", "evaluation", "blind_pass"):
            same = set(mine.get(k, [])) == set(sp[k])
            same_all &= same
            print("%-12s %s (%d vs %d)" % (k, "identical" if same else "DIFFERENT", len(mine.get(k, [])), len(sp[k])))
        common = len(set(mine.get("held_out", [])) & set(sp["held_out"]))
        print("%-12s %d of the workspace's %d threads are among the %d the researchers coded (not required to match)"
              % ("held_out", common, len(mine.get("held_out", [])), len(sp["held_out"])))
        return 0 if same_all else 1
    with open(src, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    cols = ["uid", "text", "stratum", "link", "so_question_id", "created", "author"]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({"uid": r["uid"], "text": r["text"], "stratum": sp["strata"][r["uid"]], "link": r["link"],
                        "so_question_id": r["so_question_id"], "created": r["created"], "author": r["author"]})
    print("wrote %s: %d threads" % (a.out, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
