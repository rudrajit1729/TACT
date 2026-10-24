#!/usr/bin/env python3
"""
Build the reference labels from Zhang et al.'s spreadsheet and the recorded match of each excerpt to a
thread. A row whose excerpt points to exactly one thread (n_candidate_posts = 1) is a reference label.

  python3 examples/zhang2023/scoring/reference_labels.py --xlsx "path/to/Dataset (SO).xlsx"

Reads their spreadsheet (Zenodo, doi:10.5281/zenodo.8123303) and mapping/label_attribution.csv. Writes
labels/reference_labels.csv, one line per (sheet row, thread).
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import MAPPING, LABELS, REFERENCE_LABELS  # noqa: E402
from xlsx_read import read_sheet  # noqa: E402

SHEETS = {"FU": "Functions (SO)", "PU": "Purposes (SO)", "BE": "Benefits (SO)",
          "LC": "Limitations&Challenges (SO)", "EF": "Expected Features (SO)"}
COLS = ["sheet_row", "dimension", "category", "so_question_id", "uid", "segment", "in_unit_text",
        "match", "match_score", "n_candidate_posts", "coded_data"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", required=True, help="Zhang et al.'s 'Dataset (SO).xlsx'")
    a = ap.parse_args()
    sheets = {dim: read_sheet(Path(a.xlsx), name) for dim, name in SHEETS.items()}
    out = []
    with (MAPPING / "label_attribution.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            row = sheets[r["dimension"]][int(r["sheet_row"]) - 1]
            cat, _file, _code, data = (str(x).strip() if x else "" for x in (tuple(row) + ("",) * 4)[:4])
            out.append({**r, "category": cat, "coded_data": data.replace("\r", " ")})
    LABELS.mkdir(exist_ok=True)
    with REFERENCE_LABELS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(out)
    print("%d rows -> %s; %d reference labels (excerpt in exactly one thread)"
          % (len(out), REFERENCE_LABELS, sum(1 for o in out if o["n_candidate_posts"] == "1")))


if __name__ == "__main__":
    main()
