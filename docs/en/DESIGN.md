English | [中文](../zh-TW/DESIGN.md)

# Ant-Behavior-Impersonating Group Problem-Solving System: MIAT 2.0 Design Document

> For the full design of the third subsystem, the "microGPT ant language model" (`miat_ants/foraging`), see [`DESIGN_microgpt_ants.md`](DESIGN_microgpt_ants.md).

Original thesis: C.-H. Chen (2000), "Ant-behavior-impersonating group problem-solving system" (Java applet implementation)
Goal of the rewrite: rebuild the two systems with the MIAT 2.0 methodology (requirements → IDEF0 → GRAFCET → high-level synthesis → layered verification) as an experimental platform for three subsequent research topics:

1. Stigmergy and We-sense
2. Distributed responsibility
3. Entangled reversibility

In the paper, Topic 1 corresponds to the first decoupling (D1, coordination without convergence), Topic 2 to D2 (traces and responsibility), and Topic 3 to D3 (recovery without return).

---

## Phase 0｜Requirement Formalization

| ID | Requirement | Measurement | Acceptance criterion | Test / evidence |
|---|---|---|---|---|
| R-01 | The ant–TSP system solves the symmetric TSP with Ant System (ant-cycle, Eqs. 1–5) | Known optimum of the 5×5 grid, 24+√2 | Error ≤ 3% within 40 cycles | `test_grid_optimum_found_and_token_walk` |
| R-02 | Every ant's tour must be legal: each city exactly once, returning to the start at the end | `is_valid_tour` | 100% legal | A23 assert, `test_baselines_valid` |
| R-03 | The pheromone update follows Eq. (3): τ ← ρτ + Δτ | Numerical comparison | Error < 1e-9 | `test_medium_eq3_and_provenance_invariant` |
| R-04 | Reproduce thesis Table 1: ACO, SA, and GA compared on the 42-city problem, 10 runs each | Best / mean / standard deviation | Table and CSV output | `exp2_tsp_compare` |
| R-05 | Reproduce thesis Fig. 3: parameter experiments on the number of ants, ρ, α, β, Q | % gap from the reference optimum | Figure and CSV output | `exp1_tsp_params` |
| R-06 | The automatic sorting system performs pick-up and drop according to Eqs. (6)(7)(8) | Monotonicity, boundary values | p_pick decreases with f, p_drop increases with f | `test_density_bounds_and_probabilities` |
| R-07 | Object conservation: the total number of objects on the grid and being carried is always N, with no duplicate ids | Checked after every run | 200/200 | `test_object_conservation_and_clustering` |
| R-08 | Spatial entropy (Eqs. 9–10) measures the degree of clustering | 0 for complete separation, > 0.9 for a random distribution | Pass | `test_entropy_extremes` |
| R-09 | Reproduce thesis Figs. 7 and 8 and Table 2 | E_S curves and tables | Figure and CSV output | `exp3_sorting` |
| R-10 | The same random seed must give exactly the same result | Compare two runs | Identical | `test_seed_reproducibility` |
| R-11 | The medium can be switched between shared and private, and supports read delay, noise, and cutting (Topic 1) | Interface tests and experiments | delay reads an old state; after cut, a uniform matrix is read | `test_medium_delay_and_cut`, `exp4` |
| R-12 | Every bit of pheromone can be traced to the agent that left it, and is conserved: τ = base + Σ contrib (Topic 2) | Invariant check | Error < 1e-6 | `check_invariant`, `exp5` |
| R-13 | All pick-up and drop events are written to the event contract; event counts must agree with the state: picks − drops = number carried (Topic 2) | Compare events with state | Identical | `test_object_conservation_and_clustering` |
| R-14 | External perturbations are handled as high-priority events at cycle boundaries, including blocking/unblocking edges, removing/restoring ants, cutting/restoring the medium, and scrambling the grid (Topic 3) | Token walkthrough of the exception path | After blocking, the best tour does not contain the blocked edge | `test_exception_path_block_edge`, `exp6` |
| R-15 | Every GRAFCET must pass the Gate 2 review: reachable, has an exit condition, no condition may be True | `Grafcet.validate()` | Checked automatically at construction; an exception is raised on failure | `test_validate_*`, [`GRAFCET_MODELS.md`](GRAFCET_MODELS.md) |
| R-16 | Responsibility is quantified with paired statistics: bootstrap intervals, Wilcoxon tests with effect sizes, Holm correction, and group Shapley values (Topic 2) | Unit tests of the statistics helpers | Pass | `test_holm`, `test_paired_stats_and_ci`, `exp7`, `exp10` |
| R-17 | A colony can be warm-started from a known tour: the medium is imprinted with the tour's steady-state pheromone and the archive holds it (Topic 3) | Interface test | Imprinted tour is recovered by the medium and the archive | `test_warm_start_imprint_and_reference_helpers`, `exp8` |

**Non-functional requirements**

- A single 25-city, 100-cycle run takes less than 3 seconds on an ordinary laptop.
- Pure Python implementation, depending only on numpy and matplotlib.
- All randomness comes only from each system's own `np.random.Generator`; no global state is used.

---

## Phase 1｜System Architecture

### Physical architecture (deployment view)

| Component | Location | Description |
|---|---|---|
| Core framework | `miat_ants/core/` | GRAFCET engine, event contract, shared medium, metrics |
| Ant–TSP | `miat_ants/tsp/` | `problem.py` (A1 problem instance), `actions.py` (Datapath), `system.py` (Controller + assembly), `baselines.py` (SA/GA) |
| Ant–sorting | `miat_ants/sorting/` | `actions.py` (Datapath), `system.py` (Controller + assembly) |
| Experiments | `experiments/` | Reproduction of the original thesis (exp1–3), three research topics (exp4–8), learnable ants (exp9–13, incl. exp10b; see [`DESIGN_microgpt_ants.md`](DESIGN_microgpt_ants.md)) |
| Verification | `tests/` | Four layers of tests: model, Controller, Action, integration |

### Functional architecture (IDEF0): ant–TSP

| Module | Function (verb phrase) | Input | Control | Output | Mechanism |
|---|---|---|---|---|---|
| A0 | Search collectively, as an ant colony, for the shortest TSP tour | City coordinates | AntTSPConfig, perturbation events | Best tour, history, event log | Python/numpy |
| A1 | Initialize the problem | Coordinates | τ0, ρ, medium mode | D, η, medium | `a1_initialize`, `distance_matrix`, `visibility` |
| A21 | Place ants | m, n | Mask of live ants | Start cities, tabu list | `place_ants` |
| A22 | Choose the next city probabilistically | Medium reading τ, η, tabu | α_k, β_k (Eq. 1) | Next city | `choose_next`, `GraphMedium.sense` |
| A23 | Close the tours | Path after n−1 steps | Legality rules | Complete tours | `a23_close_tours` |
| A3 | Evaluate the tours | Tours, D | Current costs (possibly perturbed) | L_k, best of this cycle, global best | `tour_length` |
| A4 | Update the pheromone | Tours, L_k | Q, ρ (Eqs. 3–5) | New τ, provenance | `GraphMedium.deposit/commit` |
| A5 | Record, handle events, decide on termination | Measurements | max_cycles, event queue | history, finished | `EventQueue`, `metrics` |

### Functional architecture (IDEF0): ant–sorting

| Module | Function | Input | Control | Output | Mechanism |
|---|---|---|---|---|---|
| A0 | Sort heterogeneous objects into homogeneous clusters | Objects, grid | AntSortConfig, perturbation events | Grid, entropy curve, event log | Python/numpy |
| A11 | Place objects | H, W, number of classes, count | At most one object per cell | type_grid, id_grid | `place_objects` |
| A12 | Place ants | H, W, m | — | Positions | `place_ants` |
| A21 | Move randomly | Position, speed | 8 directions, toroidal boundary, move only while in G0.X1 | New position | `random_moves` |
| A22 | Evaluate whether to pick up | Object underfoot, neighborhood | k1 (Eqs. 6, 8), arbitration rule | Pick-success mask, pick events | `local_density`, `p_pick`, `arbitrate` |
| A23 | Evaluate whether to drop | Carried object, neighborhood | k2 (Eqs. 7, 8), arbitration rule | Drop-success mask, drop events | `p_deposit`, `arbitrate` |
| A3 | Measure the degree of clustering | type_grid | Block size s (Eqs. 9–10) | E_S | `spatial_entropy` |
| A4 | Record, handle events, decide on termination | history | max_iterations, event queue | finished | `EventQueue` |

### Interface contract of the shared medium (Topic 1)

| Method | Contract |
|---|---|
| `deposit(agent, edges, amount)` | Writes only to the delta buffer; does not take effect immediately |
| `commit()` | Applies Eq. (3) synchronously; there is no write-order dependency between agents, so no race condition exists |
| `sense(agent)` | Returns an (n, n) matrix: possibly delayed by d cycles, with added noise, or a uniform matrix when cut |
| `snapshot()` | The true state from the researcher's point of view; agents may not call it |
| `provenance_share(edges)` | Returns the shares of [initial environment amount, agent0, …], summing to 1 |

**Extension:** when the ants are replaced by LLM agents, the contracts of A2 and A4 stay unchanged as long as the agents follow the deposit/sense interface.

### Gate 1 review record

- **Shared state**
  - The TSP medium uses a two-stage deposit → commit; there are no hidden shared writes.
  - In sorting, the grid is the only shared object; conflicts on the same cell are arbitrated explicitly by `arbitrate`, with the rule that the smaller ant index wins, and the number of conflicts is also recorded.
- **Performance hot spots**
  - A22 performs one O(n) probability computation for each of the m ants per clock, so a single run costs about m·n²·cycles.
  - Neighborhood counting in sorting is vectorized with numpy roll, about O(H·W) per clock.

---

## Phase 2｜Behavior Modeling (GRAFCET)

For the full state tables and Mermaid diagrams, see **[`GRAFCET_MODELS.md`](GRAFCET_MODELS.md)**. That file is generated automatically from the models in the code and is the single source of truth.

| Controller | Activation condition | Completion condition | Description |
|---|---|---|---|
| TSP G0 | Power-on (X0) | X5 | A1→A2→A3→A4→A5 loop |
| TSP G2 | G0.X1 | X24 | Tour construction; X22 exits on the `tours_complete` completion event, not on True |
| Sort G0 | Power-on (X0) | X4 | One iteration consists of `steps_per_iteration` clocks |
| Sort G2 | G0.X1 ∧ underfoot condition | — | Population GRAFCET, n = number of ants; each ant holds its own set of state variables |

### Checks for the four concurrency failure modes

| Failure mode | How this system handles it |
|---|---|
| Stale data | The TSP medium is updated only at commit. `sense_delay`, by contrast, introduces stale data **deliberately**, as an experimental variable for Topic 1. |
| Deadlock | The only wait chain is G0.X1 ⇄ G2.X24, which cannot form a cycle. `SuperLoop.run` has a max_ticks guard. |
| Race condition | In sorting, competition for picking up or dropping on the same cell is handled by `arbitrate`. If OR divergence branches are enabled simultaneously, `Grafcet.conflicts` counts them. |
| Starvation | Removed ants (alive=False) do not execute Actions and do not take part in transition conditions. |

### Event contract (Event)

Fields: `event_type, timestamp, source_module, payload, priority, policy`

| event_type | Source | Priority | Purpose |
|---|---|---|---|
| `deposit` | `ant:k` | LOG | Topic 2: every pheromone deposit |
| `pick` / `drop` | `ant:k` | LOG | Topic 2: every sorting action; payload contains f, p, cell |
| `block_edge` / `unblock_edge` / `move_city` | environment | ENV | Topic 3: environmental change |
| `remove_ants` / `restore_ants` | environment | ENV | Topic 3: individual failure |
| `cut_medium` / `restore_medium` / `cut_sensing` / `restore_sensing` | environment | ENV | Original thesis 4.2.3: dissolving and reassembling collective intelligence |
| `scramble_region` / `scramble_all` | environment | ENV | Topic 3: large perturbation in sorting |
| `perturbation_applied` / `report` | system | Same as the original event | Traceability evidence |

---

## Phase 3｜High-Level Synthesis

`miat_ants/core/grafcet.py` implements the Controller with the GRAFCET synthesis rules of the MIAT methodology, and keeps the Controller separate from the Actions.

| GRAFCET element | Implementation |
|---|---|
| State Xi | `Grafcet.X[sid]`: a Boolean array of length n |
| Transition Ri | `add_transition(..., cond)`: a condition function. True is rejected at construction. |
| Fundamental / AND / OR | `controller()` uses synchronous-snapshot semantics; declaration order is the priority order of OR branches |
| Action | `add_step(..., action, mode)`. mode is `N` (continuous) or `P1` (once on entry). On completion, `mark_done()` produces the event. |
| Sub-GRAFCET | A separate Grafcet object; within one clock, `SuperLoop` runs "all controllers first, then all actions". Coordination is by state, not call-return. |
| Reset | `Grafcet.reset()` |

All Actions are pure functions in `actions.py`. Each function documents its Input / Output and can be tested in isolation with fixed inputs (white-box acceptance 3b, 3c).

---

## Phase 4｜Layered Verification

| Layer | Files |
|---|---|
| Model check | `Grafcet.validate()` (run automatically at construction), [`GRAFCET_MODELS.md`](GRAFCET_MODELS.md) |
| Controller simulation | `tests/test_grafcet.py`: fundamental block, AND, OR, P1/N, population, sub-controller coordination |
| Action unit tests | Formula and function tests in `tests/test_tsp.py` and `tests/test_sorting.py` |
| Integration tests | Full system runs, Token walkthroughs (normal and exception paths), conservation and consistency |
| System acceptance | exp1–exp13 (incl. exp10b) in `experiments/`, run in order by `run_all.py`, output to `results/summary_*.md` |

### Traceability

| Requirement | IDEF0 | GRAFCET state | Function | Test |
|---|---|---|---|---|
| R-01 | A0–A5 | G0.X0–X5, G2.X20–X24 | `AntTSPSystem.run` | test_grid_optimum… |
| R-02 | A21–A23 | G2.X21–X23 | `place_ants`, `choose_next`, `is_valid_tour` | test_tour_length_closed |
| R-03 | A4 | G0.X3 | `GraphMedium.commit` | test_medium_eq3… |
| R-06 | A22, A23 | Sort G2.X21, X23 | `p_pick`, `p_deposit`, `local_density` | test_density… |
| R-07, R-13 | A22, A23 | Sort G2.X21–X23 | `a22_eval_pick`, `a23_eval_drop` | test_object_conservation… |
| R-08 | A3 | Sort G0.X2 | `spatial_entropy` | test_entropy_extremes |
| R-11 | A22 (Mechanism) | TSP G2.X22 | `GraphMedium.sense` | test_medium_delay_and_cut |
| R-12 | A4 | TSP G0.X3 | `provenance_share`, `check_invariant` | test_medium_eq3… |
| R-14 | A5, A4 | TSP G0.X4, Sort G0.X3 | `_apply_perturbation` | test_exception_path_block_edge |
| R-16 | A4, A5 | TSP G0.X3–X4 | `provenance_share`; statistics tools in `experiments/common.py` | test_stats |
| R-17 | A1, A5 | TSP G0.X0, X4 | `GraphMedium.imprint`, `init_best`, `greedy_medium_tour`, `two_opt` | test_warm_start_imprint… |
| R-15 | All | All | `Grafcet.validate` | test_validate… |

---

## Differences from the Original Thesis and Notes on the Reconstruction

1. **Reconstructed equations.** The equation objects in the original .doc could not be extracted. Eqs. (1)–(5) are reconstructed from the Ant System (ant-cycle) of Dorigo, Maniezzo & Colorni (1996); Eqs. (6)–(8) from Deneubourg et al. (1991) and Lumer & Faieta (1994); Eqs. (9)–(10) from the textual description (block entropy, normalized by log(number of classes), then averaged). Because they are reconstructions, they may differ in detail from the equations of the original thesis.
2. **The 42-city instance.** The original coordinates are no longer available; 42 random cities with a fixed seed are used instead. `load_tsplib()` can swap in a standard instance such as dantzig42.
3. **SA / GA are reimplementations.** Parameters take common values, with a comparable evaluation budget.
4. **Definition of an "iteration".** The original thesis does not state how many steps one iteration of the sorting system contains. This version defines it by `steps_per_iteration` (default 20 clocks), calibrated to the order of magnitude of the values in Table 2.
5. **New research knobs** (off by default, so the default behavior is identical to the original algorithm):
   - Medium mode, delay, noise, cutting
   - Provenance tracking
   - Individual heterogeneity
   - Event logging
   - Perturbation events
