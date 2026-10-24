# Prompt index

Every model role reads one prompt file. The text a model receives is the part of the file between
`<!-- BEGIN PROMPT -->` and `<!-- END PROMPT -->`, with every `{{PLACEHOLDER}}` filled and every
`<!-- IF NAME -->` part kept only when NAME applies. `pipeline/council.py` and `pipeline/run.py`
render them from `config.yaml`; when you run without scripts, fill them yourself from the tables at the
top of each file. Rendered briefs are kept in `<workspace>/briefs/`, so a report can publish exactly
what each model received.

The input files a role may see are sent with the brief, each under a line `=== FILE: <path> ===`,
and the model returns one JSON object keyed by the output paths the brief names (see `SYSTEM` in
`pipeline/models.py`). A role never sees files outside its list: AI analysts never see each other,
AI coders never see each other, adversaries see only the role they critique. Each role's inputs
follow the paper's Table I (roles and their inputs).

## Variant x stage x role

| Stage | Role | TACT-Lite | TACT-Full | Prompt file | Called | Inputs | Output (in the workspace) |
|---|---|---|---|---|---|---|---|
| 0 Preparation | Program (no prompt) | yes | yes | `pipeline/council.py prepare` | once | the corpus CSV | `data/` (units, context, discovery batches, `splits.json` with the blind-pass and held-out samples and the seed) |
| 1 Discovery | AI analyst A, B, C | yes | yes | `01_discovery_analyst.md` | per AI analyst x research question (x discovery batch) | the corpus and the common prompt; no other AI analyst's output | `discovery/v0/per_reading/analyst_<A>_<RQ>.json`, merged to `discovery/v0/analyst_<A>.json` |
| 1 Discovery | AI analyst, provenance repair and completeness round | yes | yes | `01_discovery_analyst.md` (instructions `repair`, `completeness`) | when the provenance check fails (at most 2 repairs, 1 completeness round) | the corpus, its own file, the errors | same file, replaced |
| 1 Discovery | Discovery adversary (another model family) | | yes | `01_discovery_adversary.md` | per AI analyst (x discovery batch) | the corpus, one AI analyst's output (no decision model) | `discovery/critiques/adversary_<A>.json` |
| 1 Discovery | AI analyst's answer | | yes | `01_discovery_answer.md` (+ instructions `repair`, `completeness` for v1) | per AI analyst (x discovery batch) | the corpus, its own output, the critiques | `discovery/answers/answer_<A>.json`, `discovery/v1_delta/analyst_<A>.json` -> `discovery/v1/analyst_<A>.json` |
| 2 Reconciliation | Reconciler | yes | yes | `02_reconciler.md` | per research question | the codes that passed the provenance check (Full: with the adversary codes), the overlap table | `reconciliation/<cond>/per_rq/<RQ>/merge_plan.json` |
| 2 Reconciliation | Reconciliation adversary (another model family) | | yes | `02_reconciliation_adversary.md` | per research question | the merge plan, candidate codes and overlap table | `.../adversary_critiques.json` |
| 2 Reconciliation | Reconciler's answer | | yes | `02_reconciler_answer.md` | per research question | the plan, the critiques, the input | `.../reconciler_answers.json`, `.../merge_plan_revised.json` |
| 3 Human review | Researchers (no prompt) | yes | yes | `pipeline/human.py review-dashboard` | once, after the blind pass | all stage outputs and critique logs | `codebooks/review_edits.json` -> `approved_codebook.json` |
| 4 Coding | AI coder 1, 2, 3 (every code shown) | yes | yes (TACT-Lite baseline) | `04_coder.md` | per AI coder x batch | the approved codebook and a batch with context | `coding/L/coder<k>_batch<n>.jsonl` |
| 4 Coding | Decision model: screening | | yes | `decision_model_questions.md` | per unit x every approved code | one unit, every code | `coding/jev/screen.json` |
| 4 Coding | AI coder, screened (`SCREENING` part on) | | yes | `04_coder.md` | per AI coder x batch | the approved codebook and a batch, with the screened codes per unit | `coding/LJ/coder<k>_batch<n>.jsonl` (v0) |
| 4 Coding | Coding adversary (another model family) | | yes | `04_coding_adversary.md` | per AI coder x batch | one AI coder's batch and assignments, the codebook (no decision model) | `coding/LJA/critiques/coder<k>_batch<n>.json` |
| 4 Coding | AI coder's answer | | yes | `04_coder_answer.md` | per AI coder x batch | the batch, its assignments, the critiques, the codebook | `coding/LJA/answers/...`, `coding/LJA/coder<k>_batch<n>.jsonl` (v1) |
| 5 Reliability and consensus | Program (no prompt) | yes | yes | `pipeline/council.py consensus` | per condition | all AI coders' final assignments (Full: and the screening scores, for the high-uncertainty flags) | `results/<cond>/` |

`<cond>` is `lite` or `full` at reconciliation; at coding, the conditions are `L` (TACT-Lite), `LJ`
(screened, v0, before the coding adversaries' critiques) and `LJA` (v1, after them). In TACT-Full
with the decision model switched off, the adversaries critique `L` and write `LA`.

## Model family rule

Three AI analysts and three AI coders come from three model families. Each adversary comes from
another model family than the role it critiques (default rotation: A by C's family, B by A's, C by
B's; the same for AI coders 1, 2, 3). The reconciler may be any model family; its adversary is
another model family.

## Reasoning settings

Discovery (with its repairs and answers) and reconciliation (with its answers) run at each model's
default reasoning; every other generative call runs with reasoning reduced
(`reasoning.default_stages`, `reasoning.reduced_effort`).

## Validation corpus

`examples/zhang2023/config.yaml` fills the placeholders with the paper's validation study: Zhang et
al.'s five research questions with their goals and rationales, the Stack Overflow unit and respondent
names, and the scope rule.
