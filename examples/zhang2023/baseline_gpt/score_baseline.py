#!/usr/bin/env python3
"""
Score the single-model baseline the same way as TACT's final coding: recall, precision and F1 of its
codes, mapped onto Zhang et al.'s categories, on the evaluation threads.

  python3 examples/zhang2023/baseline_gpt/score_baseline.py [--map [--dry-run]]

Reads output.json, mapping_baseline.json, data/splits.json and the reference labels. Writes codebook.json and
scores.json (against the 182 reference labels in categories the final codebook covers, and against all 183).
--map first builds mapping_baseline_rerun.json with scoring/map_codebook.py (which calls models) and writes
scores_rerun.json instead; --map --dry-run prints the mapping prompts and stops.
"""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SCORING = HERE.parent / "scoring"
sys.path.insert(0, str(SCORING))
from paths import MAP, load_mapping, evaluation_threads, reference_labels  # noqa: E402
from coding_scores import score  # noqa: E402

out = json.loads((HERE / "output.json").read_text())
book = {"codes": [{"id": c["id"], "rq": c["rq"], "label": c["label"], "definition": c.get("definition", "")} for c in out["codebook"]]}
(HERE / "codebook.json").write_text(json.dumps(book, indent=1))
mp_path, scores_path = HERE / "mapping_baseline.json", HERE / "scores.json"
if "--map" in sys.argv:
    mp_path, scores_path = HERE / "mapping_baseline_rerun.json", HERE / "scores_rerun.json"
    cmd = [sys.executable, str(SCORING / "map_codebook.py"), str(HERE / "codebook.json"), str(mp_path)]
    subprocess.run(cmd + (["--dry-run"] if "--dry-run" in sys.argv else []), check=True)
    if "--dry-run" in sys.argv:
        sys.exit(0)
mp = load_mapping(mp_path)
rqs = {c["id"]: c["rq"] for c in book["codes"]}
evs = evaluation_threads()
lab = reference_labels(evs)
cov = set().union(*load_mapping(MAP["approved"]).values())
lab182 = {u: {x for x in cs if x in cov} for u, cs in lab.items()}; lab182 = {u: cs for u, cs in lab182.items() if cs}
pairs = [(a["uid"], c) for a in out["assignments"] if a["uid"] in evs for c in a.get("codes", []) if c in rqs]
res = {}
for name, L in (("182_labels", lab182), ("183_labels", lab)):
    s = score(pairs, mp, rqs, L, evs)
    res[name] = {"recall": round(s["recall"], 4), "precision": round(s["precision"], 4), "f1": round(s["f1"], 4), "matched": s["matched"]}
res["n_codes"] = len(book["codes"]); res["cats_per_code"] = round(sum(len(v) for v in mp.values()) / max(1, len(mp)), 2)
res["n_unmapped"] = sum(1 for c in book["codes"] if not mp.get(c["id"]))
scores_path.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
