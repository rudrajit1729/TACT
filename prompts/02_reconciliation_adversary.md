# 02 Reconciliation adversary (Stage 2; TACT-Full only)

## Purpose

Before the candidate codebook goes to human review, an adversary from another model family than
the reconciler critiques the merge plan. It checks whether the plan merged codes that should stay
apart (opposite positions, or codes that rest on few shared units), left apart codes that should be
merged, or let codes with support fall below the minimum respondents (they would be dropped). It
also flags labels that restate the question, missing members and wrong relations. It cannot change
the plan; the reconciler answers every critique (`02_reconciler_answer.md`) and revises the plan
where needed. Critiques that argue for merging are as welcome as those that argue for splitting, so
the adversary does not push the codebook only towards fragmentation. The original plan, the
revision and the critique log all go to the researchers. No decision model is used at
reconciliation.

## Who receives it, and what it sees

- One reconciliation adversary, from another model family than the reconciler, once per research
  question.
- Sees: the merge plan and the reconciliation input (raw codes, overlap table) for this question.
  The corpus is not included.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{RQ_LINE}}` | the question for this call |
| `{{N_RAW_CODES}}`, `{{N_OVERLAPS}}` | counts in this call's input |
| `{{MIN_SUPPORT}}` | the minimum respondents per code (3) |

## Output schema

`reconciliation/adversary_critiques.json`, as in the prompt.

<!-- BEGIN PROMPT -->
# Reconciliation adversary

You critique the reconciler's merge plan. You cannot change it; you file critiques the
reconciler must answer. The plan covers the codes answering {{RQ_LINE}}.

## Inputs

- `reconciliation/merge_plan.json`: the plan (`groups` with `members` = raw code keys).
- `reconciliation/input.json`: the {{N_RAW_CODES}} raw codes and the {{N_OVERLAPS}}-pair overlap table.

The corpus is not included in this call; judge units by the representative quotes
(`representative_quotes`, checked against the corpus by a program) and the unit lists in the input. Do not
read anything else.

## What to look for

- `LOW_OVERLAP_MERGE`: members merged that rest on few shared units and whose definitions and
  quotes do not show the same thing (cite the pair's shared / only-a / only-b / Jaccard / overlap
  coefficient from the overlap table). Low overlap alone is not enough: an AI analyst may leave a
  fitting unit uncited.
- `AVERAGED_OPPOSITES`: a group whose members take opposite positions or describe different
  problems, now averaged under one label.
- `DROPPED_DESPITE_SUPPORT`: a code with support left alone (for example a single-analyst code
  that shares units with a group it should have joined), so that it falls below the minimum of
  {{MIN_SUPPORT}} respondents and is dropped.
- `LABEL_RESTATES_QUESTION`: a label or definition that restates the research question or a
  layer instead of describing what the units say.
- `MISSING_MEMBER`: a raw code key absent from every group, or in two groups without `member_units`.
- `MISSED_MERGE`: two or more groups that are the same code (same units, definitions a coder could
  not tell apart); name them and the shared evidence. Critique over-splitting as readily as
  over-merging: a codebook that is too fine is as wrong as one that is too coarse.
- `WRONG_RELATION`: a recorded relation (`broader_than`, `narrower_than`, `overlaps`,
  `contrasts_with`) the units do not support, or a relation the plan should have recorded
  instead of a merge (or instead of two unrelated groups).

## Output

`reconciliation/adversary_critiques.json`:

```json
{
  "critiques": [
    {"id": "RC-01", "type": "LOW_OVERLAP_MERGE", "group_label": "the group's label",
      "members": ["A:A-RQ1-03", "B:B-RQ1-07"], "units": ["unit ids"],
      "evidence": "the overlap numbers or the quoted words",
      "argument": "why this is wrong and what the fix is"}
  ],
  "notes": "what you checked and found sound"
}
```

File every genuine failure you can evidence and nothing else. Return ONLY the JSON.
<!-- END PROMPT -->
