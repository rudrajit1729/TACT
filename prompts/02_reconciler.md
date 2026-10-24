# 02 Reconciler (Stage 2; TACT-Lite and TACT-Full)

## Purpose

Three model families have already surfaced the candidate codes independently, so one reconciler
consolidates them; this is a consolidation rather than a discovery task. A program first builds the
overlap table: for each pair of codes from different AI analysts (within one research question),
the units both cite, Jaccard similarity and the overlap coefficient. The reconciler reads it
alongside each code's definition and representative quotes and proposes a merge plan that sorts the
codes into groups, each of which becomes one code of the candidate codebook, with a rationale per
group. It groups codes only when they share units and describe the same thing within one research
question, so reconciliation runs once per research question. Because an AI analyst may leave a
fitting unit uncited, low overlap alone does not rule out a merge. It records how groups relate
(equivalent, broader_than, narrower_than, overlaps, contrasts_with); opposite positions stay in
separate groups linked by `contrasts_with`. It does not apply the minimum number of respondents per
code: a program does that afterwards (`council.py reconcile-apply`), drops codes below it and lists
them, so that the researchers can restore any they consider important. It does not admit the codes
the adversaries proposed (TACT-Full); it only says how each relates to a group, so the researchers
can decide.

## Who receives it, and what it sees

- One reconciler (any model family), once per research question.
- Sees: the raw codes for this question that passed the provenance check (with units,
  definitions, include/exclude, representative quotes, examples, layer; in TACT-Full the AI
  analysts' revised codes, whose critique logs go to the researchers), the program-computed
  overlap table for cross-analyst pairs, and the codes the adversaries proposed for this question.
  The corpus is not included.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{RQ_LINE}}` | the question id and text for this call |
| `{{N_UNITS}}`, `{{UNITS}}` | corpus size and unit name |
| `{{N_RAW_CODES}}`, `{{N_OVERLAPS}}`, `{{N_ADVERSARY_CODES}}` | counts in this call's input |
| `{{GROUPS_MIN}}`, `{{GROUPS_MAX}}` | the consolidation guide (`reconciliation.groups_per_rq`, default 5 to 15) |
| `{{MIN_SUPPORT}}`, `{{MAX_LABEL_WORDS}}`, `{{RESPONDENTS}}` | thresholds (minimum respondents per code, label length) and vocabulary |

Input file (built by `council.py reconcile-prepare`): `reconciliation/input.json` for this
question, with `codes`, `overlap` and `adversary_codes`.

## Output schema

`reconciliation/merge_plan.json` as in the prompt. The program checks every raw key is placed
(orphans become their own groups and are reported as errors) and every group has a rationale,
keeps many-to-many provenance, normalizes relation-type synonyms, drops and lists codes below the
minimum respondents, and writes the candidate codebook.

<!-- BEGIN PROMPT -->
# Reconciliation: reconciler brief

Three AI analysts analyzed the same {{N_UNITS}} {{UNITS}} independently, each at three analysis
layers (semantic, latent, contrastive). Propose a merge plan: decide which of their codes are the
SAME code, sort them into groups (each group becomes one code of the candidate codebook), give each
group one label, one definition and a rationale, and record how the groups relate to each other.

This call reconciles only the {{N_RAW_CODES}} raw codes that answer {{RQ_LINE}}. Every group gets
this question's `rq`.

## Input

`reconciliation/input.json`

- `codes`: {{N_RAW_CODES}} raw codes keyed `<analyst>:<id>`, each with its units, definition,
  include/exclude, verbatim representative quotes (`representative_quotes`, already checked against the
  corpus by a program), proposed positive and negative examples, and the `layer` of the analysis
  layer that produced it (semantic, latent, contrastive). Layer is provenance, not a grouping
  rule: codes from different layers that name the same units and the same thing are one code.
- `overlap`: the overlap table, {{N_OVERLAPS}} cross-analyst pairs that share at least one unit,
  with `shared`, `only_a`, `only_b`, `jaccard` (Jaccard similarity: shared / units either code
  cites) and `overlap_coefficient` (shared / units the smaller code cites). This is
  **descriptive evidence**, not a rule: an AI analyst may leave a fitting unit uncited, so weigh
  it together with the definitions, the include/exclude clauses and the representative quotes,
  and do not rule out a merge on low overlap alone. Two codes worded differently that name the
  same units and whose definitions describe the same thing are one code; two worded alike that
  name different units are not. A high overlap coefficient with low Jaccard similarity usually
  means one code is narrower than the other: record that as a relation rather than forcing a merge.
- `adversary_codes`: {{N_ADVERSARY_CODES}} codes the discovery adversaries proposed (OMISSION
  critiques) that the AI analysts did not adopt, marked `adversary_code`. **Do not place them in
  groups.** For each, say in `adversary_code_assessment` which group it would be equivalent to or
  how it relates; if you cannot resolve it, say so in its `note`. The researchers decide on it at
  human review.

The corpus is not included in this call; judge units by the representative quotes and the unit
lists in the input.

## Output

`reconciliation/merge_plan.json`:

```json
{
  "groups": [
    {"group_id": "G01", "rq": "the question id",
      "label": "at most {{MAX_LABEL_WORDS}} words, in the {{RESPONDENTS}}' terms",
      "definition": "what it covers, one or two sentences",
      "include": "what counts",
      "exclude": "what looks similar and goes elsewhere, naming the other group's label",
      "members": ["A:A-RQ1-03", "B:B-RQ1-07", "C:C-RQ1-02"],
      "member_units": {"C:C-RQ1-02": ["unit ids of this member that belong here"]},
      "rationale": "required: the evidence (shared units, definitions, quotes) for this grouping, in one or two sentences"}
  ],
  "relations": [
    {"type": "broader_than", "from": "G01", "to": "G04", "note": "G04 is a sub-case of G01"},
    {"type": "contrasts_with", "from": "G02", "to": "G07", "note": "the opposite position"}
  ],
  "adversary_code_assessment": [
    {"key": "ADV:ADV-A-01", "relation": "equivalent", "to": "G03", "note": "..."}
  ],
  "notes": "what you could not resolve"
}
```

Relation types: `equivalent` (that is what a group is), `broader_than`, `narrower_than`,
`overlaps`, `contrasts_with`. Relations are between groups (`group_id`).

## Rules

- **Every raw code key appears in at least one group**, normally exactly one. A raw code that
  genuinely holds two things may be a member of two groups; then give `member_units` for it in
  each group (which of its units belong there). Provenance is kept many-to-many. Orphans are
  errors. A code you think worthless still gets its own group; the minimum of {{MIN_SUPPORT}}
  respondents per code is applied afterwards, by a program, which lists what it drops.
- **Each raw code carries `rq`, the research question its reading answered. Group only codes
  with the same `rq`, and give every group its `rq`.**
- **Group codes only when they share units and describe the same thing**: shared units,
  matching definitions and include/exclude, quotes saying the same thing. Never merge on similar
  wording alone. **Give every group a `rationale`.**
- **A single-analyst code may stand alone.** `n_analysts` is the strength signal, kept as provenance.
- **Aim for a codebook coders can apply: about {{GROUPS_MIN}} to {{GROUPS_MAX}} groups per research question.**
  Merge a narrower code into the broader group that covers it unless coders would need the
  distinction to answer the question; when you merge, record the narrower code in `relations` as
  `narrower_than` the group, so nothing is lost.
- **Preserve genuine disagreement.** Opposite positions are two groups joined by `contrasts_with`.
- **Do not invent codes.** Group only what the analysts proposed; a label must describe the
  members' units, not the research question.
- **No method jargon** in labels or definitions.

Return ONLY the JSON object.
<!-- END PROMPT -->
