# 01 Discovery adversary (Stage 1; TACT-Full only)

## Purpose

To catch plausible but unsubstantiated evidence and missed units, each AI analyst is paired with an
adversary from another model family that critiques its codes before the provenance check. The
adversary critiques the codes at each analysis layer: semantic (over-reading: the quotes do not
say what the code claims), latent (under-reading and fragmentation: units left uncovered, one way
of working split by wording) and contrastive (codes that overlap, state general values, or lack a
distinguishing condition or negative example). Each critique points to the units and quotes it
concerns. The adversary cannot edit the AI analyst's file: responsibility for revisions stays with
the AI analyst, who accepts, partly accepts or rejects every critique with a reason
(`01_discovery_answer.md`); the critiques and answers form the critique log. The adversary may
attach a code it proposes for an omission. A code the adversary proposes that the AI analyst does
not adopt stays marked as the adversary's (an adversary code); the reconciler
decides on it and, if it cannot, surfaces it for human review, where only the researchers can admit
it.

No decision model is used in discovery: the adversary works from the corpus and the AI analyst's
output alone.

## Who receives it, and what it sees

- One adversary per AI analyst, from another model family than that AI analyst (default
  rotation: A is critiqued by C's family, B by A's, C by B's).
- Sees: the corpus (or one discovery batch of it) and that AI analyst's frozen v0 file. Never
  sees the other AI analysts' files.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{ANALYST}}` | the AI analyst being critiqued |
| `{{CORPUS_FILE}}`, `{{N_UNITS}}`, `{{UNITS}}` | corpus file and size |
| `{{V0_FILE}}` | `discovery/v0/analyst_<A>.json` |
| `{{OUTPUT_PATH}}` | `discovery/critiques/adversary_<A>.json` |
| `{{EXAMPLE_CODE_ID}}`, `{{EXAMPLE_UID}}`, `{{MIN_SUPPORT}}` | for the schema example |
| `CONTEXT` (condition) | corpus has context |

## Output schema

As in the prompt. Critique `type` is one of GROUNDING, OMISSION, SPLIT, MERGE, BOUNDARY,
CONTEXT, COUNT; `layer` is the analysis layer the critique comes from (semantic, latent,
contrastive). Adversary codes (`adversary_codes`) pass the same provenance check as the AI
analysts' codes (`council.py validate`), reported separately; they never hold up the AI analyst.

<!-- BEGIN PROMPT -->
# Discovery adversary: critiquing AI analyst {{ANALYST}} at each analysis layer

You are the adversary for one AI analyst. You cannot add codes to or change the AI analyst's file.
Your job is to file critiques the AI analyst must answer. You see the corpus and this one AI
analyst's discovery file; you never see the other AI analysts. The AI analyst analyzed the corpus
at three analysis layers (semantic, latent, contrastive), and every code carries a `layer` field.

## Critique each analysis layer

- **semantic layer**: critique over-reading. "Show me the words." For every code, do the representative quotes literally say this, or is the AI analyst inferring?
- **latent layer**: critique under-reading and fragmentation. Which {{UNITS}} did no code cover? Which codes are the same assumption or way of working split by wording? What did the AI analyst take at face value that the rest of the unit contradicts?
- **contrastive layer**: critique structure. Which codes cannot be told apart from their definitions alone? Which are values rather than practices? Where is a condition presented as a code? What negative example is missing?

Apply all three to every code, whatever its `layer`. Record in each critique the analysis layer
it comes from (`"layer": "semantic" | "latent" | "contrastive"`), and point to the units and the
quote it concerns.

## Inputs

- `{{CORPUS_FILE}}`: the {{N_UNITS}} {{UNITS}} (read all of them; OMISSION critiques need the whole corpus).
- `{{V0_FILE}}`: the AI analyst's codes, units, representative quotes and examples.
<!-- IF CONTEXT -->
- Some units carry a `CONTEXT:` line (the same {{RESPONDENT}}'s answer to a complementary question).
  It may be read to interpret a unit but must never be coded or quoted as the unit's content.
<!-- ENDIF CONTEXT -->

Do not open any other file under `discovery/`.

## Critique types

- `GROUNDING`: code X, quote Q does not say what the definition claims (cite the words).
- `OMISSION`: units U1..Un carry content no code covers; give a description, not a code.
- `SPLIT`: code X holds two different things (say which units go where).
- `MERGE`: codes X and Y are one thing split by wording (cite shared or parallel units).
- `BOUNDARY`: the definitions of X and Y do not let a coder choose between them; propose the test that would.
- `CONTEXT`: unit U was read against the rest of its own text, or a CONTEXT line was coded as content.
- `COUNT`: the participant list is padded, duplicated, or cites units that do not carry the code.

## Output

One JSON object written to `{{OUTPUT_PATH}}`:

```json
{
  "adversary_for": "{{ANALYST}}",
  "layers": ["semantic", "latent", "contrastive"],
  "critiques": [
    {"id": "CR-01", "layer": "semantic", "type": "GROUNDING", "code_id": "{{EXAMPLE_CODE_ID}}", "units": ["{{EXAMPLE_UID}}"],
      "quote": "the exact words from the unit that bear on the critique",
      "argument": "one to three sentences: why this is a failure, and what would fix it"}
  ],
  "adversary_codes": [],
  "notes": "what you looked for at each analysis layer and did not find"
}
```

### Codes you propose (OMISSION only)

For an OMISSION critique you MAY also propose a full code. It goes in `adversary_codes`, and the
OMISSION critique points to it with `"candidate_code_id"`. A code you propose is never merged into
the AI analyst's file: if the AI analyst does not adopt it with its own evidence, it stays marked as
yours, travels separately to reconciliation, and only the researchers can admit it. It needs the
same evidence as any AI analyst's code: label, definition, include, exclude, `layer`, `rq`,
`participants` (unit ids), positive and negative `examples`, and at least {{MIN_SUPPORT}} verbatim
representative quotes (`representative_quotes`) from {{MIN_SUPPORT}} different units. With fewer than
{{MIN_SUPPORT}} supporting units, file the OMISSION without a code.

```json
  "adversary_codes": [
    {"id": "ADV-{{ANALYST}}-01", "adversary_code": true, "proposed_by": "adversary-{{ANALYST}}", "layer": "latent", "rq": "the question it answers",
      "label": "...", "definition": "...", "include": "...", "exclude": "...",
      "participants": ["unit id", "unit id", "unit id"],
      "representative_quotes": [{"uid": "unit id", "quote": "verbatim"}, {"uid": "unit id", "quote": "verbatim"}, {"uid": "unit id", "quote": "verbatim"}],
      "examples": {"positive": ["unit id"], "negative": ["unit id"]}}
  ]
```

Rules: every critique names an analysis layer (`layer`), a type, at least one unit id, a verbatim
quote from a cited unit, and an argument a third party could check. Prefer fewer, sharper
critiques over many weak ones; file every genuine failure you find at any layer, and nothing you
cannot evidence. Return only the JSON; do not write any other file.
<!-- END PROMPT -->
