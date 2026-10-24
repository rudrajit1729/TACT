#!/usr/bin/env python3
"""
Build the TACT-Lite and TACT-Full results dashboards for the 256 Stack Overflow threads from the recorded
coding, without calling any model. It recomputes consensus and reliability on the 192 evaluation threads
with pipeline/reliability.py and stops if any code's alpha differs from the recorded one.

  python3 examples/zhang2023/build_dashboards.py

Reads, in examples/zhang2023/: config.yaml, data/threads.csv, data/splits.json, the final codebook
(codebooks/approved_codebook.json), results/L/coder_long.csv, results/LJA/coder_long.csv and
results/L_eval/ and results/LJA_eval/ (reliability.csv, summary.json). Writes dashboard_lite.html and
dashboard_full.html in the same folder.
"""
from __future__ import annotations

import csv
import html
import json
import shutil
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "pipeline"))
import config as C  # noqa: E402
import council as K  # noqa: E402
import dashboard as DB  # noqa: E402
import reliability as R  # noqa: E402

CODERS = OrderedDict([("1", "Claude Opus 5"), ("2", "GPT-5.6"), ("3", "Gemini 3.6 Flash")])
PAPER = {"L": {"name": "Lite", "cost": 35.26, "per100": 13.77, "kappa": 0.79},
         "LJA": {"name": "Full", "cost": 86.00, "per100": 33.59, "kappa": 0.85}}


def read_csv(p):
    csv.field_size_limit(10 ** 9)
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def current_keys(book):
    """Read the recorded codebook under the key names the pipeline uses now (in memory only; the file is not
    changed). The paper's run wrote `gate` for the review record, `anchor_quotes` for the representative quotes and
    `n_quarantined_accepted` for the number of adversary codes admitted at review."""
    if "review" not in book and "gate" in book:
        book["review"] = book["gate"]
    if "n_adversary_codes_accepted" not in book and "n_quarantined_accepted" in book:
        book["n_adversary_codes_accepted"] = book["n_quarantined_accepted"]
    for c in book.get("codes", []):
        if "representative_quotes" not in c and "anchor_quotes" in c:
            c["representative_quotes"] = c["anchor_quotes"]
    return book


def coder_rows(cond):
    return [OrderedDict([("coder", r["coder"]), ("uid", r["uid"]), ("batch", "-"), ("codes", [c for c in r["codes"].split("|") if c]),
                         ("why", r["why"]), ("uncovered_note", r["uncovered_note"])]) for r in read_csv(HERE / "results" / cond / "coder_long.csv")]


def build(mode: str, out: Path):
    data = C.read_config_file(HERE / "config.yaml")
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "paper-run"
        data["mode"], data["workspace"] = mode, str(ws)
        data["study"]["corpus_csv"] = str(HERE / "data" / "threads.csv")
        cfg = C.Config(data, HERE / "config.yaml")
        K.cfg, K.W = cfg, ws
        (ws / "data").mkdir(parents=True)
        shutil.copyfile(HERE / "data" / "threads.csv", ws / "data" / "corpus.csv")
        shutil.copyfile(HERE / "data" / "splits.json", ws / "data" / "splits.json")
        (ws / "codebooks").mkdir()
        book = current_keys(json.loads((HERE / "codebooks" / "approved_codebook.json").read_text(encoding="utf-8"), object_pairs_hook=OrderedDict))
        (ws / "codebooks" / "approved_codebook.json").write_text(json.dumps(book), encoding="utf-8")
        corpus = OrderedDict((r["uid"], r) for r in read_csv(ws / "data" / "corpus.csv"))
        evaluation = json.loads((ws / "data" / "splits.json").read_text())["evaluation"]
        prim = "LJA" if mode == "full" else "L"
        summaries = OrderedDict()
        for cond in (["L", "LJA"] if mode == "full" else ["L"]):
            rows = coder_rows(cond)
            dec = OrderedDict()   # no decision recorded: the paper keeps and reports all 72 codes
            res = R.run(rows=rows, coders=list(CODERS), problems=[], corpus=corpus, book=book, cfg=cfg, rel_units=evaluation,
                        out=ws / "results" / cond, label=cond, low_alpha_decisions=dec)
            # the paper's figures, recomputed: every code's alpha must match results/<cond>_eval/reliability.csv
            paper = {r["code"]: r for r in read_csv(HERE / "results" / ("%s_eval" % cond) / "reliability.csv")}
            mine = {r["code"]: r for r in res["rel"]}
            bad = [c for c in paper if c in mine and paper[c]["alpha"] and abs(float(paper[c]["alpha"]) - mine[c]["alpha"]) > 1e-9]
            ps = json.loads((HERE / "results" / ("%s_eval" % cond) / "summary.json").read_text())
            if bad or abs(ps["alpha_median"] - res["summary"]["alpha_median"]) > 1e-9:
                raise SystemExit("%s: recomputed alpha differs from the paper's files for %s" % (cond, bad or "the median"))
            summaries[cond] = res["summary"]
        DB.bind(K)
        s = summaries[prim]
        n_codes = book.get("n_approved") or len(book["codes"])
        DB.OPTIONS = OrderedDict([
            ("title", "The paper's validation: TACT-%s on 256 Stack Overflow threads" % PAPER[prim]["name"]),
            ("subtitle_html", "Corpus: the Stack Overflow threads about GitHub Copilot that Zhang et al. (2023) analysed, rebuilt as of 18 June 2023 "
                              "(<a href=\"data/ATTRIBUTION.md\">attribution, CC BY-SA</a>). Reliability is computed on the 192 evaluation threads."),
            ("links", [("README.md", "About this example"), ("codebooks/approved_codebook.json", "The approved codebook (JSON)"),
                       ("results/%s_eval/reliability.csv" % prim, "Every code's agreement (CSV)"),
                       ("dashboard_%s.html" % ("lite" if mode == "full" else "full"), "The %s dashboard" % ("TACT-Lite" if mode == "full" else "TACT-Full"))]),
            ("about_html", about_html(mode, n_codes, s)),
            ("below_threshold_status", "kept and reported"),
            ("codebook_version", "final"),
            ("retained_label", "codes at or above the alpha threshold"),
            ("below_threshold_decision_html", "Kept in the final codebook: the paper reports every figure on all %d codes." % n_codes),
            ("human_html", "<ul><li>Held-out sample: two authors independently coded the held-out evaluation threads with the approved "
                           "codebook, without seeing the model assignments, and resolved their differences. Pooled over all (thread, code) "
                           "decisions on the %d approved codes, the council's coding agreed with theirs at a Cohen's kappa of <b>%.2f</b> "
                           "under %s (paper, Section V-C).</li>"
                           "<li>Spot-check: two authors checked the AI coders' rationales against the codebook on a random 10%% of threads.</li>"
                           "<li>Codes below the alpha threshold stay in the final codebook; every figure here is on all %d codes.</li>"
                           "<li>The researchers' own files (blind pass, review, held-out coding) are not part of this folder.</li></ul>" % (
                               n_codes, PAPER[prim]["kappa"], "TACT-" + PAPER[prim]["name"], n_codes)),
            ("cost_html", "<p>From the paper's Table IV, at list prices in September 2026: TACT-Lite cost <b>$%.2f</b> for the 256 threads (about $%.0f per 100), "
                          "TACT-Full <b>$%.2f</b> (about $%.0f per 100). "
                          "<a href=\"../../SETUP.md\">SETUP.md</a> explains how cost scales with your corpus.</p>" % (
                              PAPER["L"]["cost"], PAPER["L"]["per100"], PAPER["LJA"]["cost"], PAPER["LJA"]["per100"])),
            ("footer_html", "Built by <code>examples/zhang2023/build_dashboards.py</code> from the paper's result files in this folder, with this "
                            "repository's own consensus and reliability code; every code's alpha matches the paper's files."),
        ])
        try:
            out.write_text(DB.build(), encoding="utf-8")
        finally:
            DB.OPTIONS = {}
        print("%s: TACT-%s, median alpha %.2f (min %.2f, max %.2f) on %d evaluation threads, %d codes; cross-family kappa median %.2f"
              % (out.name, PAPER[prim]["name"], s["alpha_median"], s["alpha_min"], s["alpha_max"], s["n_reliability_units"],
                 s["n_codes"], s["cross_family_kappa_median"]))
        return summaries


def about_html(mode, n_codes, s):
    e = html.escape
    roles = ", ".join("coder %s %s" % (k, e(v)) for k, v in CODERS.items())
    if mode == "lite":
        what = ("<b>TACT-Lite coding</b> (condition L): three AI coders, %s, each applied the approved codebook to every thread with every "
                "code shown; a code reaches consensus when at least two of the three AI coders assign it." % roles)
    else:
        what = ("<b>TACT-Full coding</b> (condition LJA): the same three AI coders (%s) coded every thread with the codes the decision "
                "model (TypeSafe Jev) screened for it; then an adversary from another model family critiqued each AI coder's batch and the "
                "AI coder answered, keeping or revising each assignment. The TACT-Lite row of the table below is the same codebook coded "
                "without screening or adversaries." % roles)
    return ("<p>%s</p><p>The approved codebook (<b>%d codes</b> across five research questions) came out of discovery by three "
            "AI analysts from the same three model families, reconciliation by Claude Opus 5, human review, and the consolidation "
            "the paper describes in Section V-C. "
            "The research questions are Zhang et al.'s own: functions implemented with Copilot, purposes of using it, benefits, "
            "limitations and challenges, and expected features.</p>"
            "<p>The paper reports a median alpha of 0.77 for TACT-Lite and 0.87 for TACT-Full on the evaluation threads; this page "
            "recomputes it from the AI coders' assignments: <b>%.2f</b> here.</p>" % (what, n_codes, s["alpha_median"]))


def main():
    build("lite", HERE / "dashboard_lite.html")
    build("full", HERE / "dashboard_full.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
