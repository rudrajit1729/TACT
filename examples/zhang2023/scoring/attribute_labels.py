#!/usr/bin/env python3
"""
Match every row of Zhang et al.'s five constant-comparison sheets to a thread of the corpus by its excerpt:
an exact normalised substring, else a word n-gram score of at least 0.5 that beats the next thread by 0.2.

  python3 examples/zhang2023/scoring/attribute_labels.py --xlsx "Dataset (SO).xlsx" --threads-json threads_revisions.json

Reads their spreadsheet (Zenodo, doi:10.5281/zenodo.8123303), data/threads.csv and every thread with its
revision history as JSON ({"threads": {question_id: {found, title, body, question_comments, answers: [{body,
comments}], question_revisions, answer_revisions}}}). Writes labels/reference_labels.csv, one line per
matched row and thread.
"""
from __future__ import annotations
import argparse, csv, html, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DATA, LABELS, REFERENCE_LABELS  # noqa: E402
from xlsx_read import read_sheet  # noqa: E402

def norm(s: str) -> str:
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = s.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def grams(tokens, n):
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def score(snip: str, seg: str) -> float:
    """Share of the snippet's word n-grams found in seg (1.0 if a plain substring)."""
    if not snip:
        return 0.0
    if snip in seg:
        return 1.0
    st, gt = snip.split(), seg.split()
    n = 3 if len(st) >= 6 else 2
    if len(st) < n:
        return 0.0
    sg = grams(st, n)
    return len(sg & grams(gt, n)) / len(sg)


def parts(raw: str) -> list[str]:
    """Split a Coded Data cell into its pieces: their extraction tool wrote composite cells
    as 'title\nQ:body', 'body\n\nC1:comment\nC2:comment', with 'WARN: THIS PARAGRAPH
    CONTAINS TAG: [CODE]' where a code block was. Pieces under 4 words are dropped unless
    the whole cell is that short."""
    raw = re.sub(r"WARN: THIS PARAGRAPH CONTAINS TAG: \[[A-Z]+\]", "\n\n", raw or "")
    pcs = re.split(r"\n\s*(?:Q|C\d+|A\d*):|\n\s*\n", raw)
    pcs = [norm(x) for x in pcs]
    pcs = [x for x in pcs if len(x.split()) >= 4] or [norm(raw)]
    return pcs


def thread_score(pcs: list[str], ss: list[tuple[str, str]]):
    """Length-weighted mean over pieces of the best segment score; returns (score, kinds)."""
    tot, acc, kinds = 0, 0.0, []
    for pc in pcs:
        sc, kind = max(((score(pc, s), k) for k, s in ss), default=(0.0, ""))
        w = len(pc.split())
        tot += w
        acc += w * sc
        if sc >= 0.5:
            kinds.append(kind)
    return (acc / tot if tot else 0.0), kinds


def segments(t: dict):
    yield "title", t["title"]
    yield "question_body", t["body"]
    for c in t["question_comments"]:
        yield "question_comment", c
    for a in t["answers"]:
        yield "answer", a["body"]
        for c in a["comments"]:
            yield "answer_comment", c
    # older revisions (their coding predates later edits)
    for r in t.get("question_revisions", []):
        if r.get("title"):
            yield "title", r["title"]
        if r.get("body"):
            yield "question_body", r["body"]
    for r in t.get("answer_revisions", []):
        if r.get("body"):
            yield "answer", r["body"]


SHEETS = {"Functions (SO)": "FU", "Purposes (SO)": "PU", "Benefits (SO)": "BE",
          "Limitations&Challenges (SO)": "LC", "Expected Features (SO)": "EF"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", required=True, help="Zhang et al.'s 'Dataset (SO).xlsx'")
    ap.add_argument("--threads-json", required=True, help="every thread with its revision history (see above)")
    a = ap.parse_args()
    csv.field_size_limit(10**8)
    threads = json.loads(Path(a.threads_json).read_text())["threads"]
    segs = {q: [(k, norm(x)) for k, x in segments(t)] for q, t in threads.items() if t["found"]}
    corpus = {r["so_question_id"]: r for r in csv.DictReader((DATA / "threads.csv").open(encoding="utf-8"))}
    unit_norm = {q: norm(r["text"]) for q, r in corpus.items()}
    out = []
    for sheet, dim in SHEETS.items():
        for i, r in enumerate(read_sheet(Path(a.xlsx), sheet)[1:], start=2):
            if not r or not r[0]:
                continue
            cat, file_, code, data = (str(x).strip() if x else "" for x in r[:4])
            pcs = parts(data)
            best = sorted(((sc, q, kinds) for q, ss in segs.items()
                           for sc, kinds in [thread_score(pcs, ss)] if sc > 0), key=lambda b: -b[0])
            second = best[1][0] if len(best) > 1 else 0.0
            if best and best[0][0] >= 0.999:
                hits, how = [b for b in best if b[0] >= 0.999], "exact"
            elif best and best[0][0] >= 0.5 and best[0][0] - second >= 0.2:
                hits, how = [best[0]], "fuzzy"
            else:
                hits, how = [], "unmatched"
            base = dict(sheet_row=i, dimension=dim, category=cat, coded_data=data.replace("\r", " "), match=how)
            if not hits:
                out.append({**base, "so_question_id": "", "uid": "", "segment": "", "in_unit_text": "",
                            "match_score": round(best[0][0], 3) if best else 0, "n_candidate_posts": 0})
            for sc, q, kinds in hits:
                order = ["title", "question_body", "question_comment", "answer", "answer_comment"]
                kinds = sorted(set(kinds), key=order.index) or ["?"]
                out.append({**base, "so_question_id": q, "uid": corpus[q]["uid"] if q in corpus else "",
                            "segment": "+".join(kinds),
                            "in_unit_text": any(score(pc, unit_norm[q]) >= 0.7 for pc in pcs) if q in unit_norm else "",
                            "match_score": round(sc, 3), "n_candidate_posts": len(hits)})
    cols = ["sheet_row", "dimension", "category", "so_question_id", "uid", "segment", "in_unit_text",
            "match", "match_score", "n_candidate_posts", "coded_data"]
    LABELS.mkdir(exist_ok=True)
    with REFERENCE_LABELS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    for dim in SHEETS.values():
        rs = [o for o in out if o["dimension"] == dim]
        print(dim, "rows", len({o["sheet_row"] for o in rs}), Counter(o["match"] for o in rs),
              "in our units", sum(1 for o in rs if o["uid"]), "text in unit", sum(1 for o in rs if o["in_unit_text"] is True))


if __name__ == "__main__":
    main()
