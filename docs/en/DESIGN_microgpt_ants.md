English | [中文](../zh-TW/DESIGN_microgpt_ants.md)

# microGPT Ant Language Model: MIAT 2.0 Design Document

This document defines the platform's third subsystem, `miat_ants/foraging`: an ant's perceptions and actions are encoded as token sequences, a tiny autoregressive Transformer (microGPT scale, about 4 thousand parameters) serves as the ant's decision core, and rule-based ants are kept as the control group.

**Design decisions**

| Item | Decision |
|---|---|
| Experimental environment | Foraging, with an open field and a double bridge |
| Model weights | Shared base model + individual online fine-tuning per agent |
| Learning method | Behavior cloning (BC) first, then online filtered self-imitation |
| Social learning | Off by default, available as a switch |
| Sequence format | Perception tokens and action tokens interleaved |

---

## Phase 0｜Requirement Formalization

| ID | Requirement | Measurement | Acceptance criterion | Evidence |
|---|---|---|---|---|
| F-01 | Sequences use the interleaved format `. o₁ a₁ o₂ a₂ …`. Perception tokens may be written only by the world; action tokens may be produced only by the core. | Check each token's class by position | An exception is raised on violation | test_vocab_and_sequence_contract |
| F-02 | The model computes the loss and samples only at action positions. During sampling, the probabilities of non-action tokens are masked to 0. | Loss mask, sampling results | 100% action tokens | test_masked_loss, test_rule_core_contract_and_gpt_decide_only_actions |
| F-03 | microGPT backpropagation is correct | Gradient check against finite differences | Relative error < 1e-5 | test_gradcheck |
| F-04 | The model can learn: it can overfit a fixed sequence | Loss after training | Drops to < 0.05 | test_overfit |
| F-05 | Parameter count on the same scale as microgpt | Count | 3–6 thousand | test_param_count |
| F-06 | Batched multi-agent inference: each agent has its own weights, and one forward pass makes all decisions | Compare with one-by-one inference | Numerically identical | test_batched_equals_single |
| F-07 | World conservation: total food = remaining + being carried + delivered | Checked after every run | Identity holds | test_food_conservation |
| F-08 | Perception encoding is correct: food, wall, pheromone, nest direction, in the nest | Hand-built scenarios | All match the expected tokens | test_perception_cases |
| F-09 | Rule-based ants (teacher) can complete foraging, and prefer the short path on the double bridge | Delivery rate, short-corridor share | Deliveries > 0; short-corridor share > 0.5 | exp9(a)(b) |
| F-10 | GPT ants after BC are functionally on par | Ratio of delivery rates | ≥ 80% of rule-based ants | exp9(a) |
| F-11 | Online learning updates only that agent's own weights | Weight difference | Other agents unchanged | test_individual_learning_isolated |
| F-12 | The medium supports shared / private / cut, continuing the control design of Topic 1 | Interface tests | Pass | test_field_medium |
| F-13 | Key events are written to the event contract: take, deliver, episode end, learning, perturbation | Compare events with state | Number of deliver events = delivery count | test_food_conservation_events_and_token_walk |
| F-14 | All GRAFCETs pass the Gate 2 review; the Token walkthrough covers the normal and exception paths (episode timeout) | `validate()`, trace | Pass | test_food_conservation_events_and_token_walk |
| F-15 | Results with the same seed are exactly identical | Compare two runs | Identical | test_individual_learning_isolated_and_reproducible |

**Non-functional requirements**

- Depends only on numpy; no GPU required.
- On an ordinary CPU, a single run of 30 ants × 3000 steps takes less than 60 seconds.
- Pretrained weights ship with the project: `miat_ants/foraging/weights/base_bc.npz`.

---

## Phase 1｜System Architecture

### Vocabulary (24 tokens)

| Class | Token | Meaning | Writer |
|---|---|---|---|
| Boundary | `.` | Episode start (BOS) | System |
| Action · move | `F` `L` `R` | Forward; turn left 45° then forward; turn right 45° then forward | Core |
| Action · move and mark | `f` `l` `r` | Same as above, and deposit pheromone at the new position | Core |
| Action · operate | `T` `D` | Take food (then turn 180°); drop food in the nest (then turn 180°) | Core |
| Perception · searching | `X` `A` `B` `C` | Food underfoot; food ahead, ahead-left, ahead-right | World |
| Perception · searching | `P` `Q` `S` `N` `W` | Strongest pheromone ahead, ahead-left, ahead-right; nothing at all; wall ahead | World |
| Perception · carrying | `0` `1` `2` `3` `4` `w` | In the nest; nest ahead, right, behind, left; wall ahead | World |

**Perception priority**

- Searching: X > W > food direction (A/B/C) > pheromone direction (P/Q/S, must exceed the threshold) > N
- Carrying: 0 > w > nest direction

Perception selects the most salient cue for the current task; this operationalizes Merleau-Ponty's "intentional arc" and Gibson's "affordances".

### Physical architecture

| Component | Location |
|---|---|
| Tiny Transformer | `miat_ants/microgpt/model.py` (pure numpy) |
| Field medium | `miat_ants/core/field_medium.py` |
| Foraging subsystem | `miat_ants/foraging/`: `vocab.py`, `world.py`, `cores.py`, `system.py`, `pretrain.py`, `analysis.py` |
| Pretrained weights | `miat_ants/foraging/weights/` |
| Experiments | `experiments/exp9_microgpt_ants.py`; see also `exp10_topic2_learnable.py` (incl. exp10b), `exp11_d1_controls.py`, `exp12_learnable_return.py`, `exp13_grammar_adherence.py` |

### IDEF0 functional architecture

| Module | Function | Input | Control | Output | Mechanism |
|---|---|---|---|---|---|
| A0 | Forage as a population of tokenized ants and form trails | Map, base weights | ForagingConfig, perturbation events | Delivery records, history, events, per-agent weights | numpy |
| A1 | Initialize the world, medium, and core | Map specification, weight file | Seed, core type, weight mode | World, FieldMedium, AgentCore | `World`, `make_core` |
| A21 | Perception encoding: world state → perception token | Position, heading, carrying state, medium reading | Perception priority, pheromone threshold | One perception token per ant, appended to its context | `World.perceive` |
| A22 | Decision: context → action token | Each ant's most recent 16 tokens | Temperature, action mask | One action token per ant | `AgentCore.decide` |
| A23 | Action execution: action token → change in the world | Action tokens | Rules for walls, food, and nest | New state, event flags (take / deliver / blocked), medium deposits | `World.apply`, `FieldMedium.deposit` |
| A3 | Medium update | delta buffer | ρ (retention coefficient) | τ ← ρτ + Δτ | `FieldMedium.commit` |
| A4 | Online learning | Each agent's buffer of successful episodes | Learning rate, batch size, number of updates, social learning on/off | Updated weights, loss | `AgentCore.learn` |
| A5 | Measurement and event handling | History, world state | Perturbation event queue, number of epochs | Metrics, finished | `metrics`, `EventQueue` |
| A6 | Behavior-cloning pretraining (offline) | Trajectories of rule-based ants | Steps, batch, learning rate | `base_bc.npz` | `pretrain.py` |

### Interface contracts

**AgentCore** (must be implemented by both the rule core and the GPT core)

| Method | Contract |
|---|---|
| `decide(ids, contexts) -> tokens` | contexts are token id sequences of length ≤16, whose last token must be a perception token. Return values must belong to the action token set. Must not read the world or the medium. |
| `learn(ids, episodes) -> dict` | May update only the parameters of the agents in ids. The rule core does not learn and returns an empty dict. |
| `n_params() / policy_probe(contexts)` | Observation interface for researchers: obtain action distributions under fixed probe contexts. |

**World**

| Method | Contract |
|---|---|
| `perceive(ids) -> obs_tokens` | Returns only perception tokens; does not change state |
| `apply(ids, act_tokens) -> ActResult` | Invalid actions are treated as no-ops and raise no exception; returns moved / took / delivered / blocked / marked flags |
| `food_total()` | Used for the conservation check |

**FieldMedium** (continues the GraphMedium contract)

| Method | Contract |
|---|---|
| `deposit(ids, cells, amount)` | Writes only to the delta buffer |
| `commit()` | Applies τ ← ρτ + Δτ |
| `sense(ids, cells)` | Returns readings; returns 0 when cut; noise can be added; in private mode, an agent can read only its own medium |

**Event contract**

| Event | Source | Priority |
|---|---|---|
| `take`, `deliver` | `ant:k` | LOG |
| `episode_end` (payload: success, length, mark_rate) | `ant:k` | LOG |
| `learn` (payload: number of agents, mean loss) | A4 | MISSION |
| `cut_medium`, `restore_medium`, `block_gate`, `unblock_gate`, `remove_ants`, `restore_ants` | environment | ENV |

### Gate 1 review

- **Shared state**
  - The medium uses a two-stage deposit→commit.
  - Positions and food in the world are processed in A23 in ant-index order: when only 1 unit of food remains on a cell, the ant with the smaller index takes it first. This is an explicit arbitration rule.
- **Performance hot spots**
  - A22 performs one batched forward pass per step, with complexity O(A·T²·C).
  - A4 performs n Adam updates for each of the A agents in every epoch.

---

## Phase 2｜Behavior Modeling (GRAFCET)

### G0: sensorimotor clock (main controller)

| Step | Action | Transition condition | Next state |
|---|---|---|---|
| X0 (init) | A1 initialize (P1) | init_done | X1 |
| X1 | A21 perceive (P1) | obs_ready | X2 |
| X2 | A22 decide (P1) | actions_ready | X3 |
| X3 | A23 act (P1) | act_done | X4 |
| X4 | A3 medium update, step count + 1 (P1) | step_done ∧ ¬epoch_end | X1 |
| X4 | Same as above | step_done ∧ epoch_end | X5 |
| X5 | A4 online learning (P1) | learn_done | X6 |
| X6 | A5 measurement and events (P1) | record_done ∧ ¬finished | X1 |
| X6 | Same as above | record_done ∧ finished | X7 |
| X7 | Output report (terminal) | — | — |

### G2: task state (population controller, n = number of ants)

| Step | Meaning | Transition condition | Next state |
|---|---|---|---|
| X20 (init) | Search | took | X21 |
| X20 | Search | ep_len ≥ max_ep | X23 |
| X21 | Carry back to the nest | delivered | X22 |
| X21 | Carry back to the nest | ep_len ≥ max_ep | X23 |
| X22 | Successful episode: write to the success buffer, reset the context (P1) | recorded | X20 |
| X23 | Timeout (exception path): discard the episode, reset the context (P1) | reset_done | X20 |

G0 is the perception–action clock shared by the whole population; G2 is each ant's task intention (search / return to the nest). The two are coordinated through the completion events produced by A23 (took, delivered): G2 reads these flags on the clock after A23, and A21 clears them at the start of the next round of perception.

### Concurrency failure modes

| Mode | Handling |
|---|---|
| Stale data | A21 runs after A23 and A3, so it always reads the latest world and medium |
| Race | Taking food on the same cell follows index priority; the medium uses a delta buffer |
| Deadlock | G0 is a linear loop; every state of G2 has a timeout exit |
| Starvation | Removed ants do not take part in A21–A23 |

---

## Phase 3｜Synthesis

- **Controller**: reuses `core/grafcet.py`. G0 has n = 1; G2 has n = A and is the vectorized population version.
- **Action / Datapath**: all are pure functions or object methods, mapped to the IDEF0 numbers in the tables above.
- **AgentCore implementations**: `RuleCore` (rule-based ants) and `GPTCore` (microGPT). In experiments the two are swapped within the same world, which keeps the comparison fair.

## Phase 4｜Verification

| Layer | Tests |
|---|---|
| Model check | Gate 2 review; automatic GRAFCET documentation |
| Datapath units | Gradient check, overfitting, masking, batch consistency, perception scenarios, action effects, medium |
| Integration | Food conservation, event consistency, Token walkthrough (incl. the timeout exception path), reproducibility |
| System acceptance | exp9: (a) functional parity; (b) double bridge; (c) dialects and conventions; (d) cut medium |

## Traceability

| Requirement | IDEF0 | GRAFCET | Function | Test |
|---|---|---|---|---|
| F-01, F-02 | A21, A22 | G0.X1–X2 | `vocab`, `GPTCore.decide`, `MicroGPT.loss` | test_vocab_and_sequence_contract, test_masked_loss |
| F-03 to F-06 | A22, A4 | G0.X2, X5 | `MicroGPT.forward/backward/step` | test_gradcheck, test_overfit, test_batched… |
| F-07, F-08 | A21, A23 | G0.X1, X3 | `World.perceive/apply` | test_food_conservation, test_perception_cases |
| F-11 | A4 | G0.X5, G2.X22 | `GPTCore.learn` | test_individual_learning_isolated |
| F-12 | A23, A3 | G0.X3–X4 | `FieldMedium` | test_field_medium |
| F-13, F-14 | A5, all | G0, G2 | `ForagingSystem` | test_food_conservation_events_and_token_walk |

---

## Verification Evidence (Phase 4 Results)

| Requirement | Evidence | Result |
|---|---|---|
| F-03 | test_gradcheck | Maximum relative error about 1.6e-8 |
| F-04, F-05 | test_overfit, test_param_count | Loss < 0.05; 4,096 parameters (the original microgpt has 4,192) |
| F-06, F-11 | test_batched_equals_single…, test_individual_learning_isolated… | Pass |
| F-07, F-13, F-14 | test_food_conservation_events_and_token_walk | Conserved; number of deliver events = delivery count; both the normal path and the timeout exception path are walked through |
| A6 pretraining | `miat_ants/foraging/weights/base_bc.json` | 9,984 teacher episodes, about 1.04 million tokens; held-out NLL 0.284; most likely action agrees with the teacher 91.2% of the time |
| F-09, F-10 | exp9(a) | See [RESULTS.md](RESULTS.md) (exp9): after BC, the deliveries of GPT ants are 1.07–1.15 times those of rule-based ants, meeting the parity requirement |

### Design notes

- **It is reasonable for behavior cloning to slightly outperform the teacher.** The teacher keeps about 10% noisy actions even in situations where the right action is clear. When the model approximates the teacher's distribution with limited capacity, it "denoises" it slightly.
- **Definition of dialect dispersion.** It is computed as the mean pairwise JS between agents, using the same JS definition as drift, so the values of the two can be compared directly.
