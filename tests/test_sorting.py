"""螞蟻–自動分揀：Action 單元測試、守恆檢查、整合測試。"""
import numpy as np
import pytest

from miat_ants.core.events import Event, EventQueue, PRIORITY_ENV, PRIORITY_LOG
from miat_ants.core.metrics import spatial_entropy, gini, effective_number, edge_jaccard, trail_consensus
from miat_ants.sorting import actions as act
from miat_ants.sorting import AntSortConfig, AntSortSystem


def test_density_bounds_and_probabilities():
    tg = -np.ones((5, 5), int)
    tg[1:4, 1:4] = 0
    counts = act.neighbor_type_counts(tg, 2, 1)
    f = act.local_density(np.array([0, 1]), np.array([[2, 2], [2, 2]]), counts)
    assert f[0] == pytest.approx(1.0) and f[1] == pytest.approx(0.0)
    fs = np.linspace(0, 1, 11)
    assert np.all(np.diff(act.p_pick(fs, 0.1)) < 0)       # 同質性愈高愈不撿
    assert np.all(np.diff(act.p_deposit(fs, 0.1)) > 0)    # 同質性愈高愈會放


def test_arbitration():
    cells = np.array([[1, 1], [1, 1], [2, 2]])
    g, n = act.arbitrate(cells, np.array([True, True, True]))
    assert g.tolist() == [True, False, True] and n == 1


def test_entropy_extremes():
    sep = np.zeros((16, 16), int)
    sep[:, 8:] = 1
    rnd = np.random.default_rng(0).integers(0, 2, (16, 16))
    assert spatial_entropy(sep, 2, 8) == pytest.approx(0.0)
    assert spatial_entropy(rnd, 2, 8) > 0.9


def test_object_conservation_and_clustering():
    sysm = AntSortSystem(AntSortConfig(seed=2, max_iterations=60))
    r = sysm.run()
    on_grid = (r.type_grid >= 0).sum()
    carried = (sysm.carry >= 0).sum()
    assert on_grid + carried == 200                       # 物資守恆
    ids = r.id_grid[r.id_grid >= 0].tolist() + sysm.carry[sysm.carry >= 0].tolist()
    assert sorted(ids) == list(range(200))
    e = r.history["entropy"]
    assert e[-1] < e[0] - 0.1                             # 聚類發生
    picks = len(r.events.filter("pick"))
    drops = len(r.events.filter("drop"))
    assert picks - drops == carried                       # 事件紀錄與狀態一致（可追溯）


def test_blind_mode_does_not_cluster():
    r = AntSortSystem(AntSortConfig(seed=2, max_iterations=60, sense_mode="blind")).run()
    e = r.history["entropy"]
    assert e[-1] > 0.75


def test_event_queue_priority_and_ignore():
    q = EventQueue([Event("a", 5, "x", priority=PRIORITY_LOG),
                    Event("b", 5, "x", priority=PRIORITY_ENV),
                    Event("old", 1, "x", policy="ignore")])
    out = q.pop_due(5)
    assert [e.event_type for e in out] == ["b", "a"]


def test_metrics():
    assert gini([1, 1, 1, 1]) == pytest.approx(0)
    assert gini([0, 0, 0, 1]) == pytest.approx(0.75)
    assert effective_number([0.25] * 4) == pytest.approx(4)
    assert edge_jaccard([0, 1, 2, 3], [1, 2, 3, 0]) == 1.0
    assert trail_consensus(np.ones((5, 5))) == pytest.approx(0, abs=1e-9)
