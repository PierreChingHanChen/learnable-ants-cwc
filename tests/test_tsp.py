"""螞蟻–TSP：Action 單元測試、介質契約、整合測試、Token 走查。"""
import numpy as np
import pytest

from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.core.medium import GraphMedium
from miat_ants.tsp import actions as act
from miat_ants.tsp import AntTSPConfig, AntTSPSystem, grid_cities, grid_optimum, random_cities
from miat_ants.tsp.baselines import simulated_annealing, genetic_algorithm


def test_distance_and_visibility():
    c = np.array([[0, 0], [3, 4], [0, 4]], float)
    D = act.distance_matrix(c)
    assert D[0, 1] == pytest.approx(5.0)
    eta = act.visibility(D)
    assert eta[0, 1] == pytest.approx(0.2) and eta[0, 0] == 0


def test_transition_probabilities_eq1():
    tau = np.array([1.0, 2.0, 1.0, 4.0])
    eta = np.array([0.0, 1.0, 2.0, 1.0])
    allowed = np.array([False, True, True, False])
    p = act.transition_probabilities(tau, eta, allowed, alpha=1, beta=1)
    assert p.sum() == pytest.approx(1)
    assert p[0] == 0 and p[3] == 0                   # tabu 城市機率為 0
    assert p[1] == pytest.approx(2 / 4) and p[2] == pytest.approx(2 / 4)


def test_tour_length_closed():
    c = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
    D = act.distance_matrix(c)
    assert act.tour_length([0, 1, 2, 3], D) == pytest.approx(4.0)


def test_medium_eq3_and_provenance_invariant():
    m = GraphMedium(4, 2, tau0=1.0, rho=0.5)
    m.deposit(0, [(0, 1)], 2.0)
    m.deposit(1, [(0, 1), (1, 2)], 1.0)
    m.commit()
    assert m.tau[0, 1] == pytest.approx(0.5 * 1 + 3.0)    # τ = ρτ + Δτ
    assert m.tau[1, 0] == m.tau[0, 1]
    assert m.check_invariant()
    share = m.provenance_share([(0, 1)])
    assert share.sum() == pytest.approx(1)
    assert share[1] == pytest.approx(2.0 / 3.5)


def test_medium_delay_and_cut():
    m = GraphMedium(3, 1, tau0=1.0, rho=0.5, sense_delay=1)
    m.deposit(0, [(0, 1)], 10.0)
    m.commit()
    assert m.sense(0)[0, 1] == pytest.approx(1.0)        # 讀到上一週期的狀態
    m.cut()
    assert np.all(m.sense(0) == 1.0)


def test_grid_optimum_found_and_token_walk():
    sysm = AntTSPSystem(grid_cities(), AntTSPConfig(n_ants=25, max_cycles=40, seed=3, record_trace=True))
    r = sysm.run()
    assert act.is_valid_tour(r.best_tour, 25)
    assert r.best_length == pytest.approx(grid_optimum(), rel=0.03)
    # Token 走查（正常路徑）：G0 依序經過 X0→X1→X2→X3→X4→X1 ... →X5
    seq = []
    for _, active, _ in sysm.g0.trace:
        if not seq or seq[-1] != active:
            seq.append(active)
    flat = [a[0] for a in seq]
    assert flat[:6] == ["X0", "X1", "X2", "X3", "X4", "X1"]
    assert flat[-1] == "X5"
    assert len(r.history["cycle"]) == 40


def test_seed_reproducibility():
    a = AntTSPSystem(random_cities(15, seed=1), AntTSPConfig(n_ants=10, max_cycles=10, seed=7)).run()
    b = AntTSPSystem(random_cities(15, seed=1), AntTSPConfig(n_ants=10, max_cycles=10, seed=7)).run()
    assert a.best_length == b.best_length and a.best_tour == b.best_tour


def test_exception_path_block_edge():
    """Token 走查（例外路徑）：封鎖目前最佳巡迴上的一條邊，系統須繞開。"""
    coords = grid_cities()
    base = AntTSPSystem(coords, AntTSPConfig(n_ants=25, max_cycles=20, seed=5)).run()
    e = act.tour_edge_list(base.best_tour)[0]
    ev = Event("block_edge", 20, "env", {"edge": list(e), "factor": 1000.0}, PRIORITY_ENV)
    r = AntTSPSystem(coords, AntTSPConfig(n_ants=25, max_cycles=60, seed=5, perturbations=[ev])).run()
    assert tuple(e) not in {tuple(x) for x in act.tour_edge_list(r.best_tour)}
    assert tuple(e[::-1]) not in {tuple(x) for x in act.tour_edge_list(r.best_tour)}
    assert any(x.event_type == "perturbation_applied" for x in r.events.events)


def test_private_mode_runs():
    r = AntTSPSystem(random_cities(12, seed=2),
                     AntTSPConfig(n_ants=8, max_cycles=5, seed=1, medium_mode="private")).run()
    assert act.is_valid_tour(r.best_tour, 12)


def test_baselines_valid():
    c = random_cities(12, seed=2)
    t, L = simulated_annealing(c, n_evals=5000, seed=1)
    assert act.is_valid_tour(t, 12)
    t, L = genetic_algorithm(c, pop=20, generations=30, seed=1)
    assert act.is_valid_tour(t, 12)


def test_custom_policy_contract():
    """擴充點：自訂策略違反 tabu 契約時必須被攔下。"""
    bad = lambda k, cur, allowed, tau, eta, rng: cur
    with pytest.raises(ValueError):
        AntTSPSystem(random_cities(8, seed=1), AntTSPConfig(n_ants=3, max_cycles=2, seed=0, policy=bad)).run()
    ok = lambda k, cur, allowed, tau, eta, rng: int(np.flatnonzero(allowed)[0])
    r = AntTSPSystem(random_cities(8, seed=1), AntTSPConfig(n_ants=3, max_cycles=2, seed=0, policy=ok)).run()
    assert act.is_valid_tour(r.best_tour, 8)


def test_heterogeneity_makes_identity_matter():
    c = random_cities(12, seed=3)
    homo = {AntTSPSystem(c, AntTSPConfig(n_ants=6, max_cycles=8, seed=0, disabled_ants=[k])).run().best_length
            for k in range(6)}
    assert len(homo) == 1          # 同質：移除哪一隻都一樣（可互換）


def test_warm_start_imprint_and_reference_helpers():
    c = random_cities(12, seed=4)
    D = act.distance_matrix(c)
    t = act.two_opt(list(range(12)), D)
    assert act.is_valid_tour(t, 12)
    assert act.tour_length(t, D) <= act.tour_length(list(range(12)), D)
    m = GraphMedium(12, 2, tau0=0.1, rho=0.5)
    m.imprint(act.tour_edge_list(t), 5.0)
    assert m.check_invariant()
    from miat_ants.core.metrics import edge_jaccard
    assert edge_jaccard(act.greedy_medium_tour(m.tau, start=t[0]), t) == 1.0   # 介質指向寫入的路徑
    sysm = AntTSPSystem(c, AntTSPConfig(n_ants=5, max_cycles=3, seed=0, init_tour=t, init_best=True,
                                        init_boost=5.0, record_medium_tour=True))
    r = sysm.run()
    assert r.best_length <= act.tour_length(t, D) + 1e-9
    assert len(r.history["medium_tour"]) == 3
