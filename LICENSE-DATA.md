# License for prompts, documentation and data

Source code is released under the MIT License (`LICENSE`). Everything else in this repository is
released under the **Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0)**,
https://creativecommons.org/licenses/by-sa/4.0/ (legal code:
https://creativecommons.org/licenses/by-sa/4.0/legalcode). This covers:

- **The prompts** (`prompts/`) and the documentation (`README.md`, `SUPPLEMENT.md`, `SETUP.md`,
  `AGENTS.md`, the README files in `examples/`) and the figure (`figures/`).
- **The validation corpus** (`examples/zhang2023/data/threads.csv`): 256 Stack Overflow threads,
  which their authors contributed under CC BY-SA (version per post; see
  `examples/zhang2023/data/ATTRIBUTION.md`, which lists every thread, its link, its question author
  and what we changed). It is redistributed under CC BY-SA 4.0, as the ShareAlike term requires.
- **Everything derived from the corpus**: the candidate and approved codebooks, the AI coders'
  assignments and rationales, consensus, reliability and prevalence files, the screening plan, the
  disagreement list, the single-model baseline's output and the dashboards
  (`examples/zhang2023/codebooks/`, `results/`, `baseline_gpt/`, `dashboard_*.html`). They quote
  and adapt the threads, so they are CC BY-SA 4.0 as well.
- **The mapping** (`examples/zhang2023/mapping/`): the mappings, their audit files and
  `label_attribution.csv` are ours. `categories.json` holds the category names of Zhang et al.'s
  scheme with definitions we derived from their paper and dataset, and example excerpts from their
  dataset. Credit their work when you reuse it:
  Beiqi Zhang, Peng Liang, Xiyu Zhou, Aakash Ahmad and Muhammad Waseem. *Demystifying Practices,
  Challenges and Expected Features of Using GitHub Copilot.* International Journal of Software
  Engineering and Knowledge Engineering 33(11-12), 2023; dataset: Zenodo, doi:10.5281/zenodo.8123303
  (CC BY 4.0). Their spreadsheet and their labels are not included in this repository;
  `examples/zhang2023/scoring/reference_labels.py` rebuilds the reference labels from a copy you
  download.

When you reuse this material, credit the Stack Overflow authors as listed in
`examples/zhang2023/data/ATTRIBUTION.md`, cite the paper (`CITATION.cff`), link to the license,
indicate your changes, and license your adaptations under CC BY-SA 4.0.
