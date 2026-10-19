English | [中文](../zh-TW/EXPERIMENTS.md)

# Reproducing the experiments

This guide lists every step that produces the results and figures of "Coordination without convergence: Three decouplings in learnable ant collectives", with its settings and outputs, and maps every figure and table of the paper to the script and data behind it. Results themselves are summarized in [RESULTS.md](RESULTS.md); file formats are described in [DATA_DICTIONARY.md](DATA_DICTIONARY.md).

## Conventions

- **Paired design.** Every comparison is paired by random seed: within a seed, conditions share all randomness up to the point at which they differ. Counterfactual branches are created by pausing a colony and copying its complete state (`ForagingSystem.run_until` and `fork`).
- **Statistics.** 95% percentile bootstrap intervals (10,000 resamples), two-sided paired Wilcoxon signed-rank tests with Cohen's d_z, Holm correction within families, exact McNemar tests for paired binary outcomes, and two one-sided tests (TOST) for equivalence. Helpers are in `experiments/common.py`.
- **Default settings are the paper's settings.** Running a script without environment variables reproduces the paper's sample sizes.
- **Quick mode.** `QUICK=1` shrinks every experiment to a few seeds and short runs, for smoke testing only. It writes to the same `results/` and `figures/` folders and therefore overwrites the paper's data; use a separate copy, or restore with `git checkout -- results figures`.
- **Generated logs.** Each script also writes a text summary to `results/summary_<name>.md` (Traditional Chinese). These files are logs and are not tracked by git; the curated bilingual version is [RESULTS.md](RESULTS.md).
- **Running a step overwrites its stored results.** Every script writes to `results/` and `figures/`, replacing the files that ship with the repository; restore them with `git checkout -- results figures` if needed.
- **Base models.** The behavior-cloned base models are included in `miat_ants/foraging/weights/`. `base_bc.npz` is retrained with `python -m miat_ants.foraging.pretrain` (about 2 min; this overwrites the shipped file); `base_bc_mark05.npz` (teacher marks with probability 0.5) is retrained automatically by `exp11_d1_controls.py` if the file is missing.

## Running

```bash
python run_all.py                 # every step below, in order
python run_all.py exp10b exp12    # only the named steps (exp1 runs exp1 only, not exp10–exp13)
python experiments/exp12_learnable_return.py   # one script directly
```

Running a script directly uses the same defaults. On Windows PowerShell, set environment variables with `$env:QUICK="1"` before the command instead of the `VAR=value command` form. The confirmatory replication exp10b is the exp10 script with three environment variables:

```bash
EXP10_SEED0=1000 EXP10_SHAPLEY=12 EXP10_TAG=b python experiments/exp10_topic2_learnable.py
```

The full pipeline takes several hours on two CPU cores; the full exp10 run alone takes about 50 min. In quick mode, each traveling-salesman and sorting experiment (exp1–exp8) takes 20 to 100 s.

## Steps

| Step (`run_all.py`) | Script | Paper | Default sample | Main outputs in `results/` |
|---|---|---|---|---|
| exp1_tsp_params | `exp1_tsp_params.py` | Validation: text S2, fig. S1 | 5 runs per parameter value, 100 cycles; 5×5 grid and 30-city instance | `exp1_tsp_params.csv` |
| exp2_tsp_compare | `exp2_tsp_compare.py` | Validation: table S14 | 10 runs per method, 42 cities | `exp2_tsp_compare.csv` |
| exp3_sorting | `exp3_sorting.py` | Validation: fig. S2, table S15 | 3 runs per setting, 1000 iterations | `exp3_entropy_curve.csv`, `exp3_fig8_ants.csv`, `exp3_table2_k1k2.csv` |
| exp4_topic1_we_sense | `exp4_topic1_we_sense.py` (`EXP4_SEEDS`) | D1: Fig. 2F, table S3B | 20 seeds | `exp4a_private_vs_shared.csv`, `exp4b_perceptual_consistency.csv`, `exp4c_sorting_sensing.csv` |
| exp5_topic2_responsibility | `exp5_topic2_responsibility.py` | D2, early version (superseded by exp7) | 8 seeds | `exp5a_provenance.csv`, `exp5b_counterfactual.csv`, `exp5c_sorting_authorship.csv`, `exp5_tsp_event_log.csv`, `exp5_sorting_event_log.csv` |
| exp6_topic3_reversibility | `exp6_topic3_reversibility.py` | D3: Fig. 4C, table S11 | 4 seeds per ρ | `exp6a_block_unblock.csv`, `exp6b_cut_remove.csv`, `exp6c_sorting_scramble.csv` |
| exp7_topic2_stats | `exp7_topic2_stats.py` | D2: text S4, fig. S5, table S9 | 32 seeds; Shapley values on 10 | `exp7_counterfactual_stats.csv`, `exp7_top_vs_random.csv`, `exp7_dispersion.csv`, `exp7_group_shapley.csv` |
| exp8_topic3_controls | `exp8_topic3_controls.py` (`EXP8_SEEDS`) | D3: Fig. 4, A and B; tables S10 and S12 | 50 pairs per ρ = 0.3, 0.5, 0.9 | `exp8_topic3_controls.csv`, `exp8_topic3_stats.csv`, `exp8_trajectories.npz` |
| exp9_microgpt_ants | `exp9_microgpt_ants.py` (`EXP9_SEEDS`, `EXP9_SKIP_D`) | D1: Fig. 1E, Fig. 2, A to C; Table 1; tables S2 to S4 | 20 seeds, 30 ants, 3000 steps | `exp9a_parity.csv`, `exp9b_stigmergy.csv`, `exp9c_dialect.csv` |
| exp10_topic2_learnable | `exp10_topic2_learnable.py` (`EXP10_SEEDS`, `EXP10_SHAPLEY`) | D2: Fig. 3, Table 2, tables S6 and S7 | 20 seeds (0 to 19); Shapley values on 8 | `exp10_per_seed.csv`, `exp10_counterfactual_stats.csv`, `exp10_top_vs_random.csv`, `exp10_shapley_gpt.csv`, `exp10_shapley_rule.csv` |
| exp10b_confirmatory | `exp10_topic2_learnable.py` with `EXP10_SEED0=1000 EXP10_SHAPLEY=12 EXP10_TAG=b` | D2: Table 2, text S3, fig. S4, table S8 | 20 seeds (1000 to 1019); Shapley values on 12 | `exp10b_*.csv` (same files as exp10, plus `exp10b_noise.csv`) |
| exp11_d1_controls | `exp11_d1_controls.py` (`EXP11_SEEDS`) | D1: Fig. 2B (social learning), fig. S3, table S4 | 20 seeds per condition | `exp11_per_seed.csv` |
| exp12_learnable_return | `exp12_learnable_return.py` (`EXP12_SEEDS`) | D3: Fig. 4, D to F; fig. S6; table S13 | 20 seeds | `exp12.npy`, `exp12_stats.csv` |
| exp13_grammar_adherence | `exp13_grammar_adherence.py` (`EXP13_SEEDS`) | D1: Fig. 2, D and E; table S5 | 20 seeds | `exp13_grammar.csv`, `exp13_per_seed.csv` |
| fig_data | `fig_data.py` (`FIG_SEEDS_CURVE`, `FIG_SEEDS_BLOCK`) | Fig. 1, C and D | 20 seeds per agent class | `fig_data.npy` |
| analysis_revision | `analysis_revision.py` | Paired tests, TOST, and the prespecified exp10b tests | reads exp9, exp11, exp13, exp10b | `summary_revision.md` (generated log) |
| make_figures | `make_figures.py` | Fig. 1 to 5 | reads `results/` | `figures/paper/Fig1`–`Fig5` (.pdf, .png) |
| make_supp_figures | `make_supp_figures.py` | figs. S1 to S6 | reads `results/` | `figures/paper/FigS1`–`FigS6` (.pdf, .png) |

Environment variables in parentheses override the default sample size for that script. Part (d) of exp9 (an unpaired block-and-reopen run) is skipped by default (`EXP9_SKIP_D=1`) because exp12 replaces it with paired forks.

## Where each paper item comes from

### Main text

| Item | Content | Data | Script |
|---|---|---|---|
| Fig. 1A–B | Schematics of an ant and a trip | none | `make_figures.py` |
| Fig. 1C–D | Pheromone field; cumulative deliveries | `fig_data.npy` | `fig_data.py`, `make_figures.py` |
| Fig. 1E | Yield relative to rule-based ants | `exp9a_parity.csv` | `exp9_microgpt_ants.py` |
| Fig. 2A | Deliveries by medium | `exp9b_stigmergy.csv` | `exp9_microgpt_ants.py` |
| Fig. 2B–C | Dispersion; equivalence test | `exp13_per_seed.csv`, `exp11_per_seed.csv` | `exp13_grammar_adherence.py`, `exp11_d1_controls.py` |
| Fig. 2D–E | Legal mass; within-grammar dispersion | `exp13_per_seed.csv` | `exp13_grammar_adherence.py` |
| Fig. 2F | Collective gain in the traveling-salesman problem | `exp4a_private_vs_shared.csv` | `exp4_topic1_we_sense.py` |
| Fig. 3 | Trace versus cause | `exp10_shapley_gpt.csv`, `exp10_shapley_rule.csv`, `exp10_counterfactual_stats.csv` | `exp10_topic2_learnable.py` |
| Fig. 4A–B | Competence, medium, record | `exp8_topic3_stats.csv` | `exp8_topic3_controls.py` |
| Fig. 4C | Half-life of pheromone | `exp6a_block_unblock.csv` | `exp6_topic3_reversibility.py` |
| Fig. 4D–F | Paired return forks | `exp12.npy` | `exp12_learnable_return.py` |
| Fig. 5 | Summary diagram | none | `make_figures.py` |
| Table 1 | Yield of rule-based and learnable colonies | `exp9a_parity.csv` | `exp9_microgpt_ants.py` |
| Table 2 | Trace share versus Shapley share | `exp10_shapley_*.csv`, `exp10b_shapley_*.csv` | `exp10_topic2_learnable.py` |

### Supplementary Materials

| Item | Data | Script |
|---|---|---|
| fig. S1 | `exp1_tsp_params.csv` | `exp1_tsp_params.py` |
| fig. S2 | `exp3_entropy_curve.csv`, `exp3_fig8_ants.csv` | `exp3_sorting.py` |
| fig. S3 | `exp11_per_seed.csv` | `exp11_d1_controls.py` |
| fig. S4 | `exp10b_shapley_gpt.csv`, `exp10b_shapley_rule.csv` | exp10b |
| fig. S5 | `exp7_group_shapley.csv`, `exp7_counterfactual_stats.csv` | `exp7_topic2_stats.py` |
| fig. S6 | `exp12.npy` | `exp12_learnable_return.py` |
| table S1 | literature comparison | none |
| table S2 | `exp9a_parity.csv` | `exp9_microgpt_ants.py` |
| table S3 | `exp9b_stigmergy.csv`, `exp4a_private_vs_shared.csv` | exp9, exp4 |
| table S4 | `exp9c_dialect.csv`, `exp13_per_seed.csv`, `exp11_per_seed.csv` | exp9, exp13, exp11; `analysis_revision.py` |
| table S5 | `exp13_grammar.csv`, `exp13_per_seed.csv` | `exp13_grammar_adherence.py` |
| table S6 | `exp10_counterfactual_stats.csv`, `exp10_top_vs_random.csv` | exp10 |
| table S7 | `exp10_shapley_gpt.csv`, `exp10_shapley_rule.csv` | exp10 |
| table S8 | `exp10b_*.csv` | exp10b; `analysis_revision.py` |
| table S9 | `exp7_counterfactual_stats.csv`, `exp7_top_vs_random.csv`, `exp7_group_shapley.csv` | exp7 |
| table S10 | `exp8_topic3_stats.csv` (part `control1`) | exp8 |
| table S11 | `exp6a_block_unblock.csv`, `exp6b_cut_remove.csv` | exp6 |
| table S12 | `exp8_topic3_stats.csv` (part `control2`), `exp8_topic3_controls.csv` | exp8 |
| table S13 | `exp12_stats.csv`, `exp12.npy` | exp12 |
| table S14 | `exp2_tsp_compare.csv` | exp2 |
| table S15 | `exp3_table2_k1k2.csv` | exp3 |

## Legacy files

These files are kept for completeness but are not used by the final figures:

- `fig_data_5seeds.npy`: an earlier 5-seed version of `fig_data.npy`.
- `fig_data_null.npy`: an earlier 10-seed null model for Fig. 4F, used by `make_figures.py` only if `exp12.npy` is missing (produced by `fig_data_null.py`).
- `exp9d_block_unblock.csv`: the earlier unpaired block-and-reopen run of exp9, superseded by exp12.
- exp5 outputs: an early 8-seed version of the traveling-salesman responsibility analysis, superseded by exp7. Its event logs illustrate the event contract.
- `example_custom_policy.csv`: output of the custom-policy example, not used in the paper.
