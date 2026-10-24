# 04 Coding adversary (Stage 4; TACT-Full only)

## Purpose

As in Stage 1, each AI coder is paired with an adversary from another model family that critiques
its assignments and omissions for one batch: rationales that fail a definition, missed
assignments, coded context, and missed issues. The adversary sees the full codebook (not the
screened subset), the batch and the AI coder's assignments. It sees nothing from the decision
model: the decision model is used only for screening before coding and for flagging
high-uncertainty assignments after consensus. The adversary cannot change assignments; the AI
coder answers each critique and revises its assignments (`04_coder_answer.md`). The AI coder's
original output stays frozen as `v0` and the revision is `v1`; Krippendorff's alpha is computed on
both.

## Who receives it, and what it sees

- One coding adversary per AI coder, from another model family than that AI coder, once per batch.
- Sees: the batch (every unit, with context), the AI coder's frozen v0 assignments for it, and the
  full codebook. Never sees another AI coder's file.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{CODER}}`, `{{UNIT}}` | AI coder id; unit name |
| `{{ISSUE_IDS}}`, `{{CODEBOOK_VERSION}}`, `{{CODEBOOK}}` | as in 04_coder.md |
| `{{EXAMPLE_UID}}`, `{{EXAMPLE_CODE}}` | schema example |
| `CONTEXT` (condition) | corpus has context |

## Output schema

`coding/critiques/coder<k>_batch<N>.json`, as in the prompt.

<!-- BEGIN PROMPT -->
# Coding adversary: critiquing AI coder {{CODER}}

You see one AI coder's assignments for one batch, with its rationales, the batch text and the
closed codebook. You cannot change assignments; you file critiques the AI coder must answer.

## Inputs

- `coding/batches/batch<N>.txt`: the batch named in your instruction.
- `coding/v0/coder{{CODER}}_batch<N>.jsonl`: AI coder {{CODER}}'s assignments and rationales (`why`) for it.
- The codebook below. Do not read any other AI coder's file.

## Critique types

- `FALSE_POSITIVE`: the unit was given code X but does not meet its definition or falls under
  its exclude clause; cite the definition clause it fails.
- `FALSE_NEGATIVE`: the unit meets code X and was not given it; cite the words in the unit.
- `ISSUE_MISSED`: the unit should have been flagged with an issue code ({{ISSUE_IDS}}), or was
  flagged with one but has codeable content.
<!-- IF CONTEXT -->
- `CONTEXT_CODED`: an assignment rests on the unit's `CONTEXT:` line rather than on the unit's
  own words.
<!-- ENDIF CONTEXT -->

## Output

`coding/critiques/coder{{CODER}}_batch<N>.json`:

```json
{
  "coder": "{{CODER}}", "batch": 1,
  "critiques": [
    {"id": "CC-01", "type": "FALSE_NEGATIVE", "uid": "{{EXAMPLE_UID}}", "code_id": "{{EXAMPLE_CODE}}",
      "quote": "the exact words from the unit", "argument": "why the definition is met (or not)"}
  ],
  "notes": "what you checked and found sound"
}
```

Check every unit. File every genuine failure you can evidence
against the codebook's words, and nothing else. Return ONLY the JSON.

## The codebook (closed, version {{CODEBOOK_VERSION}})

{{CODEBOOK}}
<!-- END PROMPT -->
