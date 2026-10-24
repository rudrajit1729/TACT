#!/usr/bin/env python3
"""
Run the single-model baseline: one GPT-5.6 call that builds a codebook for the five research
questions and codes every thread.

  python3 examples/zhang2023/baseline_gpt/run_baseline.py [--out PATH] [--config PATH] [--dry-run]

Reads data/threads.csv and the research questions in config.yaml. Writes output_rerun.json
({"codebook": [...], "assignments": [...]}); --dry-run prints the prompt without calling the model.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE.parent
REPO = EXAMPLE.parent.parent
sys.path.insert(0, str(REPO / "pipeline"))
import config as C  # noqa: E402
import models  # noqa: E402

DEFAULT_CONFIG = EXAMPLE / "config.yaml"
THREADS = EXAMPLE / "data" / "threads.csv"
FAMILY = "gpt"
STAGE = "baseline"

BRIEF = """# Thematic analysis of {n} Stack Overflow threads about GitHub Copilot

You are a qualitative researcher. `threads.txt` holds {n} Stack Overflow threads (question, answers and
comments) about GitHub Copilot, each under a line `=== THREAD <id> ===`. Do a thematic analysis to answer
these five research questions:

{rqs}

1. For each research question, develop a codebook: codes, each with a short label and a one-sentence
   definition.
2. Then code every thread: for each thread, list every code that applies (a thread may have none, or
   codes from several questions).

Return one JSON object under the key `output.json`, in exactly this shape:

{{"codebook": [{{"id": "RQ1.4-C1", "rq": "RQ1.4", "label": "...", "definition": "..."}}],
  "assignments": [{{"uid": "U001", "codes": ["RQ1.4-C1"]}}]}}

Include an assignments entry for every thread id, even if its code list is empty.
"""


def read_threads() -> list:
    csv.field_size_limit(10 ** 8)
    with THREADS.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_inputs(work: Path, cfg, rows: list) -> tuple[Path, list]:
    work.mkdir(parents=True, exist_ok=True)
    rqs = "\n".join("- %s: %s" % (q["id"], q["text"]) for q in cfg.rqs.values())
    brief = work / "brief.md"
    brief.write_text(BRIEF.format(n=len(rows), rqs=rqs), encoding="utf-8")
    threads = work / "threads.txt"
    threads.write_text("\n\n".join("=== THREAD %s ===\n%s" % (r["uid"], r["text"]) for r in rows) + "\n", encoding="utf-8")
    return brief, [("threads.txt", threads)]


def check(out: dict, uids: list) -> list:
    msgs = []
    ids = {c.get("id") for c in out.get("codebook", [])}
    got = [a.get("uid") for a in out.get("assignments", [])]
    missing = [u for u in uids if u not in set(got)]
    if missing:
        msgs.append("%d threads without an assignments entry: %s" % (len(missing), ", ".join(missing[:20])))
    unknown = sorted({c for a in out.get("assignments", []) for c in a.get("codes", []) if c not in ids})
    if unknown:
        msgs.append("%d code ids not in the codebook: %s" % (len(unknown), ", ".join(map(str, unknown[:20]))))
    return msgs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="config with the gpt model family and the five questions (default: %(default)s)")
    ap.add_argument("--out", default=str(HERE / "output_rerun.json"), help="output JSON (default: %(default)s)")
    ap.add_argument("--work", help="folder for the prompt inputs and the reply (default: <workspace>/baseline)")
    ap.add_argument("--dry-run", action="store_true", help="build and print the prompt; call no model, write nothing")
    a = ap.parse_args()

    cfg = C.load(a.config)
    models.configure(cfg)
    rows = read_threads()
    if len(cfg.rqs) != 5:
        sys.exit("expected Zhang et al.'s five research questions in %s, found %d" % (a.config, len(cfg.rqs)))

    if a.dry_run:
        with tempfile.TemporaryDirectory() as tmp:
            brief, inputs = write_inputs(Path(tmp), cfg, rows)
            p = models.preview(stage=STAGE, role="single-model-baseline", family=FAMILY, brief=brief, inputs=inputs, reasoning=True)
        print("call id %s | family %s | backend %s | model %s | reasoning %s | %d threads | %d chars, about %d tokens"
              % (p["call_id"], p["family"], p["backend"], p["model"], p["reasoning"], len(rows), p["prompt_chars"], p["prompt_tokens_estimated"]))
        print("-" * 100)
        print(p["prompt"])
        print("-" * 100)
        print("dry run: 1 prompt built, no model called, nothing written")
        return

    work = Path(a.work).resolve() if a.work else cfg.workspace / "baseline"
    brief, inputs = write_inputs(work, cfg, rows)
    print("one call: %d threads, %d research questions -> %s" % (len(rows), len(cfg.rqs), models.resolve_model(FAMILY, STAGE)[2]))
    models.call(stage=STAGE, role="single-model-baseline", family=FAMILY, brief=brief, inputs=inputs,
                outputs=[("output.json", "output.json")], root=work, reasoning=True)
    out = json.loads((work / "output.json").read_text(encoding="utf-8"))
    out = {"codebook": out.get("codebook", []), "assignments": out.get("assignments", [])}
    dest = Path(a.out).resolve()
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for m in check(out, [r["uid"] for r in rows]):
        print("   ! " + m)
    print("codes %d, assignments %d -> %s" % (len(out["codebook"]), len(out["assignments"]), dest))


if __name__ == "__main__":
    main()
