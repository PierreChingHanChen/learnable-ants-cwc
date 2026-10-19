English | [中文](../zh-TW/RESULTS.md)

# Experimental Results

This file collects the results of each experiment in the paper "Coordination without convergence: Three decouplings in learnable ant collectives" (C.-H. Chen). It is a curated copy of the text summaries that the experiment scripts write automatically (`results/summary_*.md`, in Chinese, not tracked by git) and of the revision analysis (`results/summary_revision.md`, written by `experiments/analysis_revision.py`), selected and reformatted. All numbers are as produced by the code and have not been altered.

- Unless stated otherwise, confidence intervals are 95% bootstrap intervals, written `[lo, hi]`, and tests are paired Wilcoxon signed-rank tests. exp7, exp10 and exp10b also report Holm-corrected p values; exp8 uses exact McNemar tests and Clopper–Pearson intervals for binary outcomes; the D1 equivalence tests use TOST.
- d_z is the paired effect size (Cohen's d_z).
- Per-seed data are in the CSV files under `results/`.
- The revision-analysis numbers (summary_revision) are the final 20-seed values and are merged into the relevant D1 and D2 sections.

## Overview

| Experiment | Paper claim | Script | Main CSV outputs | Seeds |
|---|---|---|---|---|
| exp1 | Platform validation (reproduces Fig. 3 of the original thesis) | `exp1_tsp_params.py` | `exp1_tsp_params.csv` | 5 repetitions per setting |
| exp2 | Platform validation (reproduces Table 1) | `exp2_tsp_compare.py` | `exp2_tsp_compare.csv` | 10 runs per method |
| exp3 | Platform validation (reproduces Figs. 7, 8 and Table 2) | `exp3_sorting.py` | `exp3_entropy_curve.csv`, `exp3_fig8_ants.csv`, `exp3_table2_k1k2.csv` | 3 |
| exp9 | D1 parity and media | `exp9_microgpt_ants.py` | `exp9a_parity.csv`, `exp9b_stigmergy.csv`, `exp9c_dialect.csv` (`exp9d_block_unblock.csv` superseded) | 20 |
| exp11 | D1 controls (social learning, learnable marking) | `exp11_d1_controls.py` | `exp11_per_seed.csv` | 20 |
| exp13 | D1 control grammar | `exp13_grammar_adherence.py` | `exp13_grammar.csv`, `exp13_per_seed.csv` | 20 |
| exp4 | D1 TSP shared vs private media | `exp4_topic1_we_sense.py` | `exp4a_private_vs_shared.csv`, `exp4b_perceptual_consistency.csv`, `exp4c_sorting_sensing.csv` | 20 |
| exp10 | D2 (exploratory) | `exp10_topic2_learnable.py` | `exp10_counterfactual_stats.csv`, `exp10_top_vs_random.csv`, `exp10_shapley_gpt.csv`, `exp10_shapley_rule.csv`, `exp10_per_seed.csv` | 20 (Shapley 8) |
| exp10b | D2 (confirmatory) | `exp10_topic2_learnable.py` (`EXP10_SEED0=1000`, `EXP10_SHAPLEY=12`, `EXP10_TAG=b`) | `exp10b_counterfactual_stats.csv`, `exp10b_top_vs_random.csv`, `exp10b_shapley_gpt.csv`, `exp10b_shapley_rule.csv`, `exp10b_noise.csv`, `exp10b_per_seed.csv` | 20, from seed 1000 (Shapley 12) |
| exp7 | D2 TSP trace vs cause | `exp7_topic2_stats.py` | `exp7_counterfactual_stats.csv`, `exp7_top_vs_random.csv`, `exp7_dispersion.csv`, `exp7_group_shapley.csv` | 32 (Shapley 10) |
| exp5 | D2 early version (superseded by exp7) | `exp5_topic2_responsibility.py` | `exp5a_provenance.csv`, `exp5b_counterfactual.csv`, `exp5c_sorting_authorship.csv`, `exp5_tsp_event_log.csv`, `exp5_sorting_event_log.csv` | 8 |
| exp8 | D3 TSP paired controls | `exp8_topic3_controls.py` | `exp8_topic3_controls.csv`, `exp8_topic3_stats.csv`, `exp8_trajectories.npz` | 50 pairs per ρ |
| exp6 | D3 half-life / forgetting | `exp6_topic3_reversibility.py` | `exp6a_block_unblock.csv`, `exp6b_cut_remove.csv`, `exp6c_sorting_scramble.csv` | 4 |
| exp12 | D3 learnable paired forks | `exp12_learnable_return.py` | `exp12_stats.csv`, `exp12.npy` | 20 |
| Revision analysis | D1, D2 synthesis | `analysis_revision.py` | (reads the exp9, exp11, exp13 and exp10b CSVs; writes `summary_revision.md`) | 20 |

All scripts are in `experiments/`; all CSV files are in `results/`.

---

## Platform validation

exp1–exp3 reproduce the ant–TSP parameter experiments, the 42-city algorithm comparison and the ant sorting system of the original 2000 thesis, to confirm the platform's basic behavior.

### exp1: Ant–TSP parameters (reproduces Fig. 3)

Setup: parameter sweeps over the number of ants m, the retention coefficient ρ, α, β and the pheromone quantity Q; 5 repetitions per setting, 100 cycles. Values are the mean gap (%) to the reference optimum. The known optimum of the 5×5 grid is 25.414 (24+√2); for the 30-city random map the reference is 456.6, the shortest tour found across all experiments.

| Parameter | Value | 5×5 grid | 30-city random |
|---|---|---|---|
| Number of ants m | 5 | 0.00% | 3.81% |
| | 10 | 0.00% | 1.37% |
| | 25 | 0.00% | 0.84% |
| | 50 | 0.00% | 0.41% |
| | 75 | 0.00% | 0.46% |
| Retention coefficient ρ | 0.1 | 0.00% | 1.07% |
| | 0.3 | 0.00% | 0.97% |
| | 0.5 | 0.00% | 0.84% |
| | 0.7 | 0.00% | 0.95% |
| | 0.9 | 0.00% | 0.74% |
| α | 0.5 | 0.00% | 0.75% |
| | 1 | 0.00% | 0.84% |
| | 2 | 0.00% | 4.00% |
| | 5 | 0.00% | 5.75% |
| | 8 | 0.00% | 8.67% |
| β | 0 | 84.34% | 123.08% |
| | 1 | 0.00% | 4.44% |
| | 2 | 0.00% | 1.12% |
| | 5 | 0.00% | 0.84% |
| | 8 | 0.00% | 1.20% |
| Pheromone quantity Q | 1 | 0.00% | 0.90% |
| | 10 | 0.00% | 0.64% |
| | 100 | 0.00% | 0.84% |
| | 1000 | 0.00% | 0.76% |
| | 10000 | 0.00% | 0.69% |

### exp2: 42-city TSP, three algorithms (reproduces Table 1)

Setup: ant colony optimization (ACO), simulated annealing (SA) and a genetic algorithm (GA), 10 runs each. The original thesis's 42-city coordinates are no longer available, so 42 cities generated from a fixed random seed are used instead.

| Method | Best | Mean best | SD | Mean seconds |
|---|---|---|---|---|
| ACO | 517.2 | 518.2 | 2.2 | 7.1 |
| SA | 516.7 | 522.5 | 8.9 | 2.8 |
| GA | 521.4 | 549.7 | 19.4 | 10.4 |

### exp3: Ant sorting system (reproduces Figs. 7, 8 and Table 2)

Setup: sorting is measured by the spatial entropy E_S. Fig. 7: convergence over 1000 iterations; Fig. 8: E_S after 100 iterations for different numbers of ants; Table 2: effect of k1 and k2 on E_S at 100/500/1000 iterations (mean of 3 runs).

- Fig. 7: E_S falls from 0.917 to 0.572 (minimum 0.325)
- Fig. 8: 10 ants→0.696, 20 ants→0.640, 50 ants→0.494, 100 ants→0.350

| k1 | k2 | E_S(100) | E_S(500) | E_S(1000) |
|---|---|---|---|---|
| 0.05 | 0.1 | 0.614 | 0.341 | 0.384 |
| 0.05 | 0.15 | 0.552 | 0.341 | 0.299 |
| 0.05 | 0.2 | 0.52 | 0.362 | 0.242 |
| 0.05 | 0.3 | 0.537 | 0.278 | 0.278 |
| 0.02 | 0.2 | 0.573 | 0.508 | 0.441 |
| 0.04 | 0.2 | 0.579 | 0.388 | 0.359 |
| 0.08 | 0.2 | 0.498 | 0.334 | 0.247 |
| 0.15 | 0.2 | 0.367 | 0.232 | 0.253 |

---

## D1: Coordination without convergence

### exp9: microGPT ants — parity, media and dialects

Setup: 30 ants, 3000 steps, 20 seeds; each ant is a language model of about 4k parameters (24 tokens, context 16). Three cores are compared: rule-based ants, the GPT (BC) base model (behavior cloning of the rule-based ants, no learning), and learnable ants (GPT, BC + online learning by online self-imitation). (a) Parity on two maps; (b) shared medium / private media / cut medium on the double bridge; (c) between-ant dispersion (dialect) and drift from the BC base model, measured on a fixed set of 96 probe contexts.

**(a) Parity and learning**

| Map | Core | Deliveries mean [95% CI] | Relative to rule-based | Short-corridor share | Timed-out episodes |
|---|---|---|---|---|---|
| `open_field` | Rule-based ants | 2760 [2731, 2788] | 1.00 | — | 0 |
| `open_field` | GPT (BC) | 2960 [2936, 2983] | 1.07 | — | 0 |
| `open_field` | GPT (BC + online learning) | 3064 [3019, 3111] | 1.11 | — | 1 |
| `double_bridge` | Rule-based ants | 443 [429, 458] | 1.00 | 0.798 | 49 |
| `double_bridge` | GPT (BC) | 511 [491, 534] | 1.15 | 0.834 | 37 |
| `double_bridge` | GPT (BC + online learning) | 607 [576, 637] | 1.37 | 0.865 | 35 |

(`open_field` has no corridors, so the short-corridor share does not apply; the raw output is `nan`.)

Paired comparisons (revision analysis):

- [`open_field`] learning − rule-based: +304.4 [+263.5, +350.1] (d_z = +3.06, Wilcoxon p = 1.91e-06, n = 20); learning − BC: +104.4 [+55.0, +155.4] (d_z = +0.90, Wilcoxon p = 0.00121, n = 20)
- [`double_bridge`] learning − rule-based: +163.7 [+130.0, +194.7] (d_z = +2.14, Wilcoxon p = 1.91e-06, n = 20); learning − BC: +95.2 [+62.3, +127.0] (d_z = +1.26, Wilcoxon p = 0.000338, n = 20)

**(b) Stigmergy: medium conditions (double bridge)**

| Core | Medium | Deliveries [95% CI] | Short-corridor share | Marking rate while searching | Marking rate while carrying |
|---|---|---|---|---|---|
| Rule-based ants | Shared medium | 443 [429, 458] | 0.798 | 0.000 | 1.000 |
| Rule-based ants | Private media | 295 [288, 302] | 0.684 | 0.000 | 1.000 |
| Rule-based ants | Cut medium | 232 [226, 238] | 0.619 | 0.000 | 1.000 |
| Learnable ants (BC + online learning) | Shared medium | 607 [576, 637] | 0.865 | 0.000 | 0.989 |
| Learnable ants (BC + online learning) | Private media | 385 [374, 396] | 0.743 | 0.000 | 0.989 |
| Learnable ants (BC + online learning) | Cut medium | 239 [232, 246] | 0.609 | 0.000 | 0.974 |

Paired comparisons (revision analysis):

- [Learnable ants] shared − private deliveries: +221.3 [+192.5, +249.6] (d_z = +3.30, Wilcoxon p = 1.91e-06, n = 20); ratio 1.57
- [Rule-based ants] shared − private deliveries: +147.6 [+132.9, +163.2] (d_z = +4.11, Wilcoxon p = 8.83e-05, n = 20); ratio 1.50

**(c) Dialects and conventions (learnable ants, fixed set of 96 probe contexts)**

| Medium | Final between-ant dispersion (nats) [95% CI] | Drift from the BC base model [95% CI] |
|---|---|---|
| Shared medium | 0.0403 [0.0380, 0.0426] | 0.0226 [0.0215, 0.0237] |
| Private media | 0.0393 [0.0368, 0.0418] | 0.0220 [0.0207, 0.0233] |
| Cut medium | 0.0295 [0.0269, 0.0322] | 0.0164 [0.0150, 0.0178] |

D1 dispersion (primary equivalence test, revision analysis). The equivalence bound was written into the draft before the extended runs, as ±10% of the mean private-media dispersion; TOST uses two one-sided paired t tests, p_TOST = max(p_lower, p_upper), confirmed by checking whether the 90% bootstrap interval lies entirely within the bound.

- Dispersion: shared 0.0403, private 0.0393, cut 0.0295 nats
- Shared − private: +0.0010 [-0.0019, +0.0040] (d_z = +0.14, Wilcoxon p = 0.522, n = 20)
- TOST: difference = +0.0010, equivalence bound ±0.0039, 90% CI [-0.0015, +0.0035], p_TOST = 0.0366, within the equivalence bound
- Drift: shared 0.0226, private 0.0220; difference +0.0006 [-0.0008, +0.0020] (d_z = +0.17, Wilcoxon p = 0.546, n = 20)
- Cut − private dispersion: -0.0098 [-0.0136, -0.0060] (d_z = -1.10, Wilcoxon p = 6.29e-05, n = 20)

The exp9 summary and the revision analysis agree on all numbers.

**Status**: Part (d) of the script (blocking and unblocking the short corridor) no longer runs by default (`EXP9_SKIP_D=1`), so the exp9 summary has no (d); `results/exp9d_block_unblock.csv` is the output of an earlier run. The unpaired observation from that run — the learnable ants' short-corridor share rose from 0.80 before blocking to 0.89 after unblocking — is superseded by the paired forks of exp12: the rise came from continued learning, not from the block itself (see exp12).

### exp11: Two controls for D1

Setup: (a) Social-learning positive control: social learning is switched on under the shared medium (each ant also imitates other ants' successful episodes); the comparison group is exp9's shared-medium learnable ants with the same seeds and no social learning. If the dispersion measure can detect convergence, social learning should reduce dispersion. (b) Learnable marking: a new base model is behavior-cloned from a teacher that marks only with probability 0.5 while carrying, which leaves room for online learning to change marking; dispersion, change in marking rate and deliveries are compared under shared and private media, with a rule-based teacher under the same condition (mark_p 0.5) as reference. 20 seeds. exp11 has no separate summary; all numbers below come from the revision analysis.

**(a) Social-learning positive control**

- Shared-medium dispersion: without social learning 0.0403, with social learning 0.0030 nats (93% decrease)
- Paired difference (social − no social): -0.0373 [-0.0401, -0.0344] (d_z = -5.70, Wilcoxon p = 1.91e-06, n = 20)
- Decrease in every seed: 20/20
- Deliveries (social − no social): +2.2 [-39.4, +38.8] (d_z = +0.02, Wilcoxon p = 0.538, n = 20)

**(b) Learnable marking (teacher marking probability 0.5)**

- GPT deliveries: shared 453, private 259; difference +193.8 [+167.4, +221.8] (d_z = +3.03, Wilcoxon p = 8.84e-05, n = 20); ratio 1.75
- Rule-based ants (mark_p 0.5) deliveries: shared 347, private 242
- GPT dispersion: shared 0.0689, private 0.0773; difference -0.0084 [-0.0122, -0.0044] (d_z = -0.91, Wilcoxon p = 0.000851, n = 20)
- TOST: difference = -0.0084, equivalence bound ±0.0077, 90% CI [-0.0116, -0.0050], p_TOST = 0.622, not entirely within the equivalence bound
- Marking rate while carrying (shared): start 0.437 → end 0.472; change +0.035 [-0.003, +0.075] (d_z = +0.38, Wilcoxon p = 0.143, n = 20)
- Marking rate while carrying (private): start 0.441 → end 0.485; change +0.043 [+0.001, +0.086] (d_z = +0.45, Wilcoxon p = 0.024, n = 20)
- End marking rate, shared − private: -0.013 [-0.030, +0.004] (d_z = -0.32, Wilcoxon p = 0.202, n = 20)
- Rule-based ants (mark_p 0.5) marking rate: 0.499

### exp13: Diverging but lawful? — control grammar

Setup: double bridge, 30 ants, 3000 steps, 20 seeds. The rule-based ants' finite-state control logic is written as a "grammar": each percept token maps to a set of legal actions. Deployment legality = the fraction of executed actions that belong to the legal set of the preceding percept token; legal mass (probe) = the probability each ant puts on legal actions across 96 probe contexts (averaged); within-grammar dispersion = the mean pairwise JS after restricting each ant's distribution to the legal set and renormalizing. The question is whether the divergence produced by learning (exp9c) violates the control logic or consists of different choices within the space the grammar allows.

- Legal mass of the behavior-cloned base model on the probes = 0.9992

| Core | Medium | Deployment legality [95% CI] | Probe legal mass (final) [95% CI] | Lowest single ant | Total dispersion | Within-grammar dispersion |
|---|---|---|---|---|---|---|
| Rule-based ants | Shared medium | 1.0000 [1.0000, 1.0000] | — | — | — | — |
| Learnable ants (BC + online learning) | Shared medium | 0.9963 [0.9954, 0.9972] | 0.9859 [0.9843, 0.9873] | 0.8432 | 0.0403 | 0.0274 |
| Rule-based ants | Private media | 1.0000 [1.0000, 1.0000] | — | — | — | — |
| Learnable ants (BC + online learning) | Private media | 0.9973 [0.9961, 0.9981] | 0.9879 [0.9863, 0.9895] | 0.8506 | 0.0393 | 0.0285 |

- [Shared] change in legal mass from before to after learning = -0.0133 [-0.0148, -0.0118], p = 1.91e-06; within-grammar dispersion / total dispersion = 0.68
- [Private] change in legal mass from before to after learning = -0.0113 [-0.0129, -0.0096], p = 1.91e-06; within-grammar dispersion / total dispersion = 0.73
- Deployment legality, shared − private (paired) = -0.0010 [-0.0019, -0.0000], p = 0.0759
- Legal mass, shared − private (revision analysis): -0.0020 [-0.0041, +0.0002] (d_z = -0.40, Wilcoxon p = 0.114, n = 20)

The exp13 summary and the revision analysis agree on all numbers; the paired shared − private difference in legal mass appears only in the revision analysis.

### exp4: Shared medium vs private media on the TSP (We-sense)

Setup: the same ant algorithm (30 cities, 30 ants) with either private media (one copy per ant, "I") or a shared medium ("We"); collective gain G = L_private / L_shared, and C is the path-consensus index. (b) tests read delay d and read noise σ on the medium (perceptual consistency, Section 5.1.1 of the original thesis); (c) compares, in the sorting system, local sensing, noisy sensing and no sensing of the medium (blind). 20 runs.

**(a) 30 cities, 20 runs**

| β | L_private (I) | L_shared (We) | Collective gain G | C_private | C_shared |
|---|---|---|---|---|---|
| 1.0 | 594.0 | 470.4 | 1.263 | 0.313 | 0.460 |
| 2.0 | 509.7 | 460.2 | 1.108 | 0.449 | 0.602 |
| 5.0 | 471.1 | 459.5 | 1.025 | 0.582 | 0.649 |

**(b) Perceptual consistency** (values are tour lengths)

- Read delay d (cycles): 0→460.2, 1→459.4, 3→459.2, 6→459.5
- Read noise σ: 0.0→460.2, 0.5→461.0, 1.0→468.5, 2.0→523.1

**(c) Sorting system** (final E_S)

- local: 0.457
- noise σ=0.2: 0.608
- noise σ=0.5: 0.848
- blind: 0.900

---

## D2: Traces overstate how concentrated responsibility is

### exp10: Trace vs cause in learnable ants (exploratory)

Setup: double bridge, 30 ants; after a 2000-step warm-up (online learning, provenance tracking) the system is forked and run for a 1000-step test window; 20 seeds (paired), group Shapley on 8 seeds. Trace share = each ant's share of the pheromone on perceivable paths (τ ≥ threshold) during the second half of the warm-up (time-averaged). Branches remove ants ranked by trace share: top-1 / bottom-1 / random-1 / top-25% / random-25% / top-50% / random-50%; a full branch with a different reseed measures natural variability. Δ_total = change in total deliveries; Δ_indirect = change in deliveries per surviving ant (the removed ants' causal contribution to others through the medium, excluding their own direct output). Group Shapley: ants are split into four quartile groups by trace share, and v(S) = test-window deliveries when only groups S are kept. Rule-based ants go through exactly the same procedure as a control.

#### Learnable ants (GPT, learning)

- Trace dispersion: Gini = 0.200 (95% CI 0.185–0.217); N_eff = 26.4 / 30
- Trace share vs warm-up direct output: Spearman ρ = +0.592 (p=4.9e-58, n=600)
- Full-colony test-window deliveries = 228.5; natural variability (reseed) mean |Δ_total| = 31.4, mean |Δ_indirect| = 1.047

Δ_indirect (change in deliveries per surviving ant)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.064 | -6.8 | +0.193 | [-0.316, +0.702] | +0.16 | 0.411 | 1 |
| bottom-1 | 0.012 | -5.9 | +0.160 | [-0.419, +0.722] | +0.12 | 0.398 | 1 |
| random-1 | 0.034 | -7.3 | +0.034 | [-0.681, +0.731] | +0.02 | 0.881 | 1 |
| top-25% | 0.348 | -58.2 | -0.485 | [-1.054, +0.115] | -0.35 | 0.14 | 0.701 |
| random-25% | 0.239 | -52.9 | -0.163 | [-0.785, +0.493] | -0.11 | 0.695 | 1 |
| top-50% | 0.643 | -124.2 | -0.580 | [-1.183, +0.060] | -0.40 | 0.0825 | 0.495 |
| random-50% | 0.507 | -114.2 | -0.827 | [-1.333, -0.277] | -0.68 | 0.0111 | 0.0777 |

Δ_total (change in total deliveries)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.064 | -6.8 | -1.2 | [-16.4, +13.8] | -0.04 | 1 | 1 |
| bottom-1 | 0.012 | -5.9 | -1.2 | [-18.4, +15.5] | -0.03 | 0.911 | 1 |
| random-1 | 0.034 | -7.3 | -6.3 | [-27.2, +14.1] | -0.13 | 0.502 | 1 |
| top-25% | 0.348 | -58.2 | -69.4 | [-86.2, -52.2] | -1.75 | 0.00012 | 0.000619 |
| random-25% | 0.239 | -52.9 | -56.6 | [-73.3, -39.2] | -1.42 | 0.000151 | 0.000619 |
| top-50% | 0.643 | -124.2 | -132.8 | [-149.3, -116.0] | -3.39 | 8.84e-05 | 0.000619 |
| random-50% | 0.507 | -114.2 | -126.7 | [-142.0, -111.2] | -3.55 | 8.84e-05 | 0.000619 |

Removal by trace vs random removal of the same number (paired; negative = removal by trace hurts more)

| k | Measure | Δ(top) − Δ(random) | 95% CI | d_z | Wilcoxon p |
|---|---|---|---|---|---|
| 1 | d_indirect | +0.159 | [-0.236, +0.534] | +0.18 | 0.355 |
| 1 | d_total | +5.0 | [-6.1, +15.7] | +0.20 | 0.26 |
| 25% | d_indirect | -0.322 | [-0.941, +0.285] | -0.23 | 0.351 |
| 25% | d_total | -12.8 | [-25.9, +0.0] | -0.43 | 0.1 |
| 50% | d_indirect | +0.247 | [-0.353, +0.850] | +0.18 | 0.469 |
| 50% | d_total | -6.2 | [-15.2, +3.1] | -0.29 | 0.232 |

Group Shapley values

| Group | Trace share | Direct share | Shapley share |
|---|---|---|---|
| Q1 (most trace) | 0.396 | 0.296 | 0.309 |
| Q2 | 0.278 | 0.270 | 0.265 |
| Q3 | 0.193 | 0.226 | 0.222 |
| Q4 (least trace) | 0.134 | 0.208 | 0.204 |

- Trace share vs Shapley share: Spearman ρ = +0.694 (p=1.1e-05, n=32)
- Direct share vs Shapley share: Spearman ρ = +0.752 (p=6.8e-07)
- Superadditivity v(N)/Σ v({g}) = 1.297 (95% CI 1.171–1.410; >1 means the groups together achieve more than the sum of each alone: synergy in the medium)

#### Rule-based ants

- Trace dispersion: Gini = 0.210 (95% CI 0.198–0.223); N_eff = 26.3 / 30
- Trace share vs warm-up direct output: Spearman ρ = +0.660 (p=2.6e-76, n=600)
- Full-colony test-window deliveries = 161.8; natural variability (reseed) mean |Δ_total| = 27.2, mean |Δ_indirect| = 0.908

Δ_indirect (change in deliveries per surviving ant)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.063 | -5.5 | -0.526 | [-0.941, -0.119] | -0.55 | 0.0206 | 0.0823 |
| bottom-1 | 0.011 | -5.3 | -0.174 | [-0.545, +0.166] | -0.21 | 0.422 | 1 |
| random-1 | 0.031 | -5.5 | +0.012 | [-0.514, +0.495] | +0.01 | 0.658 | 1 |
| top-25% | 0.351 | -37.2 | -0.478 | [-0.828, -0.161] | -0.61 | 0.0148 | 0.0742 |
| random-25% | 0.238 | -37.1 | +0.035 | [-0.567, +0.557] | +0.03 | 0.49 | 1 |
| top-50% | 0.651 | -80.9 | -1.030 | [-1.493, -0.603] | -1.01 | 0.000424 | 0.00297 |
| random-50% | 0.509 | -80.3 | -1.127 | [-1.620, -0.630] | -0.98 | 0.0015 | 0.00899 |

Δ_total (change in total deliveries)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.063 | -5.5 | -20.8 | [-33.0, -8.8] | -0.73 | 0.00744 | 0.0223 |
| bottom-1 | 0.011 | -5.3 | -10.3 | [-21.0, -0.8] | -0.44 | 0.0701 | 0.14 |
| random-1 | 0.031 | -5.5 | -5.1 | [-20.6, +9.4] | -0.14 | 0.478 | 0.478 |
| top-25% | 0.351 | -37.2 | -48.2 | [-58.2, -39.0] | -2.14 | 8.84e-05 | 0.000617 |
| random-25% | 0.238 | -37.1 | -36.4 | [-51.5, -22.5] | -1.08 | 0.000253 | 0.00101 |
| top-50% | 0.651 | -80.9 | -96.3 | [-107.7, -85.6] | -3.80 | 8.82e-05 | 0.000617 |
| random-50% | 0.509 | -80.3 | -97.2 | [-108.2, -86.5] | -3.84 | 8.84e-05 | 0.000617 |

Removal by trace vs random removal of the same number (paired; negative = removal by trace hurts more)

| k | Measure | Δ(top) − Δ(random) | 95% CI | d_z | Wilcoxon p |
|---|---|---|---|---|---|
| 1 | d_indirect | -0.538 | [-1.040, -0.048] | -0.46 | 0.0731 |
| 1 | d_total | -15.7 | [-29.9, -1.5] | -0.47 | 0.1 |
| 25% | d_indirect | -0.513 | [-0.946, -0.080] | -0.51 | 0.0641 |
| 25% | d_total | -11.8 | [-21.5, -2.3] | -0.53 | 0.067 |
| 50% | d_indirect | +0.097 | [-0.453, +0.650] | +0.08 | 0.701 |
| 50% | d_total | +0.9 | [-7.2, +9.3] | +0.05 | 0.808 |

Group Shapley values

| Group | Trace share | Direct share | Shapley share |
|---|---|---|---|
| Q1 (most trace) | 0.396 | 0.268 | 0.277 |
| Q2 | 0.289 | 0.272 | 0.265 |
| Q3 | 0.194 | 0.213 | 0.218 |
| Q4 (least trace) | 0.121 | 0.248 | 0.240 |

- Trace share vs Shapley share: Spearman ρ = +0.457 (p=0.0086, n=32)
- Direct share vs Shapley share: Spearman ρ = +0.187 (p=0.3)
- Superadditivity v(N)/Σ v({g}) = 1.229 (95% CI 1.114–1.355; >1 means the groups together achieve more than the sum of each alone: synergy in the medium)

**Status**: exp10 is exploratory. Its rule-based result that "removing the top-trace ants hurts survivors more" (d_indirect at k = 1 and k = 25%) did not replicate in the confirmatory rerun exp10b (see next section).

### exp10b: Confirmatory rerun of D2

Setup: the same procedure and code as exp10 (`exp10_topic2_learnable.py`) with fresh seeds (from 1000); 20 seeds (paired), group Shapley on 12 seeds.

#### Learnable ants (GPT, learning)

- Trace dispersion: Gini = 0.185 (95% CI 0.172–0.200); N_eff = 27.0 / 30
- Trace share vs warm-up direct output: Spearman ρ = +0.630 (p=8.4e-68, n=600)
- Full-colony test-window deliveries = 240.8; natural variability (reseed) mean |Δ_total| = 23.3, mean |Δ_indirect| = 0.777

Δ_indirect (change in deliveries per surviving ant)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.056 | -7.6 | -0.116 | [-0.838, +0.616] | -0.07 | 0.747 | 1 |
| bottom-1 | 0.010 | -5.7 | -0.207 | [-0.747, +0.353] | -0.16 | 0.467 | 1 |
| random-1 | 0.036 | -8.3 | +0.072 | [-0.352, +0.591] | +0.07 | 0.695 | 1 |
| top-25% | 0.333 | -61.7 | -0.670 | [-1.250, -0.037] | -0.47 | 0.05 | 0.25 |
| random-25% | 0.236 | -53.5 | -0.535 | [-1.054, -0.007] | -0.44 | 0.0892 | 0.357 |
| top-50% | 0.632 | -127.2 | -1.167 | [-1.853, -0.457] | -0.72 | 0.0126 | 0.0755 |
| random-50% | 0.509 | -119.2 | -1.403 | [-1.850, -0.953] | -1.36 | 0.000218 | 0.00152 |

Δ_total (change in total deliveries)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.056 | -7.6 | -10.9 | [-31.9, +10.3] | -0.23 | 0.205 | 0.421 |
| bottom-1 | 0.010 | -5.7 | -11.7 | [-28.0, +5.0] | -0.31 | 0.204 | 0.421 |
| random-1 | 0.036 | -8.3 | -6.2 | [-18.9, +8.9] | -0.19 | 0.14 | 0.421 |
| top-25% | 0.333 | -61.7 | -77.1 | [-93.2, -59.8] | -1.95 | 8.84e-05 | 0.000529 |
| random-25% | 0.236 | -53.5 | -65.8 | [-79.2, -51.9] | -2.05 | 8.82e-05 | 0.000529 |
| top-50% | 0.632 | -127.2 | -144.7 | [-161.2, -126.7] | -3.57 | 8.84e-05 | 0.000529 |
| random-50% | 0.509 | -119.2 | -140.2 | [-151.7, -128.0] | -5.04 | 1.91e-06 | 1.34e-05 |

Removal by trace vs random removal of the same number (paired; negative = removal by trace hurts more)

| k | Measure | Δ(top) − Δ(random) | 95% CI | d_z | Wilcoxon p |
|---|---|---|---|---|---|
| 1 | d_indirect | -0.188 | [-0.741, +0.329] | -0.15 | 0.778 |
| 1 | d_total | -4.7 | [-20.6, +10.1] | -0.13 | 0.747 |
| 25% | d_indirect | -0.135 | [-0.654, +0.426] | -0.11 | 0.538 |
| 25% | d_total | -11.3 | [-25.2, +3.0] | -0.34 | 0.145 |
| 50% | d_indirect | +0.237 | [-0.523, +1.020] | +0.13 | 0.674 |
| 50% | d_total | -4.5 | [-17.1, +8.7] | -0.15 | 0.444 |

Group Shapley values

| Group | Trace share | Direct share | Shapley share |
|---|---|---|---|
| Q1 (most trace) | 0.379 | 0.300 | 0.294 |
| Q2 | 0.291 | 0.267 | 0.296 |
| Q3 | 0.201 | 0.230 | 0.224 |
| Q4 (least trace) | 0.129 | 0.203 | 0.186 |

- Trace share vs Shapley share: Spearman ρ = +0.723 (p=6.5e-09, n=48)
- Direct share vs Shapley share: Spearman ρ = +0.770 (p=1.6e-10)
- Superadditivity v(N)/Σ v({g}) = 1.284 (95% CI 1.205–1.361; >1 means the groups together achieve more than the sum of each alone: synergy in the medium)

#### Rule-based ants

- Trace dispersion: Gini = 0.208 (95% CI 0.195–0.223); N_eff = 26.3 / 30
- Trace share vs warm-up direct output: Spearman ρ = +0.663 (p=2.3e-77, n=600)
- Full-colony test-window deliveries = 156.3; natural variability (reseed) mean |Δ_total| = 26.0, mean |Δ_indirect| = 0.867

Δ_indirect (change in deliveries per surviving ant)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.063 | -5.5 | -0.186 | [-0.597, +0.197] | -0.20 | 0.469 | 1 |
| bottom-1 | 0.010 | -5.8 | -0.133 | [-0.543, +0.281] | -0.14 | 0.654 | 1 |
| random-1 | 0.035 | -5.0 | +0.062 | [-0.414, +0.581] | +0.05 | 0.904 | 1 |
| top-25% | 0.350 | -36.5 | -0.196 | [-0.559, +0.191] | -0.22 | 0.376 | 1 |
| random-25% | 0.242 | -36.5 | -0.074 | [-0.543, +0.404] | -0.07 | 0.737 | 1 |
| top-50% | 0.648 | -77.5 | -1.010 | [-1.460, -0.573] | -0.97 | 0.000885 | 0.0062 |
| random-50% | 0.503 | -78.3 | -0.727 | [-1.197, -0.263] | -0.67 | 0.0144 | 0.0865 |

Δ_total (change in total deliveries)

| Condition | Trace share of removed | Additive expectation Δ | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm p |
|---|---|---|---|---|---|---|---|
| top-1 | 0.063 | -5.5 | -10.9 | [-23.4, +0.7] | -0.39 | 0.0617 | 0.185 |
| bottom-1 | 0.010 | -5.8 | -9.7 | [-22.0, +2.8] | -0.34 | 0.145 | 0.29 |
| random-1 | 0.035 | -5.0 | -3.1 | [-17.1, +12.0] | -0.09 | 0.507 | 0.507 |
| top-25% | 0.350 | -36.5 | -41.0 | [-51.1, -29.9] | -1.68 | 1.34e-05 | 9.35e-05 |
| random-25% | 0.242 | -36.5 | -38.2 | [-49.4, -26.7] | -1.46 | 0.000219 | 0.000875 |
| top-50% | 0.648 | -77.5 | -92.6 | [-102.6, -82.0] | -3.88 | 8.84e-05 | 0.000531 |
| random-50% | 0.503 | -78.3 | -89.2 | [-100.3, -78.0] | -3.44 | 8.84e-05 | 0.000531 |

Removal by trace vs random removal of the same number (paired; negative = removal by trace hurts more)

| k | Measure | Δ(top) − Δ(random) | 95% CI | d_z | Wilcoxon p |
|---|---|---|---|---|---|
| 1 | d_indirect | -0.248 | [-0.686, +0.155] | -0.25 | 0.472 |
| 1 | d_total | -7.8 | [-20.6, +4.2] | -0.26 | 0.349 |
| 25% | d_indirect | -0.122 | [-0.550, +0.315] | -0.12 | 0.388 |
| 25% | d_total | -2.8 | [-11.2, +5.7] | -0.14 | 0.501 |
| 50% | d_indirect | -0.283 | [-0.680, +0.147] | -0.29 | 0.227 |
| 50% | d_total | -3.4 | [-9.1, +2.7] | -0.25 | 0.239 |

Group Shapley values

| Group | Trace share | Direct share | Shapley share |
|---|---|---|---|
| Q1 (most trace) | 0.393 | 0.274 | 0.257 |
| Q2 | 0.289 | 0.261 | 0.267 |
| Q3 | 0.196 | 0.238 | 0.240 |
| Q4 (least trace) | 0.122 | 0.227 | 0.236 |

- Trace share vs Shapley share: Spearman ρ = +0.238 (p=0.1, n=48)
- Direct share vs Shapley share: Spearman ρ = +0.186 (p=0.21)
- Superadditivity v(N)/Σ v({g}) = 1.370 (95% CI 1.269–1.478; >1 means the groups together achieve more than the sum of each alone: synergy in the medium)

#### Revision analysis: trace share vs Shapley share (12 Shapley seeds)

| Core | Group | Trace share | Shapley share | Difference [95% CI] | d_z | Wilcoxon p | One-sided p |
|---|---|---|---|---|---|---|---|
| Learnable ants | Q1 | 0.379 | 0.294 | +0.085 [+0.056, +0.116] | +1.57 | 0.000977 | 0.000488 |
| Learnable ants | Q4 | 0.129 | 0.186 | -0.057 [-0.076, -0.040] | -1.77 | 0.000488 | 0.000244 |
| Rule-based ants | Q1 | 0.393 | 0.257 | +0.136 [+0.115, +0.156] | +3.60 | 0.000488 | 0.000244 |
| Rule-based ants | Q4 | 0.122 | 0.236 | -0.115 [-0.143, -0.082] | -2.05 | 0.000977 | 0.000488 |

(n = 12.)

- Superadditivity: learnable ants 1.284 [1.205, 1.361], rule-based ants 1.370 [1.269, 1.478]; one-sided p (> 1) = 0.000244 for both
- ρ(trace, Shapley): learnable ants +0.723, rule-based ants +0.238; ρ(direct output, Shapley): learnable ants +0.770, rule-based ants +0.186

Pre-specified test: does learning shift contribution toward direct output?

- Within each seed, the difference between the slopes of Shapley share on direct share and on trace share (direct − trace): learnable ants +0.590, rule-based ants +0.012
- Difference (GPT − rule-based, paired by seed): +0.578 [+0.081, +1.023] (d_z = +0.66, Wilcoxon p = 0.0522, n = 12); one-sided p (GPT > rule-based) = 0.0261

In the revision analysis, the values for "removal by trace vs random removal (indirect effect)" and "total effect of single removals (GPT)" are identical to the exp10b tables above.

### exp7: Trace vs cause on the TSP (statistical reinforcement)

Setup: 30 cities, 20 heterogeneous ants (individual disposition h=0.5), 100 cycles, 32 seeds (paired design). Individuals are removed by their rank in pheromone provenance share (trace), and Δ = L(removed) − L(full) (best tour length; larger is worse). The second attribution method is group Shapley values (10 seeds) with v(S) = L_random − L(S).

**(1) Paired counterfactuals: change in best tour length Δ after removal**

| Condition | Mean Δ | 95% CI | d_z | Wilcoxon p | Holm-corrected p |
|---|---|---|---|---|---|
| top-1 | -0.05 | [-0.92, +0.88] | -0.02 | 0.652 | 1 |
| bottom-1 | +1.34 | [+0.10, +2.80] | +0.34 | 0.0828 | 0.343 |
| random-1 | -0.09 | [-1.04, +0.86] | -0.03 | 0.868 | 1 |
| top-25% | +0.07 | [-0.95, +1.21] | +0.02 | 0.659 | 1 |
| random-25% | +1.20 | [+0.17, +2.50] | +0.35 | 0.0359 | 0.215 |
| top-50% | +0.72 | [-0.10, +1.52] | +0.31 | 0.0687 | 0.343 |
| random-50% | +2.85 | [+1.10, +4.79] | +0.52 | 0.00709 | 0.0496 |

Removal by provenance share vs random removal of the same number (paired)

| k | Mean Δ(top) − Δ(random) | 95% CI | d_z | Wilcoxon p |
|---|---|---|---|---|
| 1 | +0.04 | [-0.89, +1.00] | +0.01 | 1 |
| 25% | -1.13 | [-2.16, -0.13] | -0.39 | 0.0757 |
| 50% | -2.13 | [-4.16, -0.31] | -0.38 | 0.115 |

**(2) Dispersion of responsibility (across seeds)**

- Gini = 0.056, 95% CI 0.053–0.060
- N_eff = 19.79 / 20, 95% CI 19.76–19.82
- Largest single share = 0.059, 95% CI 0.058–0.061 (equal split = 0.050)
- Individual disposition vs contribution share: Spearman ρ(α, share) = +0.571 (p=1.2e-56); ρ(β, share) = +0.126 (p=0.0014), n=640

**(3) Second attribution method: group Shapley values (10 seeds)**

v(S) = L_random − L(S), L_random = 1528.3 (expected length of a random tour)

| Group (quartile by provenance share) | Provenance share | Shapley share |
|---|---|---|
| Q1 (highest) | 0.282 | 0.244 |
| Q2 | 0.258 | 0.251 |
| Q3 | 0.240 | 0.252 |
| Q4 (lowest) | 0.220 | 0.253 |

- Spearman ρ between the two attributions = -0.674 (p=1.9e-06, n=40)
- Single-group sufficiency = mean_g v({g}) / v(N) = 0.9918, 95% CI 0.9903–0.9934 (close to 1 = any quarter of the colony alone achieves almost the whole result: the outcome is "overdetermined" and no group is a necessary condition)
- Note: v is measured against a random tour, so sufficiency measures achievement "relative to disorder"; for differences in the last few percent of quality, see the paired counterfactuals in (1).

### exp5: Distributed responsibility (early version)

Setup: 30 cities, 20 ants. (a) Provenance: which ant deposited the pheromone on the final best tour; (b) counterfactual removal compared with natural variability; (c) authorship of the final clusters in the sorting system and the number of ants that handled each item. Every judgment traces back to the event log.

- (a) Best tour L=461.3; share of initial environmental pheromone 1.52e-32; ant contribution Gini=0.070, N_eff=19.7/20; largest single contribution 0.064
- (b0) Interchangeability in a homogeneous colony: with the same seed, removing any one of the 20 ants gives number of distinct outcomes = 1 (=1 means individual identity is causally irrelevant; only the number matters)
- (b) Counterfactuals in a heterogeneous colony (h=0.5) (8 seeds): full colony 461.2 ± 1.3
  - remove top-1 contributor: 460.7 ± 2.2 (Δ=-0.4; Δ/natural variability=-0.34)
  - remove bottom-1 contributor: 461.1 ± 1.4 (Δ=-0.1; Δ/natural variability=-0.09)
  - remove top 25% contributors: 461.8 ± 4.0 (Δ=+0.7; Δ/natural variability=+0.50)
  - remove random 25%: 461.4 ± 1.8 (Δ=+0.2; Δ/natural variability=+0.15)
  - remove top 50% contributors: 464.5 ± 4.7 (Δ=+3.3; Δ/natural variability=+2.54)
- (c) Sorting, 400 iterations: 92/200 items in clusters; author Gini=0.333, N_eff=29.0/40; on average each item was handled by 4.1 ants (at most 13); 1786 events in total

**Status**: exp5 is an early 8-seed version, superseded by exp7 (32 paired seeds, Holm correction, group Shapley).

---

## D3: Recovery without return

### exp8: Paired controls on the TSP — is the "hysteresis" real?

Setup: 30 cities, 30 ants; one edge is blocked at cycle 60 (T1), unblocked at cycle 140 (T2), and the run ends at cycle 220 (T_END); 50 paired seeds per cell. Reference optimum L* = 456.637 (consistent across repeated ACO + 2-opt runs). Control 1: cold start; each seed is run both "never blocked" and "blocked → unblocked", and at T_END the two are compared on current competence (mean gap of the per-cycle best over the last 20 cycles), the archived record's gap, and the similarity (Jaccard) of the medium path and the archived path to the path at T1. Control 2: warm start with L* pre-written into the medium; an edge of L* is blocked and later unblocked, and the fraction that refinds L* within 80 cycles after unblocking is compared with the fraction of same-seed cold-start colonies that first find it within 80 cycles.

**Control 1: cold start, perturbed − control (paired)**

| ρ | Measure | Control | Perturbed | Difference (perturbed − control) [95% CI] | Wilcoxon p |
|---|---|---|---|---|---|
| 0.3 | Current competence gap % | 6.034 | 6.081 | +0.048 [-0.565, +0.625] | 0.335 |
| 0.3 | Archived record gap % | 0.637 | 1.687 | +1.050 [+0.639, +1.473] | 2.49e-05 |
| 0.3 | Medium path vs T1 (J) | 0.767 | 0.725 | -0.042 [-0.072, -0.011] | 0.0119 |
| 0.3 | Archived path vs T1 (J) | 0.835 | 0.682 | -0.152 [-0.203, -0.100] | 8.82e-06 |
| 0.5 | Current competence gap % | 5.001 | 5.186 | +0.185 [-0.324, +0.698] | 0.559 |
| 0.5 | Archived record gap % | 0.493 | 1.117 | +0.623 [+0.331, +0.963] | 1.85e-05 |
| 0.5 | Medium path vs T1 (J) | 0.783 | 0.761 | -0.023 [-0.059, +0.015] | 0.115 |
| 0.5 | Archived path vs T1 (J) | 0.834 | 0.703 | -0.131 [-0.182, -0.079] | 9.73e-05 |
| 0.9 | Current competence gap % | 4.273 | 4.336 | +0.063 [-0.140, +0.261] | 0.388 |
| 0.9 | Archived record gap % | 0.339 | 0.712 | +0.373 [+0.267, +0.484] | 8.63e-07 |
| 0.9 | Medium path vs T1 (J) | 0.768 | 0.764 | -0.004 [-0.035, +0.026] | 0.977 |
| 0.9 | Archived path vs T1 (J) | 0.826 | 0.716 | -0.110 [-0.158, -0.064] | 5.68e-05 |

**Control 2: starting from the optimum — refinding within 80 cycles after unblocking vs first finding within 80 cycles from a cold start**

"Finding" is counted under three criteria: gap to L* ≤ 0% (exact), ≤ 0.5%, ≤ 1%. Proportions carry Clopper–Pearson 95% CIs; the parentheses in the McNemar column give the counts of the two kinds of discordant pairs.

| ρ | Criterion | First finding (cold) [95% CI] | Refinding (warm + perturbed) [95% CI] | McNemar p (paired) | Median cycles needed (first / re-) |
|---|---|---|---|---|---|
| 0.3 | ≤0.0% | 0.06 [0.01, 0.17] | 0.06 [0.01, 0.17] | 1 (2 vs 2) | 34 / 54 |
| 0.3 | ≤0.5% | 0.32 [0.20, 0.47] | 0.20 [0.10, 0.34] | 0.263 (13 vs 7) | 34 / 8 |
| 0.3 | ≤1.0% | 0.60 [0.45, 0.74] | 0.46 [0.32, 0.61] | 0.23 (16 vs 9) | 28 / 0 |
| 0.5 | ≤0.0% | 0.06 [0.01, 0.17] | 0.00 [0.00, 0.07] | 0.25 (3 vs 0) | 14 / — |
| 0.5 | ≤0.5% | 0.30 [0.18, 0.45] | 0.24 [0.13, 0.38] | 0.69 (14 vs 11) | 20 / 45 |
| 0.5 | ≤1.0% | 0.74 [0.60, 0.85] | 0.54 [0.39, 0.68] | 0.0872 (19 vs 9) | 19 / 11 |
| 0.9 | ≤0.0% | 0.12 [0.05, 0.24] | 0.20 [0.10, 0.34] | 0.424 (5 vs 9) | 54 / 52 |
| 0.9 | ≤0.5% | 0.44 [0.30, 0.59] | 0.46 [0.32, 0.61] | 1 (10 vs 11) | 52 / 11 |
| 0.9 | ≤1.0% | 0.84 [0.71, 0.93] | 0.92 [0.81, 0.98] | 0.388 (4 vs 8) | 33 / 6 |

Pooled over the 3 values of ρ (n = 150 pairs per criterion):

- ≤0.0%: first finding 0.08, refinding 0.09, McNemar p = 1 (10 vs 11)
- ≤0.5%: first finding 0.35, refinding 0.30, McNemar p = 0.389 (37 vs 29)
- ≤1.0%: first finding 0.73, refinding 0.64, McNemar p = 0.136 (39 vs 26)

**Status**: Refinding — an earlier sample of 60 pairs suggested a refinding deficit (p = 0.07), which did not hold in 150 pairs (p = 0.39, the pooled ≤0.5% criterion above).

### exp6: Reversibility, half-life and forgetting

Setup: 30 cities, 30 ants, 4 seeds. (a) An edge of the current best tour is blocked at cycle 60 and unblocked at cycle 140; recovery time, the half-life of pheromone on the blocked edge (forgetting) and whether the colony returns to the original path after unblocking are compared across retention coefficients ρ. (b) Recovery after cutting the medium (Section 4.2.3 of the original thesis, "dissolving collective intelligence") and after removing half the ants. (c) Recovery of the sorting system after a global scramble.

**(a) Block / unblock (mean of 4 seeds)**

| ρ | Recovery cycles | Pheromone half-life on blocked edge (measured / theoretical ln½/lnρ) | Jaccard with original path after unblocking | Fraction readopting the original edge |
|---|---|---|---|---|
| 0.3 | 3.2 | 1.0 / 0.58 | 0.633 | 0.25 |
| 0.5 | 8.0 | 1.5 / 1.00 | 0.755 | 0.50 |
| 0.7 | 2.0 | 2.0 / 1.94 | 0.671 | 0.00 |
| 0.9 | 6.8 | 7.0 / 6.58 | 0.721 | 0.25 |

**(b) Cut medium and ant removal**

- Recovery after cutting the medium: mean ant tour length during the perturbation / before = 1.153; 10 cycles after recovery = 1.013
- Recovery after removing half the ants: mean ant tour length during the perturbation / before = 0.995; 10 cycles after recovery = 0.989

**(c) Sorting**

- Scramble at iteration 300: 135.2 iterations needed to recover the pre-perturbation entropy (107.0 needed for initial formation); -1 means not recovered

**Status**: The "hysteresis" reading of (a) — no return to the original path after unblocking (4 seeds, no unblocked control) — is superseded by the paired controls of exp8. exp6 is kept for its half-life measurements (measured vs theoretical ln½/lnρ).

### exp12: Paired forks with learnable ants — recovery without return

Setup: double bridge, 30 ants, 20 seeds. For each seed the colony learns for 1000 steps, then the full state is paused and copied into three branches: B (reseed rs1, short corridor blocked from step 1000 to 2000, then unblocked), C1 (same reseed rs1, never blocked: paired control) and C2 (a different reseed rs2, never blocked: baseline for pure random divergence); all run to step 3000. After unblocking (step 2100 to the end) the experiment measures the difference in short-corridor share, the difference in deliveries (with C2 − C1 as the natural-variability reference) and, for learnable ants, the per-ant policy JS divergence over 96 probe contexts. Rule-based ants go through the same procedure as a control.

#### Learnable ants (GPT)

- Short-corridor share after unblocking: control 0.888, blocked branch 0.874
- Difference in short-corridor share (blocked − control) = -0.015 [-0.042, +0.016], d_z = -0.21, p = 0.277
- Reference: difference between the two unblocked branches (C2 − C1) = +0.007 [-0.027, +0.042], d_z = +0.09, p = 0.756
- Deliveries after unblocking: control 220.9; difference (blocked − control) = +9.1 [-11.7, +31.7], d_z = +0.18, p = 0.542
- Natural variability mean |C2 − C1| = 55.0; deliveries difference relative to control = +4.1% (95% CI -5.3% to +14.4%)
- Per-ant policy JS: blocked vs control = 0.0186, between the two controls = 0.0167 (nats)
- Paired difference JS(B,C1) − JS(C1,C2) = +0.0019 [+0.0005, +0.0033], d_z = +0.60, p = 0.00944; with C2 as control = +0.0023 [+0.0012, +0.0034], d_z = +0.93, p = 0.000708
- Mean fraction of ants per seed with JS(B,C1) > JS(C1,C2) = 0.52
- Direction consistent at the seed level: 16/20 seeds

#### Rule-based ants

- Short-corridor share after unblocking: control 0.829, blocked branch 0.805
- Difference in short-corridor share (blocked − control) = -0.024 [-0.054, +0.004], d_z = -0.34, p = 0.189
- Reference: difference between the two unblocked branches (C2 − C1) = -0.019 [-0.040, +0.002], d_z = -0.39, p = 0.0826
- Deliveries after unblocking: control 161.2; difference (blocked − control) = +6.6 [-7.9, +20.5], d_z = +0.20, p = 0.332
- Natural variability mean |C2 − C1| = 20.1; deliveries difference relative to control = +4.1% (95% CI -4.9% to +12.7%)

**Status**: exp12 supersedes exp9(d) and its unpaired observation (short-corridor share 0.80→0.89): the unblocked paired control also reaches 0.888, so that rise came from continued learning.
