#!/usr/bin/env python3
"""
Map a codebook onto Zhang et al.'s categories from the code and category definitions alone. A Claude
model and a GPT model each build a mapping independently, and the Claude model reconciles the two.

  python3 examples/zhang2023/scoring/map_codebook.py <codebook.json> <out.json> [--config PATH] [--work DIR] [--dry-run]

Reads the codebook, mapping/categories.json and the claude and gpt model families in config.yaml. Writes
<out.json> ({"mapping": [{"code_id": ..., "categories": [{"id": ...}]}]}), <out>_rationales.json with each
code's rationales, and every call's prompt and reply in the work folder (default <workspace>/mapping/<out stem>/;
a call whose reply is already there is skipped). --dry-run prints the three prompts without calling any model
or writing any file.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE.parent
REPO = EXAMPLE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(REPO / "pipeline"))
from paths import CATEGORIES, DIM  # noqa: E402
import config as C  # noqa: E402
import models  # noqa: E402

DEFAULT_CONFIG = EXAMPLE / "config.yaml"
CLAUDE, GPT = "claude", "gpt"          # model families in the config's `models` section
STAGE = "mapping"

# Zhang et al.'s five questions and the dimension of their categories that answers each.
RQ_DIMENSION = {"RQ1.4": "Functions", "RQ1.5": "Purposes", "RQ2.1": "Benefits",
                "RQ2.2": "Limitations & challenges", "RQ2.3": "Expected features"}

RULE = ("A council code maps to every category that a researcher using the reference scheme might reasonably "
        "have assigned to a thread carrying that code.")

MAP_BRIEF = """# Mapping a council codebook onto a reference scheme

Two research teams coded the same Stack Overflow threads about GitHub Copilot independently, each with
its own codebook. The first is a council codebook (`council_codes.json`); the second is a reference
scheme of categories (`reference_categories.json`). Both are organized by the same five research
questions, and `reference_categories.json` names the dimension of categories that answers each question.

Map each council code onto the reference categories, using the definitions alone. You do not see any
thread or any coded data.

The rule: {rule} Judge by the code's label, definition, include and exclude clauses and by the
category's definition, not by shared words. A code answers one research question, so map it only to
categories of that question's dimension. A code may map to one category, to several, or to none; give
an empty list rather than forcing a match.

For every council code, give a rationale of one to three sentences: which categories you assigned and
why, and, where it helps, which neighbouring category you left out and why.

Return one JSON object under the key `mapping.json`:

{{"mapping": [{{"code_id": "T01", "categories": ["LC01", "LC07"], "rationale": "..."}},
             {{"code_id": "T02", "categories": [], "rationale": "..."}}]}}

Every council code must appear exactly once; use only category ids from `reference_categories.json`.
""".format(rule=RULE)

RECONCILE_BRIEF = """# Reconciling two mappings of a council codebook onto a reference scheme

Earlier you mapped each code of a council codebook (`council_codes.json`) onto the categories of a
reference scheme (`reference_categories.json`), from the definitions alone; your mapping, with your
rationale for each code, is `mapping_1.json`. Another mapper, working independently from the same two
files, built `mapping_2.json`. Neither of you saw any thread or any coded data.

Reconcile the two into one mapping. The rule is the one you mapped by: {rule} For each code, look at
every category that either mapping assigned, decide each one against the code's and the category's
definitions, and keep the categories the rule supports. A code answers one research question, so map
it only to categories of that question's dimension. A code may end with no category.

For every council code, give a rationale of one to three sentences for the reconciled categories; where
the two mappings differed, say which categories you kept or dropped and why.

Return one JSON object under the key `mapping.json`:

{{"mapping": [{{"code_id": "T01", "categories": ["LC01", "LC07"], "rationale": "..."}},
             {{"code_id": "T02", "categories": [], "rationale": "..."}}]}}

Every council code must appear exactly once; use only category ids from `reference_categories.json`.
""".format(rule=RULE)


# --------------------------------------------------------------------------- inputs
def council_codes(book: dict, cfg) -> dict:
    """The codes with their definitions only: no quotes, provenance, threads or review notes."""
    codes = [{k: c.get(k, "") for k in ("id", "rq", "label", "definition", "include", "exclude")}
             for c in book["codes"]]
    rqs = {q: (cfg.rqs[q]["text"] if q in cfg.rqs else "") for q in RQ_DIMENSION}
    return {"research_questions": rqs, "codes": codes}


def reference_categories() -> dict:
    """Zhang et al.'s categories with their definitions only (their example excerpts are left out)."""
    cats = json.loads(CATEGORIES.read_text(encoding="utf-8"))["categories"]
    return {"dimension_of_each_research_question": RQ_DIMENSION,
            "categories": [{k: c[k] for k in ("id", "dimension", "name", "definition")} for c in cats]}


# --------------------------------------------------------------------------- replies
def normalise(reply) -> list:
    """[{code_id, categories: [ids], rationale}] from the reply; tolerates category objects and a dict keyed by code."""
    m = reply.get("mapping", reply) if isinstance(reply, dict) else reply
    if isinstance(m, dict):
        m = [dict(v, code_id=k) if isinstance(v, dict) else {"code_id": k, "categories": v} for k, v in m.items()]
    out = []
    for x in m or []:
        cats = []
        for c in x.get("categories") or []:
            cid = c if isinstance(c, str) else (c.get("id") or c.get("category_id") or "")
            if cid and cid not in cats:
                cats.append(str(cid).strip())
        out.append({"code_id": str(x.get("code_id") or x.get("id") or ""), "categories": cats,
                    "rationale": str(x.get("rationale") or x.get("reason") or "").strip()})
    return out


def problems(mapping: list, codes: list, cat_ids: set) -> list:
    rq = {c["id"]: c["rq"] for c in codes}
    seen, msgs = {}, []
    for x in mapping:
        seen[x["code_id"]] = seen.get(x["code_id"], 0) + 1
        if x["code_id"] not in rq:
            msgs.append("unknown code id %s" % x["code_id"])
            continue
        for cid in x["categories"]:
            if cid not in cat_ids:
                msgs.append("%s: unknown category id %s" % (x["code_id"], cid))
            elif rq[x["code_id"]] in DIM and not cid.startswith(DIM[rq[x["code_id"]]]):
                msgs.append("%s (%s): category %s belongs to another question's dimension" % (x["code_id"], rq[x["code_id"]], cid))
        if not x["rationale"]:
            msgs.append("%s: no rationale" % x["code_id"])
    msgs += ["%s appears %d times" % (k, n) for k, n in seen.items() if n > 1]
    missing = [c for c in rq if c not in seen]
    if missing:
        msgs.append("missing codes: %s" % ", ".join(missing))
    return msgs


# --------------------------------------------------------------------------- steps
def steps(work: Path) -> list:
    """(name, family, role, brief, input files, reply file)."""
    base = [("council_codes.json", work / "council_codes.json"), ("reference_categories.json", work / "reference_categories.json")]
    return [
        ("1 Claude Opus 5 builds a mapping", CLAUDE, "mapper-claude", work / "map_brief.md", base, "1_claude_mapping.json"),
        ("2 GPT-5.6, a new and independent instance, builds a second mapping", GPT, "mapper-gpt", work / "map_brief.md",
         base, "2_gpt_mapping.json"),
        ("3 The Claude instance reconciles the two mappings", CLAUDE, "mapper-claude-reconciles", work / "reconcile_brief.md",
         base + [("mapping_1.json", work / "1_claude_mapping.json"), ("mapping_2.json", work / "2_gpt_mapping.json")],
         "3_reconciled_mapping.json"),
    ]


def write_inputs(work: Path, book: dict, cfg):
    work.mkdir(parents=True, exist_ok=True)
    (work / "council_codes.json").write_text(json.dumps(council_codes(book, cfg), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (work / "reference_categories.json").write_text(json.dumps(reference_categories(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (work / "map_brief.md").write_text(MAP_BRIEF, encoding="utf-8")
    (work / "reconcile_brief.md").write_text(RECONCILE_BRIEF, encoding="utf-8")


def instruction(n_codes: int) -> str:
    return "Map all %d council codes; return each code_id exactly once, with a rationale." % n_codes


def dry_run(book: dict, cfg, work_final: Path):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        write_inputs(work, book, cfg)
        for f, step in (("1_claude_mapping.json", 1), ("2_gpt_mapping.json", 2)):
            src = work_final / f
            (work / f).write_text(src.read_text(encoding="utf-8") if src.exists() else
                                  '{"mapping": "<the reply of step %d is placed here at run time>"}\n' % step, encoding="utf-8")
        for name, fam, role, brief, inputs, reply in steps(work):
            p = models.preview(stage=STAGE, role=role, family=fam, brief=brief, inputs=inputs,
                               batch=reply.split(".")[0], instruction=instruction(len(book["codes"])), reasoning=True)
            print("=" * 100)
            print("STEP %s" % name)
            print("call id %s | family %s | backend %s | model %s | reasoning %s | %d chars, about %d tokens"
                  % (p["call_id"], p["family"], p["backend"], p["model"], p["reasoning"], p["prompt_chars"], p["prompt_tokens_estimated"]))
            print("-" * 100)
            print(p["prompt"])
    print("=" * 100)
    print("dry run: 3 prompts built, no model called, nothing written")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("codebook", help="codebook JSON with a `codes` list (id, rq, label, definition, include, exclude)")
    ap.add_argument("out", help="output mapping JSON")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="config with the claude and gpt model families (default: %(default)s)")
    ap.add_argument("--work", help="folder for the calls' inputs and replies (default: <workspace>/mapping/<out stem>)")
    ap.add_argument("--dry-run", action="store_true", help="build and print the prompts; call no model, write nothing")
    a = ap.parse_args()

    cfg = C.load(a.config)
    models.configure(cfg)
    book = json.loads(Path(a.codebook).read_text(encoding="utf-8"))
    codes = book["codes"]
    out = Path(a.out).resolve()
    work = Path(a.work).resolve() if a.work else cfg.workspace / "mapping" / out.stem
    if a.dry_run:
        dry_run(book, cfg, work)
        return

    write_inputs(work, book, cfg)
    cat_ids = {c["id"] for c in reference_categories()["categories"]}
    result = {}
    for name, fam, role, brief, inputs, reply in steps(work):
        path = work / reply
        print("%s ... " % name, end="", flush=True)
        if path.exists():
            print("reply already in %s" % path)
        else:
            models.call(stage=STAGE, role=role, family=fam, brief=brief, inputs=inputs, batch=reply.split(".")[0],
                        outputs=[("mapping.json", reply)], root=work, instruction=instruction(len(codes)), reasoning=True)
            print("done")
        got = normalise(json.loads(path.read_text(encoding="utf-8")))
        for attempt in range(1, int(cfg.d.get("max_repairs", 2)) + 1):
            msgs = problems(got, codes, cat_ids)
            if not msgs:
                break
            print("   %d problem(s) in the reply; asking the same role again (attempt %d)" % (len(msgs), attempt))
            prev = work / ("%s.attempt%d_previous.json" % (path.stem, attempt))
            path.replace(prev)
            models.call(stage=STAGE, role=role, family=fam, brief=brief, inputs=inputs + [("previous_reply.json", prev)],
                        batch=reply.split(".")[0], outputs=[("mapping.json", reply)], root=work, attempt=attempt, reasoning=True,
                        instruction=instruction(len(codes)) + " Your previous reply (previous_reply.json) had these problems; "
                        "return the complete mapping again with them fixed:\n- " + "\n- ".join(msgs))
            got = normalise(json.loads(path.read_text(encoding="utf-8")))
        msgs = problems(got, codes, cat_ids)
        if msgs:
            sys.exit("step %s: the reply in %s still has problems:\n  %s" % (name, path, "\n  ".join(msgs)))
        result[reply] = {x["code_id"]: x for x in got}

    final = result["3_reconciled_mapping.json"]
    order = [c["id"] for c in codes]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"mapping": [{"code_id": c, "categories": [{"id": k} for k in final[c]["categories"]]}
                                           for c in order]}, indent=1) + "\n", encoding="utf-8")
    side = out.with_name(out.stem + "_rationales.json")
    side.write_text(json.dumps({
        "procedure": "Section V-B: Claude Opus 5 maps; a new, independent GPT-5.6 instance maps; the Claude instance reconciles. "
                     "Definitions only. Rule: " + RULE,
        "models": {fam: models.resolve_model(fam, STAGE)[2] for fam in (CLAUDE, GPT)},
        "codes": [{"code_id": c, "categories": final[c]["categories"], "rationale": final[c]["rationale"],
                   "claude_mapping": result["1_claude_mapping.json"][c],
                   "gpt_mapping": result["2_gpt_mapping.json"][c]} for c in order]}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n_cells = sum(len(final[c]["categories"]) for c in order)
    print("mapped %d codes, %d cells (%.2f categories per code), %d codes with no category -> %s; rationales -> %s"
          % (len(order), n_cells, n_cells / max(1, len(order)), sum(1 for c in order if not final[c]["categories"]), out, side))


if __name__ == "__main__":
    main()
