# 04 AI coder's answer to the coding adversary (Stage 4; TACT-Full only)

## Purpose

The AI coder answers every critique (ACCEPT, REJECT with a reason, PARTIAL) and revises its
assignments for the batch. Its v0 file stays frozen; the revision is v1. Krippendorff's alpha is
computed on both: v0, before the coding adversaries' critiques (three independent AI coders), and
v1, after them.

## Who receives it, and what it sees

- The original AI coder (same model family and model), once per batch.
- Sees: the batch, its own frozen v0 file, the critiques, and the full codebook. Never sees
  another AI coder's files.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{CODER}}`, `{{VALID_CODES}}`, `{{ISSUE_IDS}}`, `{{CODEBOOK_VERSION}}`, `{{CODEBOOK}}` | as in 04_coder.md |
| `{{EXAMPLE_UID}}`, `{{EXAMPLE_CODE}}` | schema example |

## Output schema

Two outputs keyed by path, as in the prompt. The v1 file has the same format as v0.

<!-- BEGIN PROMPT -->
# AI coder {{CODER}}: answering the coding adversary

An adversary from another model family has critiqued your assignments. Answer every critique and
write your final assignments. Only your final assignments enter consensus.

## Inputs

- `coding/batches/batch<N>.txt`: the batch named in your instruction.
- `coding/v0/coder{{CODER}}_batch<N>.jsonl`: your assignments (frozen; do not modify).
- `coding/critiques/coder{{CODER}}_batch<N>.json`: the critiques (under the key `critiques`).
- The codebook below. Do not read any other AI coder's files.

## Outputs

1. `coding/answers/coder{{CODER}}_batch<N>.json`:

```json
{"coder": "{{CODER}}", "batch": 1,
  "answers": [{"critique_id": "CC-01", "answer": "ACCEPT", "reason": "one sentence", "revision": "{{EXAMPLE_UID}} += {{EXAMPLE_CODE}}"}]}
```

`ACCEPT` (you changed the assignment as asked), `REJECT` (reason: the definition is not met /
the exclude clause applies / the quote does not say that), `PARTIAL`.

2. `coding/v1/coder{{CODER}}_batch<N>.jsonl`: your final assignments, same format as your v0
   file, one line per unit in batch order, incorporating accepted changes. If you reject every
   critique it is a copy of your v0 file.

Valid code ids: {{VALID_CODES}}, plus {{ISSUE_IDS}}, UNCOVERED. Every line keeps a rationale
(`why`) written before its codes; update it where an assignment changed.
Write only these files.

## The codebook (closed, version {{CODEBOOK_VERSION}})

{{CODEBOOK}}
<!-- END PROMPT -->
