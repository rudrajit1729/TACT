# The validation's codebook and coded corpus

| File | What it holds |
|---|---|
| `final_codebook.json` | The 72 codes of the final codebook: id, research question, label, definition, inclusion and exclusion rules, positive and negative example threads, representative quotes and the threads each code cites. |
| `coded_corpus_lite.csv`, `coded_corpus_full.csv` | The coded corpus under TACT-Lite and TACT-Full: every one of the 256 threads with its link and the codes that reached consensus (at least two of the three AI coders), by id and label. |
| `assignments_lite.csv`, `assignments_full.csv` | Every AI coder's assignments: AI coder (1, 2 or 3), thread, codes, the rationale given before the codes, and any note for UNCOVERED content. |

Research questions use Zhang et al.'s numbering: RQ1.4 functions, RQ1.5 purposes, RQ2.1 benefits,
RQ2.2 limitations and challenges, RQ2.3 expected features. `ISSUE_*` codes mark threads with a data
problem (Section IV, Stage 4). Thread text is in `../data/threads.csv`.
