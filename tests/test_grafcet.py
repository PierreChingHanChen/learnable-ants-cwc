"""Phase 4 第一、二層：模型檢查與 Controller 模擬（Token 走查）。"""
import numpy as np
import pytest

from miat_ants.core.grafcet import Grafcet, GrafcetError, SuperLoop


def flag(d, k):
    return lambda: d[k]


def test_fundamental_block_and_reset():
    sig = {"r0": False}
    g = Grafcet("G")
    g.add_step("X0", initial=True).add_step("X1", terminal=True)
    g.add_transition("T0", ["X0"], ["X1"], flag(sig, "r0"), "r0")
    g.reset()
    assert g.active() == ["X0"]
    g.tick()
    assert g.active() == ["X0"]          # 條件未成立，Token 不動
    sig["r0"] = True
    g.tick()
    assert g.active() == ["X1"]
    g.reset()
    assert g.active() == ["X0"]


def test_true_condition_rejected():
    g = Grafcet("G")
    g.add_step("X0", initial=True).add_step("X1", terminal=True)
    with pytest.raises(GrafcetError):
        g.add_transition("T0", ["X0"], ["X1"], True, "True")


def test_and_divergence_convergence():
    s = {"go": True, "join": False}
    g = Grafcet("G")
    for k in ("X0", "X1", "X2"):
        g.add_step(k, initial=(k == "X0"))
    g.add_step("X3", terminal=True)
    g.add_transition("T0", ["X0"], ["X1", "X2"], flag(s, "go"), "go")
    g.add_transition("T1", ["X1", "X2"], ["X3"], flag(s, "join"), "join")
    g.reset()
    g.tick()
    assert set(g.active()) == {"X1", "X2"}
    g.tick()
    assert set(g.active()) == {"X1", "X2"}  # 等待共同同步條件
    s["join"] = True
    g.tick()
    assert g.active() == ["X3"]


def test_or_divergence_priority_and_conflict_count():
    g = Grafcet("G")
    g.add_step("X0", initial=True).add_step("X1", terminal=True).add_step("X2", terminal=True)
    g.add_transition("Ta", ["X0"], ["X1"], lambda: True if False else np.True_, "a")
    g.add_transition("Tb", ["X0"], ["X2"], lambda: np.True_, "b")
    g.reset()
    g.tick()
    assert g.active() == ["X1"]       # 宣告順序 = 優先序（if / else-if）
    assert g.conflicts == 1           # 非互斥條件被偵測出來（模型審查訊號）


def test_validate_detects_unreachable_and_dead_end():
    g = Grafcet("G")
    g.add_step("X0", initial=True).add_step("X1").add_step("X9")
    g.add_transition("T0", ["X0"], ["X1"], lambda: True and np.True_, "c")
    issues = g.validate()
    assert any("X1 沒有離開條件" in i for i in issues)
    assert any("X9" in i for i in issues)


def test_p1_action_runs_once_and_n_runs_each_clock():
    cnt = {"p1": 0, "n": 0}
    g = Grafcet("G")
    g.add_step("X0", lambda m: cnt.__setitem__("p1", cnt["p1"] + 1), "P1", initial=True)
    g.add_step("X1", lambda m: cnt.__setitem__("n", cnt["n"] + 1), "N", terminal=True)
    g.add_transition("T0", ["X0"], ["X1"], lambda: g.clock >= 3, "clock>=3")
    g.reset()
    for _ in range(6):
        g.tick()
    assert cnt["p1"] == 1
    assert cnt["n"] == 3


def test_population_grafcet_is_elementwise():
    n = 5
    cond = np.array([1, 0, 1, 0, 0], dtype=bool)
    g = Grafcet("P", n=n)
    g.add_step("X0", initial=True).add_step("X1", terminal=True)
    g.add_transition("T0", ["X0"], ["X1"], lambda: cond, "cond")
    g.reset()
    g.tick()
    assert g.X["X1"].tolist() == cond.tolist()
    assert g.X["X0"].tolist() == (~cond).tolist()


def test_sub_grafcet_coordination_not_call_return():
    """上層 X1 啟動子控制器；子控制器以 X12 回報完成；上層離開後子控制器回到 X10。"""
    G0 = Grafcet("G0")
    G1 = Grafcet("G1")
    G0.add_step("X0", initial=True).add_step("X1").add_step("X2", terminal=True)
    G0.add_transition("T0", ["X0"], ["X1"], lambda: np.True_, "start")
    G0.add_transition("T1", ["X1"], ["X2"], lambda: G1.X["X12"], "G1.X12")
    G1.add_step("X10", initial=True).add_step("X11").add_step("X12")
    G1.add_transition("T10", ["X10"], ["X11"], lambda: G0.X["X1"], "G0.X1")
    G1.add_transition("T11", ["X11"], ["X12"], lambda: np.True_, "work_done")
    G1.add_transition("T12", ["X12"], ["X10"], lambda: ~G0.X["X1"], "¬G0.X1")
    loop = SuperLoop([G0, G1])
    loop.reset()
    seen = []
    for _ in range(6):
        loop.tick()
        seen.append((tuple(G0.active()), tuple(G1.active())))
    assert seen[-1] == (("X2",), ("X10",))
    assert (("X1",), ("X12",)) in seen
