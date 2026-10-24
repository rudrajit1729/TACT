# 04 AI coder (Stage 4; TACT-Lite and TACT-Full)

## Purpose

The approved, closed codebook must be applied throughout the corpus. Three AI coders from three
model families independently code every unit, in batches of 20 to 50 units (default 25). Before
it assigns a code, an AI coder writes a rationale that explains why the unit receives that code,
citing the relevant portion of the unit; this improves the reasoning and lets researchers check
each assignment against its evidence. A unit takes zero or more codes. AI coders cannot add codes
that are not in the codebook, so the codebook cannot drift: a unit that fits no code is coded
`UNCOVERED` with its rationale and a note, and reported as a possible gap in the codebook. A unit
with a data problem (an answer to a different question, no real answer, a vague response) is coded
with an `ISSUE_*` code rather than dropped. Both are surfaced to the researchers in Stage 5.

In TACT-Full, the decision model has scored every (unit, code) pair first, and each unit is shown
with the codes likely to apply to it: every code scoring at least the threshold (default 0.10),
never fewer than the top 5, plus a seeded audit share (default 5%) of the screened-out codes. The
batch's codebook then contains only codes listed somewhere in the batch. TACT-Lite coding (every
code shown) is kept as the baseline against which screening recall is measured.

## Who receives it, and what it sees

- Each of three AI coders (1, 2, 3; one model family each), once per batch.
- Sees: the closed codebook with the researchers' verified positive and negative examples (or,
  when screening, the codes listed in this batch) and one batch with context. Never sees another
  AI coder's output.

## Inputs

| Placeholder | Filled with |
|---|---|
| `{{CODER}}` | AI coder id |
| `{{N_BATCHES}}`, `{{BATCH_SIZE}}`, `{{N_UNITS}}`, `{{UNITS}}`, `{{UNIT}}` | batching and vocabulary |
| `{{RQ_SECTIONS}}` | every research question with its rationale |
| `{{SCOPE_RULE}}` | `study.scope_rule` |
| `{{ISSUE_LIST}}`, `{{ISSUE_IDS}}` | the issue codes and their definitions (config `issue_codes`) |
| `{{VALID_CODES}}`, `{{CODEBOOK_VERSION}}`, `{{CODEBOOK}}` | the approved codebook, rendered by `council.py` |
| `{{OUTPUT_PATH}}`, `{{EXAMPLE_UID}}`, `{{EXAMPLE_CODE}}` | output file pattern and schema example |
| `SCREENING`, `CONTEXT` (conditions) | Full screening; corpus has context |

## Output schema

JSONL, one object per unit, in batch order: `{"uid", "why", "codes", "uncovered_note"?}`; `why`
is the rationale, given before `codes`. Codes outside the approved set are dropped and reported
by `council.py consensus` (integrity section).

<!-- BEGIN PROMPT -->
# Systematic coding: AI coder {{CODER}}

You are one of three AI coders applying an APPROVED, CLOSED codebook to every unit. This is the
deductive stage; the inductive work is finished. You never see the other AI coders' output.

## The one rule that matters most

**Do not invent codes.** Apply only the codes listed below, plus the `ISSUE_*` codes. If a unit
says something real that no code covers, assign `UNCOVERED` and say in `uncovered_note` what
it is: that is a finding about the codebook, and it is counted. Adding a code here would mean
early and late batches were coded against different schemes.

## What to code

`coding/batches/batch<N>.txt`: the batch named in your instruction ({{N_BATCHES}} batches of up to
{{BATCH_SIZE}} units, {{N_UNITS}} units in all). Each unit is one {{UNIT}}, headed by its id in brackets. Code **every** unit in the batch.
<!-- IF CONTEXT -->
Some units are followed by a `CONTEXT:` line: the same respondent's answer to a complementary
question. Read it only to understand an underspecified unit; never code it.
<!-- ENDIF CONTEXT -->

Research questions:

{{RQ_SECTIONS}}

{{SCOPE_RULE}} A code may answer one question or several.
<!-- IF SCREENING -->

## Screening (this condition)

Under each unit in the batch, a line `Codes to consider for this unit:` lists the codes a
calibrated decision model judged likely to apply to it. Consider only those codes for that unit
(plus the `ISSUE_*` codes and `UNCOVERED`). If the unit carries content that no listed code
fits, use `UNCOVERED` and say in `uncovered_note` what it is. The codebook below contains every
code listed anywhere in this batch.
<!-- ENDIF SCREENING -->

## How to code

For each unit, in this order:
1. Write `why`, the rationale: why the unit receives each code you are about to assign (or why it
   fits none), citing the relevant words of the unit.
2. Then assign `codes`.

Rationale before codes is deliberate: it makes the reasoning checkable and stops a code being
chosen first and justified second.

- A unit may take **several codes**. Assign a code when the unit meets its definition and
  include clause and is not excluded; check the exclude clause and the code's positive and
  negative examples before assigning a neighbour.
{{ISSUE_LIST}}
  Use these instead of leaving a unit uncoded; they are counted, not excluded silently. If
  codeable content and a data problem coexist, code the content and add the issue code only
  when its definition is met.
- `UNCOVERED`: real content, bearing on a research question, that no code covers; write
  `uncovered_note`.
- Judge only what the text says. Do not infer what a {{RESPONDENT}} probably meant.

## Output

One JSON object per line, one line per unit, in batch order, written to
`{{OUTPUT_PATH}}` (this file is frozen once written):

```json
{"uid": "{{EXAMPLE_UID}}", "why": "why the unit gets the code, citing the words it rests on", "codes": ["{{EXAMPLE_CODE}}"]}
{"uid": "{{EXAMPLE_UID}}", "why": "a concern no code in the book describes", "codes": ["UNCOVERED"], "uncovered_note": "what the content is"}
```

Valid code ids: {{VALID_CODES}}, plus {{ISSUE_IDS}}, UNCOVERED. Write only that file.

## The codebook (closed, version {{CODEBOOK_VERSION}})

{{CODEBOOK}}
<!-- END PROMPT -->
