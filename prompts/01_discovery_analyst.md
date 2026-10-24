# 01 Discovery AI analyst (Stage 1; TACT-Lite and TACT-Full)

## Purpose

Three AI analysts from three model families analyze the whole corpus independently, once per
research question, and propose candidate codes with cited evidence. Separate analyses broaden the
candidate space; one call per question stops the most salient question from crowding out the
others. Each call works through three analysis layers in order (semantic, latent, contrastive), so
that the report can say what the later layers found that a face-value reading would not. Every
proposal must be reviewable: a code carries a short label, a definition in respondents' own terms,
inclusion and exclusion rules, positive and negative examples, every supporting unit, and
verbatim representative quotes from at least three units, which a program checks against the
corpus (the provenance check). Units with no code are listed, never dropped silently.

## Who receives it, and what it sees

- Each of the three AI analysts (roles A, B, C; one model family each), once per research
  question, and once per discovery batch when the corpus is too long for the model's context
  window (`discovery_batch_size`).
- Sees: this brief and the corpus file (or one batch of it). Never sees another AI analyst's output.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{ANALYST}}` | AI analyst id (A, B or C) |
| `{{RQ_SECTION}}` | the research question for this call, its rationale, and the list of the other questions |
| `{{CORPUS_FILE}}`, `{{N_UNITS}}` | the corpus (or discovery batch) file and the number of units in it |
| `{{UNITS}}`, `{{UNIT}}`, `{{RESPONDENT}}`, `{{RESPONDENTS}}` | study vocabulary from config (`study.unit_name`, ...) |
| `{{CORPUS_DESCRIPTION}}` | `study.corpus_description` (plus a note on the batch, when the corpus is batched) |
| `{{EXAMPLE_UID}}`, `{{ID_PREFIX}}`, `{{RQ_ID}}` | an example unit id, the code id prefix (`<analyst>-<rq slug>`), the question id |
| `{{OUTPUT_PATH}}` | where the file goes, e.g. `discovery/v0/per_reading/analyst_A_RQ1.json` |
| `{{MAX_LABEL_WORDS}}`, `{{MIN_SUPPORT}}` | thresholds (14 words; 3 respondents) |
| `CONTEXT` (condition) | true when the corpus has a `context` column |

## Output schema

One JSON object, saved to `{{OUTPUT_PATH}}`, exactly as in the prompt below; `no_code` lists the
units with no code. The program (`council.py validate`, the provenance check) checks: `n_read` equals the number of
units supplied; every cited id exists; every quote is an exact, in-sequence substring of its cited
unit's text (a match only after normalizing whitespace, case or punctuation is reported but not
accepted); quoted units are in `participants`; no duplicate ids; at least `min(3, n_participants)`
quotes from distinct units; `layer` is one of `semantic`, `latent`, `contrastive`; positive
examples are cited units and negative examples are not (missing examples are reported as
warnings); every unit is either cited by a code or listed in `no_code`.

<!-- BEGIN PROMPT -->
# Discovery: AI analyst {{ANALYST}} (three analysis layers)

You are one of three AI analysts analyzing this corpus independently. You cannot see the other
two and must not guess what they will say; their differences are reconciled later.

## Research question for this call

{{RQ_SECTION}}

## The three analysis layers, in sequence

Analyze the WHOLE corpus at three analysis layers, in this order, and keep them apart. Every code
you return carries a `layer` field saying which layer produced it.

1. **semantic**: What {{RESPONDENTS}} say at face value, in their own terms. Group answers describing the same concrete thing. A {{RESPONDENT}} would recognise the code as a description of what they said.
2. **latent**: The assumptions or ways of working behind the answers: what has to be true for an answer to make sense. Answers worded differently can share a code, and answers worded alike can belong to different codes. Do not invent motives the text does not support.
3. **contrastive**: Where {{RESPONDENTS}}' answers diverge from their overall stance: conditions they set before they would act, boundaries, and positions on which they disagree. Prefer codes that separate people over codes everyone would accept.

Do the semantic layer first and write its codes down before starting the latent layer; do the
latent layer before the contrastive layer. A later layer may reuse units already coded in an
earlier layer; it must not restate an earlier code under a new label. If a later layer finds
nothing an earlier one did not, say so in `notes` rather than inventing codes. Two-unit codes
are reported honestly with `n_participants: 2`.

## The corpus

`{{CORPUS_FILE}}`: {{N_UNITS}} {{UNITS}}. {{CORPUS_DESCRIPTION}}
Each unit starts with its id in brackets (`[{{EXAMPLE_UID}}]`) on its own line. Analyze the whole file.
<!-- IF CONTEXT -->
Some units are followed by a line starting `CONTEXT:`. It holds the same {{RESPONDENT}}'s answer to a
complementary question. Read it only to understand an underspecified unit. Never code it, never
cite a unit for something only its CONTEXT says, and never quote from it.
<!-- ENDIF CONTEXT -->

## What you produce

One JSON object written to `{{OUTPUT_PATH}}`:

```json
{
  "analyst": "{{ANALYST}}",
  "lens": "analysis layers",
  "n_read": {{N_UNITS}},
  "codes": [
    {
      "id": "{{ID_PREFIX}}-01",
      "layer": "semantic", "rq": "{{RQ_ID}}",
      "label": "at most {{MAX_LABEL_WORDS}} words, in the {{RESPONDENTS}}' terms",
      "definition": "what this covers, one or two sentences, in the {{RESPONDENTS}}' terms",
      "include": "when the code applies",
      "exclude": "what looks similar and does not get this code, naming the neighbouring code id",
      "participants": ["{{EXAMPLE_UID}}"],
      "representative_quotes": [{"uid": "{{EXAMPLE_UID}}", "quote": "verbatim, trimmed to the relevant clause"}],
      "examples": {"positive": ["{{EXAMPLE_UID}}"], "negative": ["a unit that looks similar but does not get this code"]},
      "n_participants": 1,
      "candidate_theme": "T1"
    }
  ],
  "candidate_themes": [{"theme_id": "T1", "label": "optional grouping", "codes": ["{{ID_PREFIX}}-01"]}],
  "no_code": [],
  "notes": "what each analysis layer added; anything the reconciler should know"
}
```

## Rules

- **Analyze every unit before proposing anything.** Set `n_read` to the number of units you
  actually read; it is checked against the corpus size.
- **Every code carries its unit ids** (`participants`): every unit that supports the code. A code
  without units behind it is not a code.
- **Label**: short, verb-led or noun-phrase, no method jargon, at most {{MAX_LABEL_WORDS}} words, in the
  {{RESPONDENTS}}' terms; a {{RESPONDENT}} who wrote the {{UNIT}} would recognise it as a description of what they said.
  Do not restate the research question as a code.
- **Definition** in the {{RESPONDENTS}}' terms; **include** (the inclusion rule: when the code applies);
  **exclude** (the exclusion rule: what looks similar and does not get this code, naming the
  neighbouring code by id).
- **Positive and negative examples** (`examples`): one to three positive examples (unit ids from
  this code's `participants` that show the code clearly) and one to three negative examples (unit
  ids of units that look similar but fall under the exclusion rule; never units you cite for the
  code). Researchers verify them, and they give the AI coders context later.
- **Representative quotes** (`representative_quotes`): at least 3, from at least 3 different units, each
  **verbatim** from the unit's text: copy the characters exactly (same case, punctuation and
  spacing), trim to a clause, never paraphrase or stitch fragments (use `...` only to elide within
  one unit, in order). A program checks every quote for an exact match.
- Every quote's unit id must be in that code's `participants` list. No duplicates. Never pad.
- **A unit may take several codes, or none.** Two units is still a code: report it honestly
  with `n_participants: 2`; the minimum of {{MIN_SUPPORT}} respondents per code is applied at reconciliation, not by you.
- **`no_code` lists the units with no code: nothing in them bears on {{RQ_ID}}.** Every unit is either
  cited by a code or listed there; never drop a unit silently.
- Keep meaningfully different or opposing positions in separate codes.
- Optional `candidate_themes` grouping codes; every referenced code id must exist.
- **Ids**: `{{ID_PREFIX}}-01`, `{{ID_PREFIX}}-02`, ...  Unit ids are exactly as printed, e.g. `{{EXAMPLE_UID}}`.
- **`layer`** is one of `semantic`, `latent`, `contrastive` and is required on every code.
- Return one JSON object and nothing else. Write it to the file named above; do not write
  or read any other file in `discovery/`.

## What this is for

The three AI analysts' codes are reconciled on shared units (not on wording), reviewed by
researchers against their evidence, then applied by three AI coders. Cite evidence for every code.
The `layer` field lets the report say what the later analysis layers found that the first did not.
<!-- END PROMPT -->

## Follow-up instructions (sent by the program with the same brief)

The provenance check (`council.py validate`) returns failures to the AI analyst at most
`max_repairs` times (default 2), and returns unaccounted units once. The program sends the brief
again, with the analyst's own file, the corpus, and one of these instructions.

<!-- BEGIN INSTRUCTION completeness -->
Your file accounts for {{N_ACCOUNTED}} of the {{N_UNITS}} units. The brief requires every unit to be analyzed and either cited by a code or listed in `no_code` (units with no code). The units below are neither. Read each one; add it to the participants of an existing code it fits (with a representative quote if the code needs one), propose new codes where the units share something no code covers, or list it in `no_code`. Keep every existing code unless a unit shows it is wrong. Return the complete revised file under the key `{{OUTPUT_PATH}}`.

{{UNIT_IDS}}
<!-- END INSTRUCTION completeness -->

<!-- BEGIN INSTRUCTION repair -->
Your discovery file failed the provenance check with the errors below. Fix every error (copy quotes character for character from the cited unit; cite only units that exist; quote only units in the code's participants; take positive examples from the code's participants and negative examples from units it does not cite; remove duplicate ids) and return the complete corrected file under the key `{{OUTPUT_PATH}}`.

{{ERRORS}}
<!-- END INSTRUCTION repair -->
