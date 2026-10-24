# The validation: 256 Stack Overflow threads about GitHub Copilot

The paper validates TACT on an independent dataset that other researchers coded qualitatively: the
Stack Overflow posts about GitHub Copilot that Zhang et al. analyzed by constant comparison (*Demystifying
Practices, Challenges and Expected Features of Using GitHub Copilot*, IJSEKE 33(11-12), 2023; their
dataset: Zenodo, doi:10.5281/zenodo.8123303). Their coding is the reference, and the council's agreement
with it is measured with recall, precision and F1 (Section V of the paper; details in
[SUPPLEMENT.md](../../SUPPLEMENT.md), S4).

This folder holds the data, codebooks, mapping, results and scripts of the paper's validation, and the
configuration to run TACT on this corpus yourself.

## What is here

| Path | What it is |
|---|---|
| `coded_corpus/` | **The final codebook and the coded corpus** (TACT-Lite and TACT-Full), with every AI coder's assignments and rationales. Start here. |
| `data/threads.csv` | The 256 threads (`uid, so_question_id, link, author, created, text`), each rebuilt as it stood on 18 June 2023, code blocks as `[code]`. Stack Overflow content, CC BY-SA. |
| `data/ATTRIBUTION.md` | License, what we changed, and every thread's link and question author. |
| `data/splits.json` | The split: 64 reserved threads (the pool for the blind-pass sample and the codebook's examples) and 192 evaluation threads (every agreement and reliability figure), the blind-pass sample of 50 threads, the held-out sample of 50 evaluation threads the researchers coded, the strata and the seed. |
| `codebooks/` | The TACT-Lite and TACT-Full candidate codebooks (`candidate_lite.json`, 80 codes; `candidate_full.json`, 87 codes) and the approved codebook (`approved_codebook.json`, 72 codes over the five research questions, with definitions, inclusion and exclusion rules, representative quotes, provenance and the review log). |
| `results/L/`, `results/LJA/` | TACT-Lite coding (L) and TACT-Full coding after the coding adversaries (LJA) with the approved codebook, on all 256 threads: each AI coder's codes and rationale (`coder_long.csv`), the 2-of-3 consensus, per-code reliability, prevalence and a summary. |
| `results/L_eval/`, `results/LJA_eval/` | The same, on the 192 evaluation threads: the paper's reliability figures. Their summaries list the 64 reserved threads as unknown units, because those threads are left out. |
| `results/screening/screening_plan.json` | TACT-Full's screening: the codes each AI coder was shown for each thread. |
| `results/disagreements_full.json` | The 98 code-thread pairs that count against the precision of the TACT-Full candidate codebook (SUPPLEMENT.md, S4). |
| `mapping/` | Zhang et al.'s categories with our definitions (`categories.json`); the mappings of the TACT-Lite and TACT-Full candidate codebooks and the approved codebook onto them (`mapping_lite.json`, `mapping_full.json`, `mapping_approved.json`) with their cell-by-cell audit files (`audit_*.csv`); a mapping made by one model before reconciliation (`alt_mapping_*.json`); and the attribution of every row of Zhang et al.'s sheets to a thread, without their text and categories (`label_attribution.csv`). |
| `scoring/` | The scoring scripts. |
| `baseline_gpt/` | The single-model baseline: the recorded baseline output (one GPT-5.6 call that built its own codebook and coded every thread), its mapping and its scores, and `run_baseline.py`, which runs the single-model baseline. |
| `dashboard_lite.html`, `dashboard_full.html` | The coding results as results dashboards (open in a browser; no model, no network). |
| `build_dashboards.py` | Rebuilds both dashboards with this repository's own consensus and reliability code, and stops if any code's alpha differs from the files in `results/`. |
| `config.yaml`, `config.lite.yaml` | TACT-Full and TACT-Lite on this corpus with TACT's default thresholds: the five research questions with Zhang et al.'s goals and rationales, issue codes, model roster, and the split settings. |
| `to_pipeline_csv.py` | Makes the pipeline's input (`corpus.csv`) from `data/`, with the strata, so that `prepare` draws the paper's split; `--check` compares a prepared workspace with `data/splits.json`. |

Zhang et al.'s dataset, with their labels, is available from their Zenodo record
(doi:10.5281/zenodo.8123302).

## Run TACT on these threads

This calls real models and costs money: about $35 for TACT-Lite and $86 for TACT-Full on these 256
threads at September 2026 list prices. The threads are public, so no consent question arises, but they
still go to the model providers in your config.

1. Connect three model families (and, for TACT-Full, the decision model): follow
   [SETUP.md](../../SETUP.md). Edit the `models` section of `config.yaml` or `config.lite.yaml` to
   match what you have.
2. Make the pipeline's input and check your setup:
   ```bash
   python3 examples/zhang2023/to_pipeline_csv.py
   python3 pipeline/council.py --config examples/zhang2023/config.lite.yaml doctor
   ```
3. Prepare the corpus and compare the split:
   ```bash
   python3 pipeline/council.py --config examples/zhang2023/config.lite.yaml prepare
   python3 examples/zhang2023/to_pipeline_csv.py --check runs/zhang2023-lite
   ```
   The reserved and evaluation threads and the blind-pass sample match `data/splits.json`;
   `prepare` draws its own held-out sample of 50 evaluation threads.
4. Run the stages with `--config examples/zhang2023/config.lite.yaml` (TACT-Lite) or
   `--config examples/zhang2023/config.yaml` (TACT-Full) as the main README's Quickstart 2 lists them,
   press the buttons in the local app, or ask a coding agent to follow `AGENTS.md`. The researchers'
   steps (blind pass, human review, held-out coding, spot-check, the decision on codes below the alpha
   threshold) are yours. Models change, so your results will differ from the paper's.
