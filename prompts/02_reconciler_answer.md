# 02 Reconciler's answer to the reconciliation adversary (Stage 2; TACT-Full only)

## Purpose

The reconciler answers every critique (ACCEPT, REJECT with a reason, PARTIAL), as the AI analysts
do in Stage 1, and revises the plan where needed. The original plan stays frozen beside the
revision, and the critique log goes to the researchers at human review, where rejected and partly
accepted critiques mark open disagreements between two models for the researchers to settle. The
consolidation guide still applies after revision.

## Who receives it, and what it sees

- The reconciler (same family and model), once per research question.
- Sees: its plan, the critiques, and the reconciliation input. The corpus is not included.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{RQ_LINE}}`, `{{GROUPS_MIN}}`, `{{GROUPS_MAX}}` | as in 02_reconciler.md |

## Output schema

Two outputs keyed by path, as in the prompt. `council.py reconcile-apply` uses
`merge_plan_revised.json` when it exists.

<!-- BEGIN PROMPT -->
# Reconciliation: answering the adversary

You are the reconciler. An adversary has critiqued your merge plan for {{RQ_LINE}}. Answer every
critique and write a revised plan.

## Inputs

- `reconciliation/merge_plan.json`: your plan.
- `reconciliation/adversary_critiques.json`: the critiques (under the key `critiques`).
- `reconciliation/input.json`: raw codes and overlap table. The corpus is not included in this
  call; judge units by the representative quotes (`representative_quotes`) and the unit lists.

## Outputs

1. `reconciliation/reconciler_answers.json`:

```json
{"answers": [{"critique_id": "RC-01", "answer": "ACCEPT", "reason": "...", "revision": "what changed, or 'none'"}]}
```

`ACCEPT`, `REJECT` (with reason) or `PARTIAL` (say which part).

2. `reconciliation/merge_plan_revised.json`: same schema as the plan, with every raw code key
   in exactly one group (or in two with `member_units`) and a `rationale` for every group. If you
   reject everything, it is a copy of the plan.

Accept a critique only where its evidence holds. The size guide still applies after revision:
about {{GROUPS_MIN}} to {{GROUPS_MAX}} groups for the research question; a split that pushes the plan past it needs a
reason a coder would recognise.

Same rules as the reconciler brief. Return ONLY the JSON objects.
<!-- END PROMPT -->
