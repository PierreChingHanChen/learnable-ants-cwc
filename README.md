English | [中文](README.zh-TW.md)

# Learnable ants: Coordination without convergence

Code, data, and figures for the study **"Coordination without convergence: Three decouplings in learnable ant collectives"** (Ching-Han Chen, National Central University, Taiwan).

Systems of AI agents increasingly coordinate through what they leave in shared memories rather than through messages to one another. This repository tests three assumptions behind the governance of such systems in colonies of *learnable ants*: agents whose decision core is a 4096-parameter transformer that reads perceptions and writes actions as one interleaved token sequence, keeps learning from its own successful trips, and interacts with other ants only through a pheromone medium.

| Decoupling | Assumption tested | Finding |
|---|---|---|
| D1 Coordination without convergence | Coordination requires agents to converge | A shared medium raised colony yield 1.57-fold without reducing between-ant policy dispersion; social learning made ants nearly identical without raising yield. Most divergence stayed inside the control grammar the ants were taught. |
| D2 Traces overstate how concentrated responsibility is | Records of who wrote what locate responsibility | The quarter of ants leaving the most trail carried 40% of the trace but 31% of the Shapley value; no single ant was necessary; the colony produced 30% more than its parts alone. Replicated on fresh seeds with prespecified tests. |
| D3 Recovery without return | Recovery restores the prior state | Collective performance recovered after a perturbation, whereas archived solutions and individual policies did not. |

The manuscript is under review. Citation details and the archived release (DOI) will be added here on publication.

## Contents

```
miat_ants/            simulation platform (Python + numpy)
  core/               GRAFCET engine, event contract, shared medium with provenance, metrics
  tsp/                Ant System for the traveling-salesman problem (+ SA/GA baselines)
  sorting/            ant-based item sorting
  microgpt/           numpy transformer (~4k parameters, batched over agents, hand-written gradients, Adam)
  foraging/           learnable-ant foraging: vocabulary, worlds, rule/GPT cores, system, pretraining
    weights/          behavior-cloned base models (base_bc, base_bc_mark05)
experiments/          one script per experiment (exp1–exp13), analysis and figure scripts
results/              per-seed results (CSV / NPY / NPZ) used in the paper
figures/              exploratory figures written by the experiment scripts
figures/paper/       paper figures: Fig1–Fig5 and FigS1–FigS6 (PDF + PNG)
tests/                51 automated tests (model, controller, action, integration)
docs/en/, docs/zh-TW/ documentation in English and Traditional Chinese
run_all.py            runs every experiment and figure script in order
```

## Installation

Python 3.10 or newer (tested with Python 3.13).

```bash
pip install -r requirements.txt
python -m pytest -q          # 51 tests, about 15 s
```

## Quick start

Regenerate all paper figures from the stored results (about one minute):

```bash
python experiments/make_figures.py        # Fig. 1–5  -> figures/paper/
python experiments/make_supp_figures.py   # figs. S1–S6 -> figures/paper/
```

Run a single experiment with the paper's settings, for example the paired return forks (this replaces the stored `results/exp12*` files with your own run):

```bash
python run_all.py exp12
```

Smoke-test the whole pipeline with tiny samples. This **overwrites `results/` and `figures/`** with low-sample values, so run it in a separate copy or restore the files afterward with `git checkout -- results figures`:

```bash
QUICK=1 python run_all.py
```

The full run (`python run_all.py`) takes several hours on two CPU cores. See [docs/en/EXPERIMENTS.md](docs/en/EXPERIMENTS.md) for every step, its settings, its outputs, and which figure or table of the paper it produces.

## Documentation

| Document | Content |
|---|---|
| [EXPERIMENTS.md](docs/en/EXPERIMENTS.md) | How to reproduce each result; map from paper figures and tables to scripts and data |
| [RESULTS.md](docs/en/RESULTS.md) | Curated results of every experiment |
| [DATA_DICTIONARY.md](docs/en/DATA_DICTIONARY.md) | Columns and meaning of every file in `results/` |
| [DESIGN.md](docs/en/DESIGN.md) | MIAT 2.0 design of the platform: requirements, IDEF0, event contract, traceability |
| [DESIGN_microgpt_ants.md](docs/en/DESIGN_microgpt_ants.md) | Design of the learnable-ant (microGPT) subsystem |
| [GRAFCET_MODELS.md](docs/en/GRAFCET_MODELS.md) | State tables and diagrams of all GRAFCET controllers |

Each document has a Traditional Chinese version in [docs/zh-TW/](docs/zh-TW/). Code comments, docstrings, and the text summaries that the scripts write to `results/summary_*.md` are in Traditional Chinese.

## Using the platform

### Forking a colony for paired counterfactuals

`ForagingSystem` can pause at an epoch boundary and copy its complete state (positions, cargo, pheromone fields, every ant's weights and optimizer state, controller state, random-number generator), so that alternative futures share one history (this example takes about a minute):

```python
from miat_ants.core.events import Event
from miat_ants.foraging import ForagingSystem, ForagingConfig

s = ForagingSystem(ForagingConfig(core="gpt", track_provenance=True, max_steps=3000, seed=0)).run_until(2000)
full = s.fork(events_now=[Event("reseed", 2000, "experiment", {"seed": 1})]).resume()
cut = s.fork(events_now=[Event("reseed", 2000, "experiment", {"seed": 1}),
                         Event("remove_ants", 2000, "experiment", {"ids": [3, 7]})]).resume()
```

- `run_until(step)` pauses at an epoch boundary; `fork()` copies all data-path state and the GRAFCET marking.
- `remove_ants` removes the listed ants; `reseed` resets the shared random stream so that branches face the same randomness after the fork.
- With `track_provenance=True`, the history records `contrib_trail` (each ant's pheromone on perceivable trail cells), `contrib_total`, and `delivered_by`.

### Ant System with perturbations and an event log

```python
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.core.events import Event, PRIORITY_ENV

coords = random_cities(30, seed=30)
ev = [Event("cut_medium", 50, "environment", {}, PRIORITY_ENV),
      Event("restore_medium", 100, "environment", {}, PRIORITY_ENV)]
r = AntTSPSystem(coords, AntTSPConfig(n_ants=30, max_cycles=150, seed=0, medium_mode="shared",
                                      perturbations=ev, log_deposits=True)).run()
print(r.best_length, r.history["consensus"][-1])
r.events.to_csv("my_events.csv")
```

### Plugging in your own agent

Pass any function as `AntTSPConfig(policy=...)`:

```
f(agent_id, cur, allowed_mask, tau_row, eta_row, rng) -> next_city
```

The agent sees only `tau_row` as perceived through the medium, and the system raises an exception if the tabu contract is violated. `experiments/example_custom_policy.py` contains a template (`llm_stub`) for an observation → prompt → parsed reply loop of a language-model agent; it does not call any API.

### Changing behavior

Edit the model definitions (`add_step` / `add_transition`) in the relevant `system.py`, then regenerate the model document with `python docs/gen_model_docs.py` (this rewrites the Chinese file; update the English translation in `docs/en/GRAFCET_MODELS.md` by hand). Do not bypass the model by changing control flow inside actions. New metrics go into `miat_ants/core/metrics.py` as pure functions; new perturbations need a branch in `_apply_perturbation`, an entry in the event-contract table of [DESIGN.md](docs/en/DESIGN.md), and a test.

## Relation to the original thesis

The platform reimplements, in Python, the Java applets of C.-H. Chen's 2000 thesis *Ant-behavior-impersonating group problem-solving system* and extends them with learnable ants. Experiments exp1–exp3 reproduce the thesis results. Differences: the equations were reconstructed because the original equation objects could not be extracted; the 42-city instance is a fixed-seed random instance because the original coordinates are unavailable; simulated annealing and the genetic algorithm were reimplemented; and the number of steps per sorting "iteration" was calibrated because the thesis does not state it. Details are in the last section of [DESIGN.md](docs/en/DESIGN.md).

## License

- Code (`miat_ants/`, `experiments/`, `tests/`, `docs/gen_model_docs.py`, `run_all.py`): [MIT License](LICENSE).
- Data, figures, model weights, and documentation (`results/`, `figures/`, `miat_ants/foraging/weights/`, `docs/`, README files): [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-DATA).

## Citation

If you use this code or data, please cite the repository (see [CITATION.cff](CITATION.cff)); the article reference will be added on publication.

## Contact

Questions and bug reports: please open an issue.
