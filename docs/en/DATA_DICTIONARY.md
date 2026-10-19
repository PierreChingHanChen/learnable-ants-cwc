English | [中文](../zh-TW/DATA_DICTIONARY.md)

# Data dictionary

Every file in `results/`, the experiment that writes it, and the meaning of its columns. Which paper figure or table uses each file is listed in [EXPERIMENTS.md](EXPERIMENTS.md).

## Shared conventions

- `seed` is the random seed of a run; rows with the same seed in different conditions are paired.
- `core` is `rule` (rule-based ants) or `gpt` (learnable ants: the behavior-cloned transformer with online self-imitation).
- `delivered` is the number of food items delivered to the nest; `short_frac` is the fraction of corridor crossings on the short corridor of the double bridge (0 on the open field).
- Summary-statistics files share the columns `mean`, `ci_lo`, `ci_hi` (95% bootstrap interval), `d_z` (paired effect size), `p` (two-sided paired Wilcoxon test), `n` (number of seeds), and, where present, `p_holm` (Holm-corrected).
- Policy divergences (`dispersion`, `drift`, `disp`, `js_*`) are Jensen-Shannon divergences in nats, read on 96 fixed probe contexts.
- Traveling-salesman gaps (`gap_pct`, `*_gap`) are percentages above the reference optimum (456.637 for the 30-city instance).
- `.npy` files are Python objects saved with `np.save(..., allow_pickle=True)`. Load the dictionaries `exp12.npy`, `fig_data.npy` and `fig_data_5seeds.npy` with `np.load(path, allow_pickle=True).item()`; `fig_data_null.npy` is an array of dictionaries (`np.load(path, allow_pickle=True)`).
- A few label columns keep the Chinese values written by the scripts: `group` in `exp10*_shapley_*.csv` (`Q1(痕跡最多)` = Q1, most trace; `Q4(痕跡最少)` = Q4, least trace), `group` in `exp7_group_shapley.csv` (`Q1(最高)` = highest; `Q4(最低)` = lowest), `condition` in `exp6b_cut_remove.csv` (`切斷介質後恢復` = recovery after cutting the medium; `移除半數螞蟻後恢復` = recovery after removing half of the ants), and `policy` in `example_custom_policy.csv` (`Ant System 式(1)` = Ant System, Eq. 1).

## Platform validation (exp1–exp3)

| File | Columns |
|---|---|
| `exp1_tsp_params.csv` | `instance` (`grid5x5` or `random30`), `param` (`n_ants`, `rho`, `alpha`, `beta`, `Q`), `value`, `seed`, `best` (best tour length after 100 cycles), `gap_pct` |
| `exp2_tsp_compare.csv` | `method` (`ACO`, `SA`, `GA`), `run`, `best` (best tour length, 42 cities), `sec` (wall-clock seconds) |
| `exp3_entropy_curve.csv` | `iteration`, `entropy` (spatial entropy E_S of the sorting grid, 0 to 1) |
| `exp3_fig8_ants.csv` | `n_ants`, `seed`, `entropy_100` (E_S after 100 iterations) |
| `exp3_table2_k1k2.csv` | `k1` (pick-up constant), `k2` (drop constant), `ES(100)`, `ES(500)`, `ES(1000)` (mean E_S after that many iterations) |

## Traveling-salesman and sorting experiments (exp4–exp8)

| File | Columns |
|---|---|
| `exp4a_private_vs_shared.csv` | `beta` (heuristic weight), `mode` (`shared` or `private` medium), `seed`, `best` (best tour length), `final_consensus` (trail-consensus index C: one minus the mean normalized entropy of each city's outgoing pheromone; 0, no preference; 1, a single shared path) |
| `exp4b_perceptual_consistency.csv` | `factor` (`delay` in cycles or `noise` standard deviation when reading the medium), `level`, `seed`, `best`, `consensus` |
| `exp4c_sorting_sensing.csv` | `condition` (`local` sensing, Gaussian sensing noise, or `blind`), `seed`, `final_entropy` |
| `exp5a_provenance.csv` | `ant`, `share` (share of the pheromone on the final best tour deposited by that ant) |
| `exp5b_counterfactual.csv` | `condition`, `removed` (ids of removed ants), `best_mean`, `best_sd` (best tour length over seeds) |
| `exp5c_sorting_authorship.csv` | `ant`, `author_share` (share of items in final clusters last dropped by that ant) |
| `exp5_tsp_event_log.csv`, `exp5_sorting_event_log.csv` | Event-contract log: `event_type` (`deposit`, `report`, ...), `timestamp`, `source_module`, `payload` (JSON), `priority`, `policy` |
| `exp6a_block_unblock.csv` | `rho`, `seed`, `pre_len` (best tour at blocking), `recovery_cycles` (cycles after blocking until the cycle-best tour came within 2% of the best tour found during the block), `blocked_edge_half_life` (measured, cycles), `theory_half_life` (ln ½ / ln ρ), `jaccard_final_vs_pre` (edge overlap of the final best tour with the tour at blocking), `edge_readopted` (whether the blocked edge is in the final best tour), `final_len` |
| `exp6b_cut_remove.csv` | `condition` (medium cut, or half of the ants removed), `seed`, `during_ratio` and `after_ratio` (mean tour length during the perturbation and 10 cycles after restoration, relative to before), `consensus_before`, `consensus_during` |
| `exp6c_sorting_scramble.csv` | `seed`, `pre_entropy`, `post_scramble` (E_S right after scrambling), `recovery_iterations` (iterations to return within 3% of the pre-scramble E_S; −1 if never), `first_descent_iterations` (iterations needed the first time) |
| `exp7_counterfactual_stats.csv` | `condition` (`top-1`, `bottom-1`, `random-1`, `top-25%`, `random-25%`, `top-50%`, `random-50%`) and the summary-statistics columns, for the change in best tour length after removal (positive is worse) |
| `exp7_top_vs_random.csv` | `k` (1, 25%, 50%) and the summary-statistics columns, for top-minus-random removal |
| `exp7_dispersion.csv` | `seed`, `gini` (Gini coefficient of provenance shares), `n_eff` (effective number of contributors), `max_share` |
| `exp7_group_shapley.csv` | `seed`, `group` (provenance quartile, Q1 highest), `provenance_share`, `shapley_share`, `v_single` (value of the group alone, L_random − L), `v_all` (value of the full colony), `synergy` ((v_all − Σ v_single) / v_all) |
| `exp8_topic3_controls.csv` | One row per run: `start` (`cold` start or `warm` start on the optimum), `rho`, `seed`, `blocked_edge`, `T1_archive_gap` (archived gap at blocking); for the unperturbed control (`ctrl_`) and perturbed run (`pert_`): `perf_gap` (mean cycle-best gap over the last 20 cycles), `archive_gap`, `J_medium` (edge Jaccard between the tour favored by the pheromone field and the one at blocking), `J_best` (same for the archived tour); `fresh_hit_<x>` (cold runs: first cycle at which the archive came within x% of the optimum, −1 if never) and `rehit_<x>` (warm runs: cycles after restoration until within x% again, −1 if never), for x = 0.0, 0.5, 1.0 |
| `exp8_topic3_stats.csv` | `part` (`control1`: paired perturbation; `control2`: refinding), `rho`, `metric`, `ctrl`, `pert` (condition means or proportions) and the summary-statistics columns. For `control1`, `mean`, `ci_lo`, `ci_hi` describe the paired difference pert − ctrl. For `control2`, `ctrl` and `pert` are the proportions of fresh colonies that found and warm colonies that refound the optimum, `ci_lo` and `ci_hi` are the Clopper–Pearson interval of `pert`, and `p` is an exact McNemar test |
| `exp8_trajectories.npz` | `keys` (`start|rho|seed` for each row), `ctrl` and `pert` (arrays of shape runs × 220: cycle-best gap in % per cycle) |

## Learnable ants (exp9–exp13)

| File | Columns |
|---|---|
| `exp9a_parity.csv` | `tag` (`rule`, `gpt_bc` = base model without learning, `gpt_learn` = learnable ants), `map` (`open_field` or `double_bridge`), `core`, `seed`, `delivered`, `short_frac`, `timeouts` (trips abandoned after 400 steps without delivery) |
| `exp9b_stigmergy.csv` | `tag` (`<core>_<medium>`, medium `shared`, `private` or `cut`), `map`, `core`, `seed`, `delivered`, `short_frac`, `timeouts` |
| `exp9c_dialect.csv` | `medium`, `seed`, `dispersion` (mean pairwise divergence between ants), `drift` (mean divergence of each ant from the base model) |
| `exp9d_block_unblock.csv` | Legacy unpaired block-and-reopen run: `core`, `pre`, `during`, `post` (short-corridor share before, during, after the block), `delivered` |
| `exp10_per_seed.csv`, `exp10b_per_seed.csv` | `core`, `seed`, `condition` (as in exp7), `d_total` (change in colony deliveries over the 1000-step test window), `d_indirect` (change in deliveries per surviving ant), `additive_expect` (minus the removed ants' own deliveries in the unperturbed future), `removed_trace` (trace share of the removed ants), `removed_direct` (their share of deliveries), `d_short` (change in short-corridor share) |
| `exp10_counterfactual_stats.csv`, `exp10b_counterfactual_stats.csv` | `core`, `outcome` (`d_total` or `d_indirect`), `condition`, summary-statistics columns, `p_holm`, `removed_trace`, `additive_expect` |
| `exp10_top_vs_random.csv`, `exp10b_top_vs_random.csv` | `core`, `k`, `outcome`, summary-statistics columns for top-minus-random removal |
| `exp10_shapley_gpt.csv`, `exp10_shapley_rule.csv`, `exp10b_shapley_*.csv` | `seed`, `group` (trace-share quartile, Q1 most trace), `trace_share`, `direct_share` (share of deliveries), `phi` (Shapley value in items), `superadd` (v(N) / Σ v({g}), repeated on each row of a seed) |
| `exp10b_noise.csv` | `core`, `seed`, and the exp10 effect columns for a second unperturbed branch with a different reseed (natural variability) |
| `exp11_per_seed.csv` | `tag` (`social` = social learning on the shared medium; `mark05_<core>_<medium>` = teacher marks with probability 0.5), `seed`, `delivered`, `short_frac`, `mark_carry_start` and `mark_carry_end` (fraction of loaded moves that deposited pheromone at the start and end of the run), `dispersion`, `dispersion_start` |
| `exp12.npy` | Dictionary with `T1` (1000, fork step), `T2` (2000, reopening step), and `blocks`: a list with one dictionary per core and seed holding `core`, `seed`, `step`, and for the blocked branch B (`blocked_`), its same-stream twin C1 (`control_`) and different-stream twin C2 (`control2_`): `frac` (short-corridor share), `n` (crossings) and `delivered` (cumulative deliveries) per recorded step; for learnable ants, `js_bc`, `js_cc`, `js_bc2` (per-ant divergence between B and C1, C1 and C2, B and C2 at the end; arrays of 30) |
| `exp12_stats.csv` | `core`, `metric` (`short_frac_diff`, `delivered_diff`, `js_excess` = JS(B, C1) − JS(C1, C2), `js_excess_alt` = JS(B, C2) − JS(C1, C2)) and the summary-statistics columns |
| `exp13_per_seed.csv` | `core`, `medium`, `seed`, `delivered`, `deploy_legal` (fraction of actions legal under the teacher grammar), `legal_mass` (policy probability on legal actions over the probes), `disp` (dispersion), `disp_within` (dispersion within the grammar) |
| `exp13_grammar.csv` | `core`, `medium`, means of `deploy_legal`, `legal_mass`, `disp`, `disp_within`, and `min_ant_mass` (legal mass of the least compliant ant) |

## Figure data

| File | Content |
|---|---|
| `fig_data.npy` | Dictionary with `curves`: one dictionary per agent class (`tag`) and seed with `step` and cumulative `delivered` on the double bridge; one entry also holds `tau` (pheromone field at the end) and `walls` for Fig. 1C. `blocks` is empty in the final version (paired forks are in `exp12.npy`); `T1` and `T2` are 1000 and 2000. |
| `fig_data_5seeds.npy` | Legacy 5-seed version of `fig_data.npy`. |
| `fig_data_null.npy` | Legacy null-model forks for Fig. 4F, an array of 10 dictionaries (used only if `exp12.npy` is missing). |
| `example_custom_policy.csv` | Output of `example_custom_policy.py`: `policy`, `best`, `consensus`. |

## Model weights

`miat_ants/foraging/weights/base_bc.npz` and `base_bc_mark05.npz` hold the parameters of the behavior-cloned base models (standard teacher; teacher that marks with probability 0.5). The `.json` files next to them record the training settings and held-out metrics (negative log-likelihood and top-1 agreement with the teacher).
