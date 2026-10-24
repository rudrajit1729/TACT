"""Where the scoring programs find the validation files. Every path is relative to examples/zhang2023/.

  data/threads.csv, data/splits.json      the 256 threads and the split (192 evaluation threads)
  codebooks/                              the Lite and Full candidate codebooks and the approved codebook
  mapping/                                Zhang et al.'s categories (our definitions), the mappings and their audits
  results/<cond>/consensus.csv            the coding that reached consensus (L = TACT-Lite, LJA = TACT-Full)
  labels/reference_labels.csv             Zhang et al.'s labels attributed to threads; built by
                                          scoring/reference_labels.py from their spreadsheet (not redistributed here)
"""
from __future__ import annotations
import csv, json, sys
from collections import defaultdict
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parent.parent
DATA = EXAMPLE / "data"
CODEBOOKS = EXAMPLE / "codebooks"
MAPPING = EXAMPLE / "mapping"
RESULTS = EXAMPLE / "results"
LABELS = EXAMPLE / "labels"
REFERENCE_LABELS = LABELS / "reference_labels.csv"
CATEGORIES = MAPPING / "categories.json"

# Zhang et al.'s five qualitative research questions and the prefix of their category ids.
DIM = {"RQ1.4": "FU", "RQ1.5": "PU", "RQ2.1": "BE", "RQ2.2": "LC", "RQ2.3": "EF"}

CODEBOOK = {"lite": CODEBOOKS / "candidate_lite.json", "full": CODEBOOKS / "candidate_full.json",
            "approved": CODEBOOKS / "approved_codebook.json"}
MAP = {"lite": MAPPING / "mapping_lite.json", "full": MAPPING / "mapping_full.json",
       "approved": MAPPING / "mapping_approved.json"}
ALT_MAP = {"lite": MAPPING / "alt_mapping_lite.json", "full": MAPPING / "alt_mapping_full.json"}


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def evaluation_threads() -> set:
    return set(read_json(DATA / "splits.json")["evaluation"])


def load_mapping(p) -> dict:
    """code id -> set of Zhang et al. category ids."""
    return {m["code_id"]: {c["id"] for c in m["categories"]} for m in read_json(p)["mapping"]}


def category_ids() -> dict:
    return {c["name"].strip().lower(): c["id"] for c in read_json(CATEGORIES)["categories"]}


def reference_labels(units=None, segments=None) -> dict:
    """thread uid -> set of category ids: Zhang et al.'s labels whose text points to exactly one thread
    (the reference labels), on the given threads (default: the evaluation threads)."""
    if not REFERENCE_LABELS.exists():
        sys.exit("No reference labels: %s is missing.\nBuild it from Zhang et al.'s spreadsheet "
                 "(Zenodo, doi:10.5281/zenodo.8123303, file 'Dataset (SO).xlsx'):\n"
                 "  python3 examples/zhang2023/scoring/reference_labels.py --xlsx 'path/to/Dataset (SO).xlsx'"
                 % REFERENCE_LABELS.relative_to(EXAMPLE.parent.parent))
    units = evaluation_threads() if units is None else units
    zc = category_ids()
    lab = defaultdict(set)
    csv.field_size_limit(10 ** 8)
    with REFERENCE_LABELS.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["uid"] in units and r["n_candidate_posts"] == "1" and (segments is None or r["segment"] in segments):
                lab[r["uid"]].add(zc[r["category"].strip().lower().replace("  ", " ")])
    return lab
