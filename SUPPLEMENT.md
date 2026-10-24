# Supplement to TACT: A Pragmatic Approach to Qualitative Analysis in SE Research Using an AI Council

Rudrajit Choudhuri, Christian Bird, Carmen Badea, Anita Sarma

This supplement gives the prompts and scripts (S1), the defaults (S2), the reliability computation (S3), the
details of the validation on Zhang et al.'s dataset (S4) and the measured cost of the validation run
(S5). Every file named here is in this repository.

- [S1. Prompts and scripts](#s1-prompts-and-scripts)
- [S2. Defaults](#s2-defaults)
- [S3. Reliability computation](#s3-reliability-computation)
- [S4. Validation details](#s4-validation-details)
- [S5. Measured cost of the validation run](#s5-measured-cost-of-the-validation-run)

## S1. Prompts and scripts

Each model role reads one prompt file in [`prompts/`](prompts/). The text a model receives lies between
`<!-- BEGIN PROMPT -->` and `<!-- END PROMPT -->`; the programs fill its placeholders from the study's
configuration, and every rendered prompt is kept in the run's workspace (`briefs/`). Each file states
the role's purpose, its inputs and the exact JSON it must return.
[`prompts/PROMPTS.md`](prompts/PROMPTS.md) maps variant, stage and role to a file.

| Stage | Role | Variant | Prompt |
|---|---|---|---|
| 1 Discovery | AI analyst (one per model family; one call per research question, at the three analysis layers) | TACT-Lite, TACT-Full | [`01_discovery_analyst.md`](prompts/01_discovery_analyst.md) |
| 1 Discovery | Discovery adversary | TACT-Full | [`01_discovery_adversary.md`](prompts/01_discovery_adversary.md) |
| 1 Discovery | AI analyst's answer to the critiques | TACT-Full | [`01_discovery_answer.md`](prompts/01_discovery_answer.md) |
| 2 Reconciliation | Reconciler | TACT-Lite, TACT-Full | [`02_reconciler.md`](prompts/02_reconciler.md) |
| 2 Reconciliation | Reconciliation adversary | TACT-Full | [`02_reconciliation_adversary.md`](prompts/02_reconciliation_adversary.md) |
| 2 Reconciliation | Reconciler's answer to the critiques | TACT-Full | [`02_reconciler_answer.md`](prompts/02_reconciler_answer.md) |
| 4 Coding | AI coder (one per model family) | TACT-Lite, TACT-Full | [`04_coder.md`](prompts/04_coder.md) |
| 4 Coding | Coding adversary | TACT-Full | [`04_coding_adversary.md`](prompts/04_coding_adversary.md) |
| 4 Coding | AI coder's answer to the critiques | TACT-Full | [`04_coder_answer.md`](prompts/04_coder_answer.md) |
| 4 Coding | Decision model: screening question | TACT-Full | [`decision_model_questions.md`](prompts/decision_model_questions.md) |

Stage 3 (human review) and the researchers' checks in Stage 5 are carried out by the researchers, and
the provenance check, the overlap table, the minimum-respondents rule, consensus and reliability by
programs (`pipeline/council.py`, `pipeline/reliability.py`), so none of them has a prompt.

**Scripts.** Every step that needs no judgment runs as a deterministic script in [`pipeline/`](pipeline/):

| Stage | Step | Script and command |
|---|---|---|
| 0 Data preparation | units, context, the blind-pass and held-out samples | `council.py prepare` |
| 1 Discovery | provenance check of every cited unit and quote | `council.py validate` |
| 2 Reconciliation | overlap table (Jaccard similarity, overlap coefficient) | `council.py reconcile-prepare` |
| 2 Reconciliation | apply the merge plan; drop and list codes below the minimum respondents | `council.py reconcile-apply` |
| 3 Human review | the researchers' packets and review dashboard; apply their edits | `human.py`, `council.py approve` |
| 4 Coding | batches and AI coder prompts | `council.py code-prepare` |
| 5 Consensus and reliability | consensus, per-code Krippendorff's alpha, pairwise Cohen's kappa | `council.py consensus`, `reliability.py` |
| 5 Consensus and reliability | human-council agreement on the held-out sample | `council.py heldout-score` |
| Output | results report and dashboard | `report.py`, `dashboard.py` |

`run.py` runs the model stages in order and calls these scripts between them; `models.py` connects the
model families and the decision model.

**The research questions of the validation.** The AI analysts received Zhang et al.'s five qualitative
research questions with their goals and rationales, in Zhang et al.'s original wording
([`examples/zhang2023/config.yaml`](examples/zhang2023/config.yaml)):

| RQ | Research question | Goal and rationale |
|---|---|---|
| RQ1.4 | What functions are implemented by using GitHub Copilot? | Copilot can complete entire functions according to users' comments. The question asks for a categorization of the functions implemented with Copilot (data item: functions implemented by Copilot), categorized by what each function does, from developers' descriptions of the functions they mention. |
| RQ1.5 | What are the purposes of using GitHub Copilot? | Users may use Copilot for different purposes; the question asks what users are using Copilot for (data item: intentions of using Copilot). |
| RQ2.1 | What are the benefits of using GitHub Copilot? | Using Copilot to assist programming can bring benefits (e.g., reducing the workload of developers); the question collects the advantages brought to development by applying Copilot (data item: benefits brought by using Copilot). |
| RQ2.2 | What are the limitations & challenges of using GitHub Copilot? | There are restrictions and problems when using Copilot; the question collects the limitations and challenges practitioners may experience (data item: restrictions and difficulties when using Copilot). |
| RQ2.3 | What are the expected features of users about GitHub Copilot? | There are features Copilot does not provide but users want; the question investigates the features users expect (data item: features that users want Copilot to provide). |

## S2. Defaults

The researchers fix these thresholds in data preparation (Stage 0), before any model runs, so that
they cannot choose them after seeing results.

| Setting | Default | Where it acts |
|---|---|---|
| Minimum respondents per code | 3 distinct respondents | Stage 2: a program drops codes with fewer and lists them for human review |
| Krippendorff's alpha threshold | 0.7 (raise it, e.g. to 0.8, for conservative conclusions) | Stage 5: codes below it return to the researchers, who refine and recode, or drop |
| Batch size | 25 units (20 to 50 recommended) | Stage 4: units per AI coder call |
| Consensus | 2 of 3 AI coders | Stage 5: a code that reaches it on a unit enters the coded corpus |
| Blind-pass sample | 10% of units, at least 50 and at most 150, stratified by question | Stage 3: coded by at least two researchers before any model output |
| Held-out sample | at least 10% of units, stratified by question | Stage 5: coded by at least two researchers without the council's coding |
| TACT-Full: screening | score at least 0.10, plus the top 5 codes | Stage 4: the codes each AI coder sees for a unit |
| TACT-Full: screening audit | 5% of screened-out (unit, code) pairs | Stage 4: shown anyway, at random, so that codes screening hid can be checked |
| TACT-Full: high-uncertainty assignment | screening score below 0.25 | Stage 5: consensus assignments flagged for the researchers' review |

## S3. Reliability computation

The definitions below match `pipeline/reliability.py` and the standard-library program
[`supplement/b_example.py`](supplement/b_example.py), which reproduces every number of the worked
example. A *unit* is one coded item, an *AI coder* is one model instance at Stage 4, and a *code* is one
entry of the final codebook.

**Per-code binary agreement.** The coding is multi-label, so each code is scored as its own binary
decision (did this AI coder assign this code to this unit) and reliability is reported per code, as a
distribution across codes. A unit an AI coder never saw is missing, not 0.

**Krippendorff's alpha.** For one code, each unit $u$ with $n_u \ge 2$ values ($n_{u0}$ zeros, $n_{u1}$
ones) adds $n_{u0}(n_{u0}-1)/(n_u-1)$ to $o_{00}$, $n_{u1}(n_{u1}-1)/(n_u-1)$ to $o_{11}$ and
$n_{u0}n_{u1}/(n_u-1)$ to each of $o_{01}$ and $o_{10}$. With $n$ the total, $n_0 = o_{00}+o_{01}$
and $n_1 = o_{10}+o_{11}$: observed disagreement $D_o = (o_{01}+o_{10})/n$, expected disagreement
$D_e = 2n_0n_1/(n(n-1))$, and $\alpha = 1 - D_o/D_e$. Alpha is undefined (reported as such, and left
out of the median, minimum, maximum and threshold counts) when no unit was seen by two AI coders or
when every value is the same. The report gives, per codebook, the median, minimum and maximum alpha,
the number of codes below the threshold and the number at or above 0.80.

**Pairwise Cohen's kappa.** For each pair of AI coders and each code, on the units both coded:
$p_o$ is the share of units on which they agree, $p_e = m_xm_y + (1-m_x)(1-m_y)$ with $m_x$ and $m_y$
each AI coder's share of units with the code, and $\kappa = (p_o - p_e)/(1 - p_e)$. The 2x2 counts
($a$ both assigned, $b$ and $c$ one did, $d$ neither) are reported with positive agreement
$2a/(2a+b+c)$ and negative agreement $2d/(2d+b+c)$, so that a reader can tell a rare code from real
disagreement. Pairwise kappa shows whether one AI coder diverges from the other two.

**Consensus and the ISSUE rule.** A code reaches consensus on a unit when at least 2 of the 3 AI
coders assign it, and it then enters the coded corpus. A unit that two or more AI coders code with any
`ISSUE_*` code leaves the prevalence base but stays in the file and is counted; prevalence is the
number of units on which a code reached consensus divided by the units outside the ISSUE units.
`UNCOVERED` is reported, never counted as a code.

**Human-council agreement.** Researchers code the held-out sample with the final
codebook, without seeing the council's coding, and resolve their differences. A program compares
their resolved coding with the codes that reached consensus using Cohen's kappa, per code and pooled
over all (unit, code) decisions.

**Worked example.** Three AI coders (A, B, C), six units (u1 to u6), two codes (X, Y):

| Unit | AI coder A | AI coder B | AI coder C |
|---|---|---|---|
| u1 | X | X | X |
| u2 | X, Y | X, Y | Y |
| u3 | Y | Y | Y |
| u4 | X | (none) | X, Y |
| u5 | (none) | (none) | (none) |
| u6 | Y | X, Y | Y |

For code X, the coincidence totals are $o_{00} = 7$, $o_{01} = o_{10} = 3$, $o_{11} = 5$ ($n = 18$,
$n_0 = 10$, $n_1 = 8$), so $D_o = 6/18 = 0.3333$, $D_e = 160/306 = 0.5229$ and $\alpha(X) = 0.3625$.
For code Y, $o_{00} = 7$, $o_{01} = o_{10} = 1$, $o_{11} = 9$, so $D_o = 0.1111$ and
$\alpha(Y) = 0.7875$. Pairwise kappa for X is 0.3333 (A, B), 0.6667 (A, C) and 0 (B, C); for Y it is
1, 0.6667 and 0.6667. Six (unit, code) pairs reach consensus: X on u1, u2 and u4, and Y on u2, u3 and
u6. Code X falls below the alpha threshold and returns to the researchers. If AI coder C had never seen
u6, its value there would be missing rather than 0, and $\alpha(X)$ would be 0.3333. Running
`python3 supplement/b_example.py` prints:

```
== Assignment table (1 = code applied) ==
  code X: u1=111  u2=110  u3=000  u4=101  u5=000  u6=010
  code Y: u1=000  u2=111  u3=111  u4=001  u5=000  u6=111

== Code X: binary matrix and coincidence matrix ==
    unit  values      n_u   +o00  +o01  +o10  +o11
    u1    [1, 1, 1]   3    0.00  0.00  0.00  3.00
    u2    [1, 1, 0]   3    0.00  1.00  1.00  1.00
    u3    [0, 0, 0]   3    3.00  0.00  0.00  0.00
    u4    [1, 0, 1]   3    0.00  1.00  1.00  1.00
    u5    [0, 0, 0]   3    3.00  0.00  0.00  0.00
    u6    [0, 1, 0]   3    1.00  1.00  1.00  0.00
    totals: o00=7.00 o01=3.00 o10=3.00 o11=5.00  n=18  n0=10  n1=8
    D_o = (o01+o10)/n = 0.3333   D_e = 2*n0*n1/(n(n-1)) = 0.5229   alpha = 1 - D_o/D_e = 0.3625
    krippendorff_binary -> 0.3625
    pair AB: a=2 b=1 c=1 d=2 | p_o=0.6667  m_A=0.5000  m_B=0.5000  p_e=0.5000  kappa=0.3333 | PA=0.6667 NA=0.6667
    pair AC: a=2 b=1 c=0 d=3 | p_o=0.8333  m_A=0.5000  m_C=0.3333  p_e=0.5000  kappa=0.6667 | PA=0.8000 NA=0.8571
    pair BC: a=1 b=2 c=1 d=2 | p_o=0.5000  m_B=0.5000  m_C=0.3333  p_e=0.5000  kappa=0.0000 | PA=0.4000 NA=0.5714

== Code Y: binary matrix and coincidence matrix ==
    unit  values      n_u   +o00  +o01  +o10  +o11
    u1    [0, 0, 0]   3    3.00  0.00  0.00  0.00
    u2    [1, 1, 1]   3    0.00  0.00  0.00  3.00
    u3    [1, 1, 1]   3    0.00  0.00  0.00  3.00
    u4    [0, 0, 1]   3    1.00  1.00  1.00  0.00
    u5    [0, 0, 0]   3    3.00  0.00  0.00  0.00
    u6    [1, 1, 1]   3    0.00  0.00  0.00  3.00
    totals: o00=7.00 o01=1.00 o10=1.00 o11=9.00  n=18  n0=8  n1=10
    D_o = (o01+o10)/n = 0.1111   D_e = 2*n0*n1/(n(n-1)) = 0.5229   alpha = 1 - D_o/D_e = 0.7875
    krippendorff_binary -> 0.7875
    pair AB: a=3 b=0 c=0 d=3 | p_o=1.0000  m_A=0.5000  m_B=0.5000  p_e=0.5000  kappa=1.0000 | PA=1.0000 NA=1.0000
    pair AC: a=3 b=0 c=1 d=2 | p_o=0.8333  m_A=0.5000  m_C=0.6667  p_e=0.5000  kappa=0.6667 | PA=0.8571 NA=0.8000
    pair BC: a=3 b=0 c=1 d=2 | p_o=0.8333  m_B=0.5000  m_C=0.6667  p_e=0.5000  kappa=0.6667 | PA=0.8571 NA=0.8000

== agreement(long_rows, codes, coders) ==
  code=X, alpha=0.3625, kappa_AB=0.3333, kappa_AC=0.6667, kappa_BC=0.0000, kappa_mean=0.3333, n_any=4, n_consensus=3, n_unanimous=1
  code=Y, alpha=0.7875, kappa_AB=1.0000, kappa_AC=0.6667, kappa_BC=0.6667, kappa_mean=0.7778, n_any=4, n_consensus=3, n_unanimous=3
  describe -> 2 codes; alpha median 0.79, range 0.36-0.79; 1 below 0.7, 0 at or above 0.80

== consensus_codes(long_rows) ==
  u1 X n_coders=3 unanimous=True
  u2 X n_coders=2 unanimous=False
  u2 Y n_coders=3 unanimous=True
  u3 Y n_coders=3 unanimous=True
  u4 X n_coders=2 unanimous=False
  u6 Y n_coders=3 unanimous=True
  any-coder (unit, code) pairs = 8; consensus pairs = 6; survival = 6/8 = 0.7500
  (for contrast, per-coder assignment count = 18; consensus x 3 / that is not the survival rate reported)

== Missing-value convention: coder C never saw u6 (None, not 0) ==
    unit  values      n_u   +o00  +o01  +o10  +o11
    u1    [1, 1, 1]   3    0.00  0.00  0.00  3.00
    u2    [1, 1, 0]   3    0.00  1.00  1.00  1.00
    u3    [0, 0, 0]   3    3.00  0.00  0.00  0.00
    u4    [1, 0, 1]   3    0.00  1.00  1.00  1.00
    u5    [0, 0, 0]   3    3.00  0.00  0.00  0.00
    u6    [0, 1, -]   2    0.00  1.00  1.00  0.00
    totals: o00=6.00 o01=3.00 o10=3.00 o11=5.00  n=17  n0=9  n1=8
    D_o = (o01+o10)/n = 0.3529   D_e = 2*n0*n1/(n(n-1)) = 0.5294   alpha = 1 - D_o/D_e = 0.3333
    krippendorff_binary -> 0.3333
    pair AB: n_pairable=6 kappa=0.3333 PA=0.6667 NA=0.6667
    pair AC: n_pairable=5 kappa=0.6154 PA=0.8000 NA=0.8000
    pair BC: n_pairable=5 kappa=0.1667 PA=0.5000 NA=0.6667

== When alpha is undefined ==
  no coder ever applied the code:   alpha = nan, kappa_AB = nan
  every coder applied it everywhere: alpha = nan, kappa_AB = nan
  one coder constant, the other not: kappa = -0.0000 (p_e < 1, so defined)
```

## S4. Validation details

The files are in [`examples/zhang2023/`](examples/zhang2023/README.md).

**The final codebook.** After the blind pass, we reviewed the candidate codebooks against the
threads each code cites and approved a first codebook of 80 codes. After the first coding round, we
consolidated the codes below the alpha threshold and approved the final codebook of 72 codes: 8 for functions, 15 for purposes, 12 for benefits, 22
for limitations and challenges, and 15 for expected features. Each code's definition, inclusion and
exclusion rules, representative quotes and provenance (the codes discovered by the AI analysts that it
was built from) are in
[`examples/zhang2023/codebooks/approved_codebook.json`](examples/zhang2023/codebooks/approved_codebook.json),
with the review edits and their reasons. The TACT-Lite and TACT-Full candidate codebooks (80 and 87
codes) are beside it.

**Reference labels.** Zhang et al. released each coded excerpt with its category, but not the post it
came from. We located each excerpt in the threads and kept only the labels whose excerpt appeared in
exactly one evaluation thread: 183 reference labels, each a category given to one thread, on 128 of the
192 evaluation threads. The attribution of every excerpt is in
[`mapping/label_attribution.csv`](examples/zhang2023/mapping/label_attribution.csv), without Zhang et
al.'s text and categories; [`scoring/reference_labels.py`](examples/zhang2023/scoring/reference_labels.py)
joins it with their spreadsheet. The reference labels span 43 of Zhang et al.'s categories, and the
final codebook has a code for 42 of them, so the coding stage is scored against the 182 labels in
those 42 categories.

**Mapping.** The council's codes and Zhang et al.'s categories divide the data differently, so we
mapped each council code to their categories using only the definitions. A council code mapped to
every category that a researcher using Zhang et al.'s scheme might reasonably have assigned to a thread
carrying that code. An independent instance of Claude Opus 5 built the mapping with a rationale for
each council code and reconciled it with another independent mapping by a new instance of GPT-5.6.
Neither saw Zhang et al.'s labels. Two authors from our research team further spot-checked the
rationales and froze the mapping before scoring began. For the final codebook, 148 (code, category)
cells were considered, 102 were agreed outright and 133 were kept; 9 of the 72 codes map to no
category, and a code maps to 1.8 categories on average (TACT-Lite candidate codebook 1.7, TACT-Full
1.5). The mappings, Zhang et al.'s categories with our definitions, and the cell-by-cell audit files
are in [`examples/zhang2023/mapping/`](examples/zhang2023/mapping/).

**Scoring.** At the codebook stage, a council code counts for every thread it cites; at the coding
stage, only for the threads where it reached consensus. A reference label is *matched* when its thread
carries a council code mapped to the label's category. Recall is the share of reference labels
matched; precision is the share of the council's assignments that map to a category Zhang et al. gave
the same thread, counted only on threads they labeled for the same research question; F1 combines the
two.

**The 98 code-thread pairs that count against precision.** Under TACT-Full, 98 code-thread pairs
counted against the precision of the candidate codebook: the council code cited a thread to which
Zhang et al. gave a category the code does not map to, for the same research question. Each row gives
a council code, the categories it maps to, the category Zhang et al. gave the thread, and the number
of evaluation threads (n). Some rows reflect differences in granularity, and others threads that raised
several points, of which the council and Zhang et al. coded different ones. The list is
[`results/disagreements_full.json`](examples/zhang2023/results/disagreements_full.json).

| Council code | Code maps to | Zhang et al. category | n |
|---|---|---|---:|
| **Functions (11)** | | | |
| Encryption, token signing, process memory, terminal capture, struct printing | Memory read; Printing; Serialization | String processing | 2 |
| Self-contained computations: primes, Euclid, intersection, regex scanning, value conversions | Algorithm; Image processing; String processing; URL building | Data processing | 2 |
| Click handlers, built page elements, CSS and font rules | Front-end element control | URL building | 1 |
| Encryption, token signing, process memory, terminal capture, struct printing | Memory read; Printing; Serialization | Data processing | 1 |
| Explaining, documenting, testing, diagramming and fixing code already written | Test; Text processing | Algorithm | 1 |
| Imports, class members, option names, annotations and repeated boilerplate lines | Iteration; Printing | Front-end element control | 1 |
| Imports, class members, option names, annotations and repeated boilerplate lines | Iteration; Printing | Data processing | 1 |
| Schemas, ORM calls, routes and framework or infrastructure config | Data processing | Printing | 1 |
| Sorting, filtering, de-duplicating and reshaping lists, objects and dataframes | Data processing; Filtering; Iteration | Serialization | 1 |
| **Purposes (18)** | | | |
| Asking Copilot when stuck, and to fix code that fails | To check the code; To fix bugs | To help generate code | 2 |
| Checking the suggestion, or keeping it and asking later why it works | To help generate code; To improve coding ability | To provide ideas for writing code | 2 |
| Getting code for a language, API or task I don't know | To help generate code; To improve coding ability | To provide ideas for writing code | 2 |
| Having Copilot produce the code for a task, function or config block | To help generate code; To provide ideas for writing code | To fix bugs | 2 |
| Installing Copilot, or its new chat, to see what it can do | To try out the functionality of Copilot | To help generate code | 2 |
| Checking the suggestion, or keeping it and asking later why it works | To help generate code; To improve coding ability | To fix bugs | 1 |
| Checking the suggestion, or keeping it and asking later why it works | To help generate code; To improve coding ability | To check the code | 1 |
| Finishing the line or function as I type, in whatever editor I work in | To help generate code | To try out the functionality of Copilot | 1 |
| Finishing the line or function as I type, in whatever editor I work in | To help generate code | To generate code comments | 1 |
| Finishing the line or function as I type, in whatever editor I work in | To help generate code | To improve coding ability | 1 |
| Getting code for a language, API or task I don't know | To help generate code; To improve coding ability | To fix bugs | 1 |
| Posting Copilot's code as the answer to someone else's question | To fix bugs; To help generate code | To provide ideas for writing code | 1 |
| Writing a plain-language comment and letting Copilot write the code | To help generate code | To provide ideas for writing code | 1 |
| **Benefits (10)** | | | |
| Answerers post Copilot's output as the answer, saying where it came from | Useful code generation | Better code quality | 3 |
| Called great, or met with astonishment, with no capability named | Better user experience; Useful code generation | Faster development | 1 |
| Completes whole lines and function bodies as you type | Faster development; Useful code generation | Good adaptation to users' code patterns | 1 |
| Helpful when stuck or for whole blocks, in the way otherwise | Better user experience; Useful code generation | Frequent updates to provide more features | 1 |
| Offers up to ten alternative solutions to pick from | Better user experience; Useful code generation | Frequent updates to provide more features | 1 |
| Picks up the surrounding code and the repeated pattern | Good adaptation to users' code patterns; Useful code generation | Better code quality | 1 |
| Provisional until someone who knows checks it, and the thread often does the checking | Useful code generation | Better code quality | 1 |
| Write the comment or pseudocode, press Tab, and it writes the code | Faster development; Useful code generation | Good adaptation to users' code patterns | 1 |
| **Limitations and challenges (54)** | | | |
| Copilot overrides editor settings and breaks typing: brackets, duplicate keys, dead redo | Difficulty of integration; Hard to configure; Show loading | Limitation to code generation | 5 |
| The only fix is turning Copilot off; some do, others configure around it | Difficulty of integration; Lack of customization; Unfriendly user experience | Limitation to code generation | 5 |
| Corporate proxies, VPNs and certificates block it: works at home, not at work | Difficulty of accessing Copilot; Hard to configure | Difficulty of integration | 3 |
| Signing in, authorizing or activating Copilot fails | Difficulty of accessing Copilot; Hard to configure | Difficulty of integration | 3 |
| A working Copilot stops suggesting, with no error, and fixes are rituals | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure; Show loading | Poor quality of generated code; Unfriendly user experience | 2 |
| Copilot blamed for editor behaviour that turned out to have another cause | Difficulty of integration | Limitation to code generation | 2 |
| Copilot's Tab and Ctrl+Enter collide with other keys, or can't be typed | Difficulty of integration; Lack of customization; Unfriendly user experience | Limitation to code generation | 2 |
| Little can be configured, so posters edit JSON, add plugins, patch the extension | Hard to configure; Lack of customization; Limitation to code generation | Difficulty of integration | 2 |
| Little can be configured, so posters edit JSON, add plugins, patch the extension | Hard to configure; Lack of customization; Limitation to code generation | Poor quality of generated code; Unfriendly user experience | 2 |
| Little can be configured, so posters edit JSON, add plugins, patch the extension | Hard to configure; Lack of customization; Limitation to code generation | Difficulty of accessing Copilot | 2 |
| Suggested code is wrong, invented, or no help at all | Challenge of not providing outdated suggestions; Limitation to code generation; Poor quality of generated code | Difficulty of understanding the generated code | 2 |
| Suggestions come in some languages and file types but not others | Limitation to code generation | Difficulty of integration | 2 |
| A working Copilot stops suggesting, with no error, and fixes are rituals | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure; Show loading | Limitation to code generation | 1 |
| A working Copilot stops suggesting, with no error, and fixes are rituals | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure; Show loading | High pricing | 1 |
| A working Copilot stops suggesting, with no error, and fixes are rituals | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure; Show loading | Unfriendly user experience | 1 |
| A working Copilot stops suggesting, with no error, and fixes are rituals | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure; Show loading | High pricing; Limitation to code generation | 1 |
| Accept inserts the whole block when only one line was wanted | Lack of customization; Unfriendly user experience | Difficulty of integration; Poor quality of generated code | 1 |
| Accept inserts the whole block when only one line was wanted | Lack of customization; Unfriendly user experience | Difficulty of integration; Limitation to code generation | 1 |
| Copilot blamed for editor behaviour that turned out to have another cause | Difficulty of integration | High pricing | 1 |
| Copilot overrides editor settings and breaks typing: brackets, duplicate keys, dead redo | Difficulty of integration; Hard to configure; Show loading | Poor quality of generated code; Unfriendly user experience | 1 |
| Copilot's Tab and Ctrl+Enter collide with other keys, or can't be typed | Difficulty of integration; Lack of customization; Unfriendly user experience | Hard to configure | 1 |
| Labs and Chat panels never appear or return errors | Difficulty of accessing Copilot; Difficulty of integration; Limitation to code generation | Poor quality of generated code | 1 |
| Little can be configured, so posters edit JSON, add plugins, patch the extension | Hard to configure; Lack of customization; Limitation to code generation | Difficulty of integration; Poor quality of generated code | 1 |
| No way to tell whether the code is right or what it does | Difficulty of understanding the generated code; Poor quality of generated code | Limitation to code generation | 1 |
| Not available for this IDE, platform, version, machine or container | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure | Limitation to code generation | 1 |
| Not available for this IDE, platform, version, machine or container | Difficulty of accessing Copilot; Difficulty of integration; Hard to configure | Poor quality of generated code | 1 |
| Only GitHub or IT can lift the limit, and later answers report it lifted | Difficulty of accessing Copilot; Difficulty of integration; Limitation to code generation | Unfriendly user experience | 1 |
| Only GitHub or IT can lift the limit, and later answers report it lifted | Difficulty of accessing Copilot; Difficulty of integration; Limitation to code generation | Lack of customization | 1 |
| Suggestions come back one line, repeated, or arrive unclosed | Limitation to code generation; Poor quality of generated code | Unfriendly user experience | 1 |
| Suggestions come back one line, repeated, or arrive unclosed | Limitation to code generation; Poor quality of generated code | Difficulty of integration | 1 |
| Suggestions come in some languages and file types but not others | Limitation to code generation | High pricing | 1 |
| The only fix is turning Copilot off; some do, others configure around it | Difficulty of integration; Lack of customization; Unfriendly user experience | Code privacy threat | 1 |
| Waitlist, trial, payment and the signed-in account decide who can use it | Difficulty of accessing Copilot; High pricing | Difficulty of integration | 1 |
| Waitlist, trial, payment and the signed-in account decide who can use it | Difficulty of accessing Copilot; High pricing | Poor quality of generated code; Unfriendly user experience | 1 |
| **Expected features (5)** | | | |
| Keys that accept and browse suggestions, and the Tab clashes they cause | Allow customization of shortcuts for suggestions; Compatible with other code generation tools | Can be integrated with more IDEs | 2 |
| Document the settings, let me build on it, stop overriding my editor | Compatible with other code generation tools | Accept the needed part of the suggestions | 1 |
| Side by side with IntelliSense: coexisting with the editor's own completion | Compatible with other code generation tools; Suggestions in IDE UI can be configured | Give suggestions when requested | 1 |
| Too much, too often: suggest only when I ask and stay quiet in comments, paths and normal mode | Give suggestions when requested; Suggestions in IDE UI can be configured | Accept the needed part of the suggestions | 1 |

**Single-model baseline.** To compare TACT with what a team might do today with an off-the-shelf
LLM, we gave one model the whole corpus in one prompt, as a team might in a chat window. GPT-5.6, at its
default reasoning effort, received the 256 threads and
Zhang et al.'s five research questions and was asked to build a codebook and code every thread. It ran
once, with no TACT stage: no analysis layers, provenance check, reconciliation, human review,
adversaries or decision model. The call used 114,826 input and 11,555 output tokens and returned 45
codes and 614 assignments. The prompt (the threads follow it, each headed by its identifier):

```
You are a qualitative researcher. Below are 256 Stack Overflow threads (question, answers and comments) about GitHub Copilot. Do a thematic analysis to answer these five research questions:
- RQ1.4: What functions are implemented by using GitHub Copilot?
- RQ1.5: What are the purposes of using GitHub Copilot?
- RQ2.1: What are the benefits of using GitHub Copilot?
- RQ2.2: What are the limitations & challenges of using GitHub Copilot?
- RQ2.3: What are the expected features of users about GitHub Copilot?

1. For each research question, develop a codebook: codes, each with a short label and a one-sentence definition.
2. Then code every thread: for each thread, list every code that applies (a thread may have none, or codes from several questions).

Return ONLY a JSON object, with no other text, in exactly this shape:
{"codebook": [{"id": "RQ1.4-C1", "rq": "RQ1.4", "label": "...", "definition": "..."}],
  "assignments": [{"uid": "U001", "codes": ["RQ1.4-C1"]}]}
Include an assignments entry for every thread id, even if its code list is empty.
```

Its codes were mapped to Zhang et al.'s categories by the same procedure as TACT's, from definitions
alone, at 2.0 categories per code; 7 of its 45 codes map to no category. Scored like TACT's final
coding, on the evaluation threads against the same 182 reference labels, the baseline matched 113
labels: recall 0.62, precision 0.68 and F1 0.65, against F1 0.71 for TACT-Lite and 0.72 for TACT-Full.
In 1,000 paired bootstrap resamples of the evaluation threads, TACT-Lite and TACT-Full exceeded the
baseline's F1 in 97% and 99% of resamples. The program, its output, the mapping and the scores are in
[`examples/zhang2023/baseline_gpt/`](examples/zhang2023/baseline_gpt/).

## S5. Measured cost of the validation run

Model calls, input and output tokens (millions) and cost (USD) of TACT-Lite and TACT-Full by stage for
the 256 threads, at list prices in September 2026 (Table IV of the paper). Calls and tokens count
generative model calls; TACT-Full's costs also include the decision model's screening requests.

| Stage | TACT-Lite calls | In | Out | $ | TACT-Full calls | In | Out | $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Discovery | 19 | 3.26 | 0.64 | 23.02 | 31 | 6.79 | 1.11 | 48.69 |
| Reconciliation | 5 | 0.30 | 0.15 | 5.14 | 15 | 1.12 | 0.33 | 12.64 |
| Coding | 33 | 1.59 | 0.07 | 7.10 | 99 | 4.95 | 0.34 | 24.67 |
| **Total** | **57** | **5.15** | **0.85** | **35.26** | **145** | **12.86** | **1.78** | **86.00** |

Per 100 threads, a run cost $13.77 (TACT-Lite) and $33.59 (TACT-Full). The decision model's screening
requests, one per thread scoring all 72 final codes, cost $0.24. These figures apply to corpora of
similar length: coding cost scales with the number of threads, and discovery cost with the length of
the corpus and the number of research questions.
