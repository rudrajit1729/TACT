# 01 Discovery AI analyst's answer to its adversary (Stage 1; TACT-Full only)

## Purpose

Responsibility for revisions stays with the AI analyst. It accepts (ACCEPT), partly accepts
(PARTIAL) or rejects (REJECT) every critique with a reason, and revises its own codes. The original
stays frozen as `v0`; the revision is `v1`, so the comparison is preserved, and the critique log
(critiques and answers) goes to the reconciler and then to the researchers. Citations move in both
directions under one rule: a citation is removed only when the unit clearly fails the definition
(naming the clause it fails), and added when the unit meets it. An adversary's doubt is a lead, not
a reason. A code the adversary proposes is never copied into the AI analyst's file; the AI analyst
may give a view on it or adopt the omission with its own code and evidence. An adversary code the
AI analyst does not adopt stays marked as the adversary's and goes to the reconciler and the
researchers.

## Who receives it, and what it sees

- The original AI analyst (same model family and model as its discovery call).
- Sees: its frozen v0 file, the critiques filed against it, and the corpus. Never sees other
  AI analysts' work.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{ANALYST}}`, `{{CORPUS_FILE}}`, `{{N_UNITS}}` | as in 01_discovery_analyst.md |
| `{{V0_FILE}}`, `{{CRITIQUES_FILE}}` | `discovery/v0/analyst_<A>.json`, `discovery/critiques/adversary_<A>.json` |
| `{{ANSWERS_PATH}}`, `{{DELTA_PATH}}` | `discovery/answers/answer_<A>.json`, `discovery/v1_delta/analyst_<A>.json` |

## Output schema

Two outputs, returned as one JSON object keyed by path. The second is a delta: the program
(`council.py apply-delta`) applies it to v0 to produce `discovery/v1/analyst_<A>.json`, which then
passes the same provenance check as v0 (with up to two repair rounds and one completeness round).

<!-- BEGIN PROMPT -->
# Answering the adversary: AI analyst {{ANALYST}} (three analysis layers)

An adversary from another model family has read your discovery file and filed critiques at each
analysis layer (semantic, latent, contrastive; the field `layer`). Answer every critique, then
revise your codes. You are still AI analyst {{ANALYST}}: same analysis layers, same rules as your
discovery brief, same corpus (`{{CORPUS_FILE}}`, {{N_UNITS}} units).

## Inputs

- `{{V0_FILE}}`: your file (frozen; do not modify it).
- `{{CRITIQUES_FILE}}`: the critiques (under the key `critiques`).
- `{{CORPUS_FILE}}`.

Do not open any other file under `discovery/`.

## The rule for citations

Remove a citation only when the unit clearly fails the code's definition or falls under its
exclude clause, and name the clause it fails in your answer. The adversary's doubt is a lead, not a
reason. Additions follow the same rule in the other direction: cite a unit when it meets the
definition.

## Outputs

1. `{{ANSWERS_PATH}}`: your answers to the critiques (with the critiques, the critique log):

```json
{
  "analyst": "{{ANALYST}}",
  "answers": [
    {"critique_id": "CR-01", "answer": "ACCEPT", "reason": "one or two sentences",
      "revision": "what changed in the file (code ids, units), or 'none'"}
  ]
}
```

`answer` is `ACCEPT` (you revised as asked), `REJECT` (give the reason; the critique is
wrong or unevidenced), or `PARTIAL` (you revised in part; say which part).

If the adversary proposed a code with an OMISSION critique, answer the critique as usual and add
`"adversary_code_view": "ENDORSE" | "OPPOSE" | "NEUTRAL"` with a reason. Do NOT copy the adversary's
code into your revised file, even if you endorse it: it stays marked as the adversary's, travels
separately, and only the researchers can admit it. You may instead adopt the OMISSION with your own
code (your own units and quotes), marked `"adopted_from_adversary": true`.

2. `{{DELTA_PATH}}`: your revision as a delta against your v0 file. A program applies it to v0
   to produce your v1 file:

```json
{
  "replace": ["complete code objects, same schema as the discovery file, for every code you changed or added"],
  "remove": ["ids of codes you removed"],
  "no_code_add": ["unit ids"],
  "no_code_remove": ["unit ids"]
}
```

Codes you leave untouched are not repeated. Every code in `replace` needs its `rq`, `layer`,
`participants`, positive and negative `examples` and verbatim representative quotes
(`representative_quotes`), the same evidence as any other code. A code adopted from an OMISSION critique
carries `"adopted_from_adversary": true`. If you reject every critique, every list is empty.

Rules: quotes verbatim (exact characters); quote ids in the participant list; no padding; two-unit
codes are reported honestly. Return only these two outputs.
<!-- END PROMPT -->

## Follow-up instructions (sent by the program with the same brief)

When the v1 file fails the provenance check, or leaves units neither cited nor listed in
`no_code`, the program sends the brief again with the corpus and the current v1 file, and one of
these instructions. The reply is again a delta, applied to the current v1.

<!-- BEGIN INSTRUCTION repair -->
Your revised file `{{V1_FILE}}` failed the provenance check with the errors below. Fix every error (copy quotes character for character from the cited unit; cite only units that exist; quote only units in the code's participants; remove duplicate ids). Return, under the key `{{DELTA_PATH}}`, a JSON object {"replace": [complete code objects for every code you changed or added], "remove": [ids of codes you removed], "no_code_add": [unit ids], "no_code_remove": [unit ids]}. Codes you leave untouched are not repeated.

{{ERRORS}}
<!-- END INSTRUCTION repair -->

<!-- BEGIN INSTRUCTION completeness -->
Your revised file `{{V1_FILE}}` accounts for {{N_ACCOUNTED}} of the {{N_UNITS}} units. Every unit must be either cited by a code or listed in `no_code`. The units below are neither. Read each one; add it to the participants of an existing code it fits (with a representative quote if the code needs one), propose new codes where the units share something no code covers, or list it in `no_code`. Return, under the key `{{DELTA_PATH}}`, a JSON object {"replace": [complete code objects for every code you changed or added], "remove": [], "no_code_add": [unit ids], "no_code_remove": []}.

{{UNIT_IDS}}
<!-- END INSTRUCTION completeness -->
