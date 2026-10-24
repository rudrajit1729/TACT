# AGENTS.md: operating the council pipeline

Instructions for a coding agent (Claude Code, Codex, or any agent that can run shell commands) asked
to run the bounded AI council on a user's corpus. Follow them in order. Where this file says STOP,
stop and pass control to the user; do not continue past a human step on your own.

**If the user wants to see real results without running any model**, point them to the paper's run
on 256 Stack Overflow threads: `examples/zhang2023/dashboard_lite.html` and
`examples/zhang2023/dashboard_full.html` (README, "Reproduce the paper's validation").

**Before a real run, run `doctor` first** and ask the user only for what it reports missing:

```bash
python3 pipeline/council.py --config config.yaml doctor      # or with no --config before a config exists
```

It checks Python, the config, each family's CLI login or API key variable (it reports only whether
the variable is set, never its value), the decision model, the corpus and the workspace, and prints
the fix for each FAIL. Relay each fix to the user in plain words and point them to the matching
section of `SETUP.md` (how to get a key, set it on their system, or log in to a CLI). Do not ask for
anything `doctor` shows as PASS. Never ask the user to paste a key into the chat or a file: they set
it in their own terminal. When nothing fails, run `doctor --ping` once, but only after telling the
user that it sends one tiny paid request per family.

## 0. Rules that hold throughout

1. **Programs decide what is deterministic.** The Stage 0 samples, provenance checks, the minimum
   respondents per code, consensus, reliability and the alpha rule are computed by `pipeline/council.py`. Never compute or "fix" them by
   judgment, and never edit a model's output to make a check pass; send it back to the model (the
   scripts do this) or report the failure.
2. **Isolation.** AI analysts never see each other's output; AI coders never see each other's output; an
   adversary sees only the role it critiques. Each model call is a fresh, stateless session with
   exactly the files its prompt lists. If you answer prompts through sub-agents, start a new one per
   prompt.
3. **Model families.** Three AI analysts and three AI coders come from three model families. An adversary comes
   from another model family than the role it critiques. Do not answer a role yourself unless you are that
   role's family, and then only in a fresh context.
4. **Frozen files stay frozen.** `discovery/v0/` and the v0 coding (`coding/L`, `coding/LJ`) are
   read-only after `freeze`; revisions go to v1. Never overwrite `codebooks/approved_codebook.json`
   once coding has started; codebook versions are never mixed.
5. **Humans first, models second, where the method says so.** The blind pass (on the blind-pass
   sample drawn in Stage 0) is done before any researcher sees model output. Never show a researcher
   a discovery file, codebook, critique log or dashboard before they have returned their blind pass.
   Never show model assignments to the researchers coding the held-out sample.
6. **Secrets.** Keys stay in environment variables. Never print, read, copy or write a key (do not
   open shell profiles to look for one, and do not ask the user to paste one into the chat). The
   config holds only the variable's name; `doctor` tells you whether it is set.
7. **Data governance.** Before the first model call, confirm with the user that the corpus is
   de-identified and that consent terms allow every model provider in the config, and record this under
   `data_governance`.
8. **Never invent.** No codes, quotes, units, labels or numbers that the artifacts do not contain.
   Never write a human-derived number (blind pass, review, held-out agreement, spot-check) before the
   researchers have produced it.

## 1. Ask the user for these inputs

Do not start until you have all of them. Put them in `config.yaml` (copy `config.example.yaml`).
Run `doctor` first (above): what it already finds (installed and logged-in CLIs, key variables that
are set) needs no question; ask only for the rest.

| Input | Config key | Notes |
|---|---|---|
| Variant | `mode` | `lite` or `full` (TACT-Full = adversaries + decision model). |
| Corpus | `study.corpus_csv` | CSV with `uid,text`; optional `context` (same respondent's other answers; read, never coded), `respondent` (who wrote the unit, when one respondent wrote several; the minimum support counts distinct respondents), `question`, `stratum` (used to stratify the samples), `link`. De-identified. |
| Thresholds | `thresholds`, `splits` | Fixed before any model runs. Defaults: minimum 3 distinct respondents per code (`support_floor`); Krippendorff's alpha threshold 0.7 (`alpha_drop`; raise to 0.8 for conservative conclusions); TACT-Full screening 0.10, top 5, 5% audit; high-uncertainty below 0.25. Blind-pass sample 10% (50 to 150); held-out sample at least 10%. |
| Research questions | `study.research_questions` | `id`, `text`, optional `rationale` (what the question means), optional `slug`. |
| Corpus description and vocabulary | `study.corpus_description`, `unit_name(_plural)`, `respondent_name(_plural)`, `scope_rule`, `topic_phrase` | One or two sentences the AI analysts read; the extraction rule all roles apply. |
| Issue codes | `issue_codes` | Defaults: wrong field, back-reference, non-response. Add study-specific ones if needed. |
| Model families available | `roles`, `models` | Which three model families, through which CLI or API, with which model ids; the env var NAME of each API key. If only two families are available, say so and record the model provider caveat. `SETUP.md`, section 1, shows the user how to set each one up. |
| Decision model (TACT-Full) | `decision_model` | Jev (env var name of the key), a `command` with the same contract, `manual` (each request is saved to `<workspace>/manual/` for you or the user to answer; not calibrated), or `enabled: false`. Used only at coding (screening, high-uncertainty flags). `SETUP.md`, section 3. |
| Researchers | (your notes) | At least two people for the blind pass, human review, held-out coding and spot-check. |
| Data governance | `data_governance` | What leaves the machine, to which model providers, under which terms. |
| Prices (optional) | `prices` | USD per million input and output tokens per model id, dated. |

Then run, and fix every FAIL and ERROR they print (missing corpus, placeholder model ids, a family
without a `models` entry, an adversary from the same family, an unknown backend, a key variable that
is not set, a CLI that is not logged in):

```bash
python3 pipeline/council.py --config config.yaml doctor
python3 pipeline/council.py --config config.yaml status
```
`status` also prints the next command to run; `status --json` gives the same for programs.

## 2. Choose how model calls are made

- **Route A, scripted (recommended).** Set each family's `backend` to `claude_cli`, `codex_cli`,
  `anthropic_api`, `openai_api`, `gemini_api` or `command`. `pipeline/run.py` makes every call, logs
  it, and runs the checks.
- **Route B, manual or agent-answered.** Set a family's `backend: manual` (and `answered_by:` the
  model that will answer). `run.py` writes each prompt it needs to
  `<workspace>/manual/<stage>__<role>__<batch>.prompt.md` and exits with status 3. For each prompt:
  send the whole file, in a fresh session, to a model of the right family (for example
  `claude -p < X.prompt.md > X.reply.json`, `codex exec - < X.prompt.md`, or a new sub-agent of that
  family); save the model's reply, unedited, as `<same name>.reply.json` next to the prompt; then
  rerun the same `run.py` command. Repeat until it finishes. The reply must be one JSON object keyed by
  the output paths the prompt names (for a `.jsonl` output, the value is a list of objects).
  What to expect:
  - Every prompt that can be prepared at once is prepared at once (all discovery calls, all batches); prompts
    that depend on a reply (an adversary needs the AI coder's file; an answer needs the critiques)
    appear only after you rerun.
  - Repair and completeness rounds get numbered names (`...__a1`, `...__a2`); each is a new prompt.
    Its `=== INSTRUCTION ===` section says what to fix; the reply is the complete corrected file
    (discovery v0) or a delta (discovery v1), as the instruction says.
  - With `decision_model.backend: manual`, each decision-model request is a prompt too
    (`jev-screen__coders__<uid>`): one unit and every approved code; the reply is
    `{"<code id>": probability, ...}`. There is one per unit, at coding only, and the probabilities are
    not calibrated; say so in the report.
  - To keep a manual run so that it can be replayed with no model access (for an audit):
    `python3 pipeline/council.py --config config.yaml export-replies --to replay`, then point a copy
    of the config at it with `backend: replay` and `replay_dir: replay` (models and decision model).
- **Route C, no scripts for model calls.** Possible but discouraged: section 6 lists, per role, the
  prompt file, its inputs and its output; you must still run every deterministic command listed there.

## 3. Stage by stage

`CFG` below stands for `--config config.yaml`. After every step, run `council.py CFG status`.

### Stage 0: data preparation

Before this, the researchers have fixed the thresholds and stated the research questions (section 1).

```bash
python3 pipeline/council.py CFG prepare
```
What it does: gives every unit a stable id, attaches context, splits a long corpus into discovery
batches, and draws two separate random samples, stratified by question, recording the seed in
`data/splits.json`: the **blind-pass sample** (10% of units, at least 50, at most 150) and the
**held-out sample** (at least 10% of units, drawn from the units outside the blind-pass sample).
Check: the printout gives units, the two sample sizes, the seed and the number of discovery batches.
Set `discovery_batch_size` (and rerun with `--force` before any model call) if the corpus does not fit
the AI analysts' context windows; never truncate. (The validation option, for validating the method
itself as the paper did: a config with `splits.validation_development_share` above 0 also splits the
units into reserved and evaluation units.)

```bash
python3 pipeline/human.py CFG blind-pass
```
**STOP 1 (can run in parallel with Stage 1).** Tell the user: give `human/01_blind_pass/` to at least
two researchers now, before anyone sees model output. You may continue with the model stages, but do
not show any output to those researchers until they have returned their blind pass.

### Stage 1: discovery

```bash
python3 pipeline/run.py CFG discovery
```
What it does: one call per AI analyst x research question (x discovery batch) with
`prompts/01_discovery_analyst.md`, at three analysis layers (semantic, latent, contrastive); per code
a label, definition, inclusion and exclusion rules, positive and negative examples, cited units and
representative quotes from at least three units; units with no code listed. Then the provenance check
on each call's file (cited ids exist; quotes are exact, in-sequence substrings of the cited unit's
text; quoted units are in the support list; no duplicates; enough quotes; examples consistent with
the cited units; `n_read` equals the units supplied; no unit skipped); up to `max_repairs` repair
calls and one completeness round per call; merge per AI analyst into `discovery/v0/analyst_<A>.json`;
validate; freeze.
Checks:
- `discovery/validation/v0_analyst_<A>.json` has `"status": "PASS"` for A, B, C.
- `discovery/validation/repairs.json`: note repairs and units unaccounted before and after the
  completeness round per call (they are reported).
- If a call's file FAILs after the repairs, stop and report the errors to the user. Nothing with an error
  goes to reconciliation.

**TACT-Full only:**
```bash
python3 pipeline/run.py CFG discovery-adversary
```
What it does: one adversary per AI analyst from another model family (`prompts/01_discovery_adversary.md`)
receives the corpus and that AI analyst's codes, and critiques them at each analysis layer, pointing
to the units and quotes each critique concerns; no decision model is used in discovery. The AI analyst
accepts, partly accepts or rejects each critique with a reason (`prompts/01_discovery_answer.md`) and
returns a delta that the program applies to v0 to make v1; the v1 file passes the same provenance
check (repairs as deltas). Codes the adversary proposed that the AI analyst did not adopt stay marked
as the adversary's (`adversary_codes`); they are checked, reported, and go to the reconciler and the
researchers.
Checks: `discovery/validation/v1_analyst_<A>.json` PASS for all three; every critique has an answer
(`discovery/answers/answer_<A>.json`).

### Stage 2: reconciliation

```bash
python3 pipeline/run.py CFG reconcile
```
What it does: builds the raw-code list and the overlap table for each pair of codes from different AI
analysts (shared units, units held alone, Jaccard similarity, overlap coefficient; same research question
only); one reconciler call per research question (`prompts/02_reconciler.md`), which returns a merge plan
with a rationale per group; in TACT-Full, the reconciliation adversary critiques the merge plan
(`02_reconciliation_adversary.md`) and the reconciler answers and revises (`02_reconciler_answer.md`), and
the TACT-Lite reconciliation on v0 also runs for comparison; then the program drops codes supported by
fewer than `support_floor` (3) distinct respondents and lists them (with their evidence) for possible
restoration, keeps many-to-many provenance, and writes `codebooks/candidate_<lite|full>.json`.
Checks: the printout of `reconcile-apply`; `errors` in the candidate codebook (orphans are placed as
their own groups and reported; groups that mix questions or lack a rationale are reported). Report them
to the user.

### Stage 3: human review (researchers)

Only after the researchers have returned their blind pass:

```bash
python3 pipeline/human.py CFG review-dashboard
```
**STOP 2.** Tell the user: each of at least two researchers opens
`human/03_human_review/codebook_review.html`, compares the codes with their own blind-pass codes,
reviews every code against its evidence, verifies and refines the positive and negative examples the
AI analysts proposed (never from the held-out sample), decides on the adversary codes
(TACT-Full) and on restoring codes dropped below the minimum respondents, and downloads their
decisions (Finish tab). Then:

```bash
python3 pipeline/human.py CFG review-to-edits review_<A>.json review_<B>.json
```
(With no file names it reads every `.json` in `human/03_human_review/returned/`, where the app puts
the reviewers' files.) This writes `codebooks/review_edits.draft.json` (edits both reviewers agree on) and
`human/03_human_review/review_comparison.md` (what to negotiate). The researchers meet, resolve every
item by negotiated agreement, and save the final edit log as `codebooks/review_edits.json`:

```json
{"reviewed_by": "R1, R2", "status_note": "...", "blind_pass_codes_missing": ["..."],
 "edits": [
  {"op": "relabel", "id": "T01", "label": "...", "definition": "...", "include": "...", "exclude": "...", "rq": "RQ2", "reason": "..."},
  {"op": "merge", "into": "T01", "from": ["T03"], "reason": "..."},
  {"op": "split", "id": "T05", "into": [{"id": "T05a", "label": "...", "definition": "...", "include": "...", "exclude": "...", "units": ["U1", "U2", "U3"]}, {"id": "T05b", "...": "..."}], "reason": "..."},
  {"op": "move", "units": ["U012"], "from": "T02", "to": "T05", "reason": "..."},
  {"op": "drop", "id": "T04", "reason": "..."},
  {"op": "add", "id": "T90", "rq": "RQ1", "label": "...", "definition": "...", "include": "...", "exclude": "...", "units": ["U1", "U2", "U3"], "reason": "..."},
  {"op": "examples", "id": "T01", "positive": ["U001"], "negative": ["U009"]},
  {"op": "restore", "group_id": "RQ1-G07", "id": "T95", "reason": "..."},
  {"op": "accept_adversary_code", "key": "ADV:ADV-A-01", "id": "T91", "reason": "..."},
  {"op": "reject_adversary_code", "key": "ADV:ADV-A-01", "reason": "..."},
  {"op": "relation", "type": "contrasts_with", "from": "T02", "to": "T07", "reason": "..."},
  {"op": "drop_relation", "from": "T02", "to": "T07", "type": "overlaps", "reason": "..."}]}
```

You may help the researchers turn their agreed decisions into this JSON; you may not decide for them.
Then:

```bash
python3 pipeline/council.py CFG approve        # writes codebooks/approved_codebook.json (version 1.0, closed)
```
Checks: the printout (codes approved, edits by type); warnings about fewer than two reviewers or codes
without verified positive or negative examples go to the user. Examples from the held-out sample are
ignored by the program. Only verified examples (an `examples` edit) reach the AI coders.

If review finds a gap that no candidate and its evidence can fill: copy `config.yaml` to a new file
with a new `workspace` and the reviewers' notes appended to `study.corpus_description`, run
`prepare`, `discovery` (and `discovery-adversary` in TACT-Full) and `reconcile` there, and bring the new
candidates to review as `add` edits (each with units from at least three respondents) before approving.

```bash
python3 pipeline/human.py CFG heldout-packet
```
**STOP 3 (can run in parallel with Stage 4).** Tell the user: at least two researchers code the
held-out sample in `human/05_heldout_coding/` independently, without seeing any model assignment,
resolve differences, and save one `resolved.csv`.

### Stage 4: coding (and Stage 5 consensus)

```bash
python3 pipeline/run.py CFG code
```
What it does: batches of `batch_size` (25) units; each AI coder writes a rationale before each
assignment, uses only the closed codebook, and codes `UNCOVERED` or `ISSUE_*` where needed. TACT-Lite
coding with every code shown (`prompts/04_coder.md`) goes into `coding/L`. TACT-Full adds decision-model
screening (`coding/jev/screen.json`, `coding/LJ/screening_plan.json`), screened coding into `coding/LJ`,
freeze, then per AI coder and batch the coding adversary (`04_coding_adversary.md`; it sees the batch,
the AI coder's assignments and the codebook, nothing from the decision model) and the AI coder's answer
(`04_coder_answer.md`) into `coding/LJA`. Then consensus for every condition.
Checks: warnings about units missing from an AI coder's batch; `integrity` in
`results/<cond>/summary.json` (invalid codes used, units missing per AI coder, parse problems). Report
them; do not patch AI coder files.

### Stage 5: consensus, reliability and the drop rule

`run.py code` already ran it; to rerun (for example after the spot-check):

```bash
python3 pipeline/council.py CFG consensus
```
What it computes, per condition (`L`; TACT-Full: `LJ` = v0, before the coding adversaries' critiques;
`LJA` = v1, after them):
- consensus: a code reaches consensus on a unit when at least 2 of 3 AI coders assign it; units that at
  least two AI coders code `ISSUE` are excluded from prevalence counts but kept in the file;
- per code, on the binary decision (on every unit; `reliability.units`): Krippendorff's alpha, pairwise
  Cohen's kappa with 2x2 tables, raw, positive and negative agreement; the mean kappa over AI coder
  pairs from different model families;
- the distribution: median, minimum, maximum, number below 0.7, number at or above 0.80 (no interval);
- **the alpha rule: every code with alpha below 0.7** goes back to the researchers with the units on
  which the AI coders disagreed (STOP 5 below); until they decide it is held out of prevalence and
  `consensus_retained.csv`, and it is listed with its definition and agreement counts in
  `results/<cond>/reliability_report.md`, with the researchers' decision once they have made it; codes
  with undefined alpha (no variation) are listed beside them and not reported;
- survival (pairs proposed by at least one AI coder that at least two assign); uncovered and issue counts;
- TACT-Full: consensus assignments the decision model scored below 0.25 (`high_uncertainty_below`) are
  flagged as high-uncertainty assignments for the researchers' review; they stay in the coded corpus
  unless the researchers' spot-check removes them.
The results of the run are the primary condition: `L` in TACT-Lite, `LJA` in TACT-Full.

```bash
python3 pipeline/human.py CFG spot-check
```
**STOP 4.** Tell the user: at least two researchers spot-check the random sample of rationales in
`human/05_spot_check/spot_check.csv` against the codebook, review the units coded `ISSUE` or
`UNCOVERED` and (TACT-Full) the high-uncertainty assignments, fill `keep` and `note`, and save the
agreed file as `human/05_spot_check/decisions.csv`; report the sample size. Then rerun `consensus`.
(`keep = n` on a high-uncertainty assignment removes it from the coded corpus; on any other row it is
recorded and counted in the report, and consensus is unchanged.)

```bash
python3 pipeline/human.py CFG low-alpha
```
**STOP 5.** If any code is below the alpha threshold, tell the user: the researchers read
`human/06_low_alpha/low_alpha_codes.md` (each code's definition and every unit the AI coders disagreed
on) and decide, per code, `drop`, `refine` or `keep` (with a reason), in `human/06_low_alpha/decisions.csv` (copy
`decisions_TEMPLATE.csv`; a refined code needs `new_definition`, and `new_label`, `new_include`,
`new_exclude` where they change). You may help them write the file; you may not decide for them. Then:
```bash
python3 pipeline/council.py CFG consensus      # records the decisions in the reports and the dashboard
python3 pipeline/council.py CFG refine         # only if a code is refined: archives this coding round
                                               # under archive/, writes codebook version 1.1 (dropped codes
                                               # removed); then rerun `run.py code` on the whole corpus
```
After a refine, the researchers also recode the held-out sample for the refined codes.

When the researchers' resolved coding of the held-out sample exists (as
`human/05_heldout_coding/resolved.csv`, or pass `--labels FILE`), score human-council agreement
(Cohen's kappa per code and pooled):
```bash
python3 pipeline/council.py CFG heldout-score
python3 pipeline/council.py CFG retention --human prior.csv     # only if the researchers coded the corpus first
```

### Report

```bash
python3 pipeline/council.py CFG cost
python3 pipeline/council.py CFG report        # writes <workspace>/RESULTS.md and <workspace>/dashboard.html
```
`dashboard.html` is the results dashboard (self-contained, no network): stage summary, reliability
with the codes below 0.7 and the researchers' decisions, prevalence, the codebook with representative
quotes, and calls, tokens and cost by stage. `consensus` refreshes it too; `council.py dashboard`
rebuilds it alone.
When the researchers have drafted their themes:
```bash
python3 pipeline/council.py CFG check-quotes writeup.md   # every "quote" [UID] must be an exact substring
```

## 4. What to report to the user

At the end (and briefly at every STOP), report from the artifacts, not from memory:

1. Variant, roster (model family and model id per role, from `logs/calls.jsonl`), model provider caveat,
   data governance, thresholds, the two Stage 0 samples and the seed.
2. Stage 1: codes per AI analyst by analysis layer; repairs and units unaccounted before and after the
   completeness round; validation status. TACT-Full: critiques by type and analysis layer,
   accept/reject/partial, codes the adversaries proposed.
3. Stage 2: raw codes, groups, kept, dropped below the minimum respondents (and any restored), relations,
   apply errors. TACT-Full: reconciliation critiques and answers; TACT-Lite versus TACT-Full candidate counts.
4. Stage 3: reviewers, edits by type, approved codes, adversary codes admitted, blind-pass codes
   the council lacked.
5. Stage 4/5: alpha median, min, max, number below 0.7 (by id), number at or above 0.80, pairwise
   kappa, survival, `ISSUE` and `UNCOVERED` counts; TACT-Full: the same before (v0) and after (v1) the
   coding adversaries' critiques, cells changed, screening recall against TACT-Lite, high-uncertainty
   assignments flagged and reviewed.
6. Human checks: human-council agreement on the held-out sample, spot-check sample size, the
   researchers' decision on every code below 0.7, retention if applicable.
7. Cost per stage. Anything that failed or was skipped, and why.
Point the user to `dashboard.html`, `RESULTS.md`, `results/<cond>/reliability_report.md` (the
supplement table of every code and the codes below the alpha threshold).

## 5. When something goes wrong

- A discovery call's file fails after repairs: report the errors (`discovery/validation/per_reading/`);
  options are a rerun of that call (delete its output file and rerun `run.py discovery`) or a
  different model for that family. Record the deviation.
- A reply is not parseable JSON: the raw reply is in `logs/raw/`; rerun the command (the step is
  retried); if it keeps failing, report it.
- An AI coder skipped units: consensus counts them as missing (reported); rerun only that batch by
  deleting its file before `freeze`, never after.
- Exit status 3: manual prompts are waiting (section 2, route B).
- `replay: no recorded reply ...`: a replayed run asked for a call the recording does not have (the
  config, corpus or a human file differs from the recorded run). `replay: the prompt ... differs`
  is a warning: the recorded reply is used for a prompt that changed.
- `status` tells you the next step at any point.

## 6. Running without the scripts for model calls (route C)

For each role: render the prompt (fill the placeholders from the table at the top of its file, from
`config.yaml` and the workspace), send it with exactly the listed input files (each under a line
`=== FILE: <path> ===`), save the reply's JSON to the output path, log the call with
`council.py CFG log-call --stage ... --role ... --family ... --model ... --inputs ... --outputs ...`, and run
the deterministic command shown.

| Role | Prompt | Inputs | Output | Then run |
|---|---|---|---|---|
| AI analyst, one discovery call | `01_discovery_analyst.md` (briefs already rendered by `council.py CFG discovery-briefs` into `briefs/discovery/`) | `data/corpus.txt` or one discovery batch `data/discovery_batches/<B>.txt` | `discovery/v0/per_reading/analyst_<A>_<RQ>.json` | after all calls: `council.py CFG merge-readings`, `validate --stage v0` (fix failures by sending the `repair` / `completeness` instruction from the same prompt file), `freeze --what discovery` |
| Discovery adversary (TACT-Full) | `01_discovery_adversary.md` | corpus, `discovery/v0/analyst_<A>.json` | `discovery/critiques/adversary_<A>.json` | |
| AI analyst's answer (TACT-Full) | `01_discovery_answer.md` | corpus, v0 file, critiques | `discovery/answers/answer_<A>.json`, `discovery/v1_delta/analyst_<A>.json` | `council.py CFG apply-delta --analyst <A>`, then `validate --stage v1` |
| Reconciler | `02_reconciler.md` (rendered by `council.py CFG reconcile-prepare --cond <lite or full>` into `briefs/reconciliation/`) | `reconciliation/<cond>/per_rq/<RQ>/input.json` (sent as `reconciliation/input.json`) | `reconciliation/<cond>/per_rq/<RQ>/merge_plan.json` | |
| Reconciliation adversary (TACT-Full) | `02_reconciliation_adversary.md` | input, plan | `.../adversary_critiques.json` | |
| Reconciler's answer (TACT-Full) | `02_reconciler_answer.md` | input, plan, critiques | `.../reconciler_answers.json`, `.../merge_plan_revised.json` | `council.py CFG reconcile-apply --cond <cond>` |
| AI coder | `04_coder.md` (rendered by `council.py CFG code-prepare` into `briefs/coding/`) | `coding/batches/batch<n>.txt` | `coding/L/coder<k>_batch<n>.jsonl` | after all batches: `freeze --what coding`, `consensus` |
| Decision model, screening (TACT-Full) | `decision_model_questions.md` | one unit + every approved code | `coding/jev/screen.json` (`scores`: uid -> code -> p) | screened batches and per-batch briefs are built by `run.py code`; without the scripts, list per unit the codes with p >= 0.10, at least the top 5, plus a seeded 5% audit of the rest |
| Coding adversary (TACT-Full) | `04_coding_adversary.md` | batch, the AI coder's v0 file (the codebook is in the brief; no decision-model input) | `coding/LJA/critiques/coder<k>_batch<n>.json` | |
| AI coder's answer (TACT-Full) | `04_coder_answer.md` | batch, v0 file, critiques | `coding/LJA/answers/coder<k>_batch<n>.json`, `coding/LJA/coder<k>_batch<n>.jsonl` | `consensus` (flags high-uncertainty assignments from `coding/jev/screen.json`) |

Output schemas are in each prompt file, inside the prompt text the model receives.
