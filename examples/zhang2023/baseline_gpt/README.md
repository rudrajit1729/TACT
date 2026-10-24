# Single-model baseline (SUPPLEMENT.md, S4)

One GPT-5.6 call, through the Codex command-line tool, received the 256 threads and Zhang et al.'s five
research questions, built its own codebook and coded every thread. The recorded baseline output is
`output.json`, and `codebook.json` is its codebook. Its codes were mapped to Zhang et al.'s categories with
the same procedure as TACT's codes (`mapping_baseline.json`) and scored on the 192 evaluation threads against
the same reference labels (`score_baseline.py`, results in `scores.json`). `bootstrap.py` compares TACT's
final coding with the baseline over 1,000 paired resamples of the evaluation threads (`bootstrap.json`).

`score_baseline.py` and `bootstrap.py` need the reference labels (see `../README.md`).

**Running it yourself.** `run_baseline.py` runs the single-model baseline: one GPT-5.6 call (the `gpt`
family of `../config.yaml`, `gpt-5.6-terra`, through `pipeline/models.py`) receives the 256 threads and the
five research questions from `../config.yaml`, builds a codebook and codes every thread. It writes
`output_rerun.json` in the schema of the recorded baseline output, so `output.json` stays as it is.
`score_baseline.py --map` runs the mapping procedure of Section V-B (`../scoring/map_codebook.py`) on the
baseline's codebook and scores with that mapping (`mapping_baseline_rerun.json`, `scores_rerun.json`);
without `--map` it scores with the recorded mapping. Both call models and cost money; `--dry-run` prints
the prompts without calling any model.

```bash
python3 examples/zhang2023/baseline_gpt/run_baseline.py --dry-run          # the prompt, no call
python3 examples/zhang2023/baseline_gpt/run_baseline.py                    # -> output_rerun.json
python3 examples/zhang2023/baseline_gpt/score_baseline.py --map --dry-run  # the three mapping prompts, no call
python3 examples/zhang2023/baseline_gpt/score_baseline.py --map            # -> mapping_baseline_rerun.json, scores_rerun.json
```
