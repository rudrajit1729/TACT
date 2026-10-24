# Decision-model questions (TACT-Full only)

## Purpose

Verbalized confidence from a generative model is not a calibrated probability. In TACT-Full, a
decision model trained to return calibrated probabilities (TypeSafe's Jev) answers one yes/no
question with a score between 0 and 1: how likely each code is to apply to each unit, judged from
the code's definition and its inclusion and exclusion rules. These scores serve two purposes only,
both at coding: before coding, each AI coder sees only the codes likely to apply to a unit
(screening); after coding, consensus assignments that the decision model scored low are flagged as
high-uncertainty assignments for the researchers to review. The decision model never writes text,
never changes the codebook and never votes; every assignment still rests on an AI coder's rationale.
It is not used in discovery, at reconciliation, or by the coding adversaries. Any model with the
same contract (one probability of "yes" per question, from fixed state) can take Jev's place.

## Where it is used, and the thresholds (config `thresholds`)

The researchers fix these thresholds in preparation (Stage 0), before any model runs.

| Use | When | Question asked for | Threshold |
|---|---|---|---|
| Screening | Stage 4, after the codebook is approved, before coding | every (unit, approved code) pair | an AI coder sees every code scoring at least `screening_tau` (0.10), never fewer than the top `screening_top_k` (5), plus a seeded `screening_audit_share` (5%) of the screened-out (unit, code) pairs, shown anyway so that codes screening hid can be checked |
| High-uncertainty assignments | Stage 5, after consensus | the same scores, read for every consensus assignment | a consensus assignment scored below `high_uncertainty_below` (0.25), i.e. less than a one-in-four probability that the code applies, is flagged for the researchers' review (spot-check packet); it stays in the coded corpus unless the researchers remove it |

Screening recall is measured against TACT-Lite coding of the same corpus (`council.py report`).

## The question

Both uses read the same scores: one question per code, with the unit as state. In the
experiment the wording was: "Does this Stack Overflow thread contain something a poster says about
GitHub Copilot that meets the definition of `code`, as its include and exclude clauses describe?"
The general template is below; `{{UNIT}}`, `{{RESPONDENT}}` and `{{TOPIC}}` come from
`study.unit_name`, `study.respondent_name` and `study.topic_phrase` (empty, or a phrase such as
" about GitHub Copilot" with a leading space).

<!-- BEGIN QUESTION code_applies -->
Does this {{UNIT}} contain something a {{RESPONDENT}} says{{TOPIC}} that meets the definition of `code`, as its include and exclude clauses describe?
<!-- END QUESTION code_applies -->

### Request (one per unit)

```json
{
  "state": {"unit_text": "the unit's text", "context": "the paired CONTEXT, when the corpus has it"},
  "questions": {
    "<code id>": {
      "question": "the question above",
      "code": {"label": "...", "definition": "...", "include": "...", "exclude": "...",
               "research_question": "the code's research question (omitted when decision_model.include_research_question is false)"}
    }
  }
}
```

The state key for the unit text is `decision_model.state_key` (default `unit_text`; the
experiment used `thread`). CONTEXT is interpretive only: the unit text is what is judged.

### Response

```json
{"<code id>": 0.83, "<code id>": 0.02}
```

One probability of "yes" in [0, 1] per question, or null when the model cannot answer. No text.

## Implementations

- `decision_model.backend: typesafe` (default): POST to `decision_model.endpoint` with
  `{"state": ..., "model": decision_model.model, "questions": {id: {"type": "noul", "instructions": {...}}}}`;
  the key is read from the environment variable named in `decision_model.api_key_env`
  (default `TYPESAFE_API_KEY`). The answer for each id is `answers[id].noul`.
- `decision_model.backend: command`: any program. The pipeline writes the request above as JSON on
  the program's stdin and reads the response above as JSON from its stdout. Use this to swap in
  another calibrated yes/no model (a fine-tuned classifier, a logprob-calibrated model, a local
  service). Validate it before use: the thresholds above were fixed for Jev; recalibrate them on a
  calibration sample (never on the held-out sample) when you change the model, the corpus or the
  codebook version, and report the per-code recall of screening.
- `decision_model.backend: manual`: each request is saved, with the instructions above, to
  `<workspace>/manual/<stage>__<role>__<uid>.prompt.md`; the reply (the response above) is saved
  next to it as `.reply.json`. For an agent-driven run without a decision model; the probabilities
  are not calibrated, and the report must say so.
- `decision_model.backend: replay` with `replay_dir`: answers from replies recorded from a manual run
  (`council.py export-replies`).

Every request is logged in `logs/calls.jsonl` (stage `jev-screen`, one request per unit at coding)
with the sha256 of the request, never the key.
