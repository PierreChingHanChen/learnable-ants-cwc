"""
A0 螞蟻–TSP 最佳化系統（MIAT 2.0 重寫版）
========================================

IDEF0 功能分解
--------------
A0  以蟻群集體搜尋 TSP 最短巡迴
 ├─ A1  初始化問題        (座標 → 距離 D、能見度 η、介質 τ0)
 ├─ A2  建構巡迴          (Sub-GRAFCET G2)
 │    ├─ A21 放置螞蟻、清空 tabu
 │    ├─ A22 全體螞蟻前進一步（式 1、2）
 │    └─ A23 閉合巡迴
 ├─ A3  評估巡迴          (L_k、本週期最佳、全域最佳)
 ├─ A4  更新費洛蒙        (式 3–5，經由 GraphMedium)
 └─ A5  紀錄與事件處理    (量測、外部擾動事件、終止判斷)

GRAFCET
-------
G0（主控制器，協調 A1–A5）
  X0(init) --T0: A1 完成--> X1 --T1: G2.X24--> X2 --T2: A3 完成--> X3
  X3 --T3: A4 完成--> X4 --T4a: A5 完成 ∧ 未終止--> X1
                         --T4b: A5 完成 ∧ 終止 -->  X5(terminal)
G2（巡迴建構子控制器，由 G0.X1 啟動，以 X24 回報完成）
  X20(init) --T20: G0.X1--> X21 --T21: 已放置--> X22
  X22 --T22: 所有巡迴已含 n 城市--> X23 --T23: 已閉合--> X24 --T24: ¬G0.X1--> X20
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from ..core.events import Event, EventLog, EventQueue, PRIORITY_ENV
from ..core.grafcet import Grafcet, SuperLoop
from ..core.medium import GraphMedium
from ..core import metrics
from . import actions as act


@dataclass
class AntTSPConfig:
    n_ants: int = 25
    alpha: float = 1.0
    beta: float = 5.0
    rho: float = 0.5            # 殘留係數（式 3）
    Q: float = 100.0            # 費洛蒙數量（式 5）
    tau0: float = 0.1
    max_cycles: int = 100
    seed: Optional[int] = None
    # --- 主題一：介質 ---
    medium_mode: str = "shared"         # 'shared' (We) / 'private' (I)
    sense_delay: int = 0
    sense_noise: float = 0.0
    # --- 主題二：責任追溯 ---
    track_provenance: bool = True
    log_deposits: bool = False          # 每隻螞蟻的每次沉積寫入事件紀錄
    # --- 主題三：擾動 ---
    perturbations: Sequence[Event] = field(default_factory=list)
    watch_edges: Sequence[tuple] = field(default_factory=list)   # 逐週期紀錄其費洛蒙
    disabled_ants: Sequence[int] = field(default_factory=list)   # 反事實實驗：一開始就不參與
    record_trace: bool = False
    # 個體異質性：每隻螞蟻的 α、β 乘上 lognormal(0, h)。h=0 時螞蟻完全同質、可互換。
    heterogeneity: float = 0.0
    # 擴充點（主題一）：自訂個體決策策略，可替換為 LLM 代理人。
    # policy(agent_id, cur, allowed_mask, tau_row, eta_row, rng) -> next_city
    # None 時使用式(1)。介面契約：只能讀取傳入的 tau_row（經由介質感知），不得直接存取介質。
    policy: Optional[Callable] = None
    # 主題三對照實驗：暖啟動（介質預先寫入一條路徑，例如已知最佳解）
    init_tour: Optional[Sequence[int]] = None
    init_boost: float = 0.0
    init_best: bool = False              # 暖啟動時同時把 init_tour 設為存檔中的全域最佳解
    record_medium_tour: bool = False     # 每週期紀錄介質所指向的巡迴（集體記憶）


@dataclass
class AntTSPResult:
    best_tour: List[int]
    best_length: float
    history: Dict[str, list]
    events: EventLog
    medium: GraphMedium
    cfg: AntTSPConfig
    ticks: int


class AntTSPSystem:
    def __init__(self, coords: np.ndarray, cfg: AntTSPConfig):
        self.coords = np.asarray(coords, dtype=float)
        self.n = len(self.coords)
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.log = EventLog()
        self.queue = EventQueue(cfg.perturbations)
        self._build_model()

    # ================================================================ MODEL
    def _build_model(self) -> None:
        g0 = Grafcet("G0", idef0="A0", event_log=self.log)
        g2 = Grafcet("G2", idef0="A2", event_log=self.log)
        self.g0, self.g2 = g0, g2
        g0.log_transitions = g2.log_transitions = False

        g0.add_step("X0", self.a1_initialize, "P1", initial=True, desc="初始化", idef0="A1")
        g0.add_step("X1", None, desc="建構巡迴（啟動 G2）", idef0="A2")
        g0.add_step("X2", self.a3_evaluate, "P1", desc="評估巡迴", idef0="A3")
        g0.add_step("X3", self.a4_update_pheromone, "P1", desc="更新費洛蒙", idef0="A4")
        g0.add_step("X4", self.a5_record_and_events, "P1", desc="紀錄／事件／終止判斷", idef0="A5")
        g0.add_step("X5", self.a6_report, "P1", terminal=True, desc="輸出結果", idef0="A5")
        g0.add_transition("T0", ["X0"], ["X1"], lambda: g0.done["X0"], "init_done")
        g0.add_transition("T1", ["X1"], ["X2"], lambda: g2.X["X24"], "G2.X24（巡迴建構完成）")
        g0.add_transition("T2", ["X2"], ["X3"], lambda: g0.done["X2"], "eval_done")
        g0.add_transition("T3", ["X3"], ["X4"], lambda: g0.done["X3"], "update_done")
        # Divergence OR：兩條件互斥（finished 與 ¬finished）
        g0.add_transition("T4a", ["X4"], ["X1"], lambda: g0.done["X4"] & (not self.finished), "record_done ∧ ¬finished")
        g0.add_transition("T4b", ["X4"], ["X5"], lambda: g0.done["X4"] & self.finished, "record_done ∧ finished")

        g2.add_step("X20", None, initial=True, desc="等待啟動", idef0="A2")
        g2.add_step("X21", self.a21_place_ants, "P1", desc="放置螞蟻", idef0="A21")
        g2.add_step("X22", self.a22_step_all_ants, "N", desc="全體前進一步", idef0="A22")
        g2.add_step("X23", self.a23_close_tours, "P1", desc="閉合巡迴", idef0="A23")
        g2.add_step("X24", None, desc="完成（回報 G0）", idef0="A2")
        g2.add_transition("T20", ["X20"], ["X21"], lambda: g0.X["X1"], "G0.X1")
        g2.add_transition("T21", ["X21"], ["X22"], lambda: g2.done["X21"], "placed")
        g2.add_transition("T22", ["X22"], ["X23"], lambda: self.tours_complete, "tours_complete（tabu 已滿）")
        g2.add_transition("T23", ["X23"], ["X24"], lambda: g2.done["X23"], "closed")
        g2.add_transition("T24", ["X24"], ["X20"], lambda: ~g0.X["X1"], "¬G0.X1")

        for g in (g0, g2):
            g.record_trace = self.cfg.record_trace
            issues = g.validate()
            if issues:
                raise ValueError(f"{g.name} 模型審查未通過: {issues}")
        self.loop = SuperLoop([g0, g2])

    # ============================================================== ACTIONS
    # ---- A1
    def a1_initialize(self, _m) -> None:
        c = self.cfg
        self.D_true = act.distance_matrix(self.coords)
        self.cost_factor = np.ones((self.n, self.n))     # 主題三：封路以成本倍數表示
        self._refresh_cost()
        self.medium = GraphMedium(self.n, c.n_ants, c.tau0, c.rho, mode=c.medium_mode,
                                  track_provenance=c.track_provenance,
                                  sense_delay=c.sense_delay, sense_noise=c.sense_noise,
                                  rng=self.rng)
        if c.init_tour is not None and c.init_boost > 0:
            self.medium.imprint(act.tour_edge_list(c.init_tour), c.init_boost)
        hrng = np.random.default_rng(None if c.seed is None else c.seed + 7919)
        h = c.heterogeneity
        self.ant_alpha = c.alpha * (hrng.lognormal(0, h, c.n_ants) if h > 0 else np.ones(c.n_ants))
        self.ant_beta = c.beta * (hrng.lognormal(0, h, c.n_ants) if h > 0 else np.ones(c.n_ants))
        self.ant_active = np.ones(c.n_ants, dtype=bool)
        self.ant_active[list(c.disabled_ants)] = False
        self.cycle = 0
        self.finished = False
        self.best_tour: Optional[List[int]] = None
        self.best_len = np.inf
        if c.init_tour is not None and c.init_best:
            self.best_tour = [int(x) for x in c.init_tour]
            self.best_len = act.tour_length(self.best_tour, self.D)
        self.hist: Dict[str, list] = {k: [] for k in (
            "cycle", "cycle_best", "cycle_mean", "best_so_far", "consensus",
            "n_active", "medium_cut", "best_tour")}
        self.hist["watch"] = []
        self.hist["medium_tour"] = []
        self.g0.mark_done("X0")

    def _refresh_cost(self) -> None:
        self.D = self.D_true * self.cost_factor
        self.eta = act.visibility(self.D)

    # ---- A21
    def a21_place_ants(self, _m) -> None:
        c = self.cfg
        self.ants = np.flatnonzero(self.ant_active)
        starts = act.place_ants(len(self.ants), self.n, self.rng)
        self.tours = [[int(s)] for s in starts]
        self.visited = np.zeros((len(self.ants), self.n), dtype=bool)
        self.visited[np.arange(len(self.ants)), starts] = True
        self.n_steps = 0
        self.tours_complete = self.n <= 1
        self.g2.mark_done("X21")

    # ---- A22
    def a22_step_all_ants(self, _m) -> None:
        c = self.cfg
        for idx, k in enumerate(self.ants):
            tau = self.medium.sense(int(k))
            cur = self.tours[idx][-1]
            if c.policy is None:
                nxt = act.choose_next(cur, self.visited[idx], tau, self.eta,
                                      self.ant_alpha[k], self.ant_beta[k], self.rng)
            else:
                nxt = int(c.policy(int(k), cur, ~self.visited[idx], tau[cur], self.eta[cur], self.rng))
                if self.visited[idx, nxt]:
                    raise ValueError(f"policy 回傳了已拜訪城市 {nxt}（違反 tabu 契約）")
            self.tours[idx].append(nxt)
            self.visited[idx, nxt] = True
        self.n_steps += 1
        self.tours_complete = self.n_steps >= self.n - 1     # 完成事件，不是 True

    # ---- A23
    def a23_close_tours(self, _m) -> None:
        # 巡迴以 list 表示，閉合邊 (last, first) 由 tour_length/tour_edge_list 隱含處理
        assert all(act.is_valid_tour(t, self.n) for t in self.tours)
        self.g2.mark_done("X23")

    # ---- A3
    def a3_evaluate(self, _m) -> None:
        self.lengths = np.array([act.tour_length(t, self.D) for t in self.tours])
        k = int(np.argmin(self.lengths)) if len(self.lengths) else -1
        # 環境可能改變：以目前成本重新評估既有全域最佳
        if self.best_tour is not None:
            self.best_len = act.tour_length(self.best_tour, self.D)
        if k >= 0 and self.lengths[k] < self.best_len:
            self.best_len = float(self.lengths[k])
            self.best_tour = list(self.tours[k])
        self.g0.mark_done("X2")

    # ---- A4
    def a4_update_pheromone(self, _m) -> None:
        c = self.cfg
        for idx, k in enumerate(self.ants):
            L = self.lengths[idx]
            amt = act.deposit_amount(c.Q, L)
            edges = act.tour_edge_list(self.tours[idx])
            self.medium.deposit(int(k), edges, amt)
            if c.log_deposits:
                self.log.emit("deposit", self.cycle, f"ant:{int(k)}",
                              {"length": float(L), "amount": float(amt),
                               "tour": list(map(int, self.tours[idx]))})
        self.medium.commit()
        self.g0.mark_done("X3")

    # ---- A5
    def a5_record_and_events(self, _m) -> None:
        h = self.hist
        h["cycle"].append(self.cycle)
        h["cycle_best"].append(float(self.lengths.min()) if len(self.lengths) else np.nan)
        h["cycle_mean"].append(float(self.lengths.mean()) if len(self.lengths) else np.nan)
        h["best_so_far"].append(float(self.best_len))
        h["consensus"].append(metrics.trail_consensus(self.medium.snapshot()))
        h["n_active"].append(int(self.ant_active.sum()))
        h["medium_cut"].append(bool(self.medium.is_cut))
        h["best_tour"].append(list(self.best_tour))
        if self.cfg.record_medium_tour:
            h["medium_tour"].append(act.greedy_medium_tour(self.medium.snapshot()))
        if self.cfg.watch_edges:
            snap = self.medium.snapshot()
            h["watch"].append([float(snap[i, j]) for i, j in self.cfg.watch_edges])
        # 外部事件（高優先權）在週期邊界處理
        for ev in self.queue.pop_due(self.cycle):
            self._apply_perturbation(ev)
        self.cycle += 1
        self.finished = self.cycle >= self.cfg.max_cycles
        self.g0.mark_done("X4")

    def _apply_perturbation(self, ev: Event) -> None:
        p, kind = ev.payload, ev.event_type
        if kind == "block_edge":
            i, j = p["edge"]
            self.cost_factor[i, j] = self.cost_factor[j, i] = p.get("factor", 1000.0)
            self._refresh_cost()
        elif kind == "unblock_edge":
            i, j = p["edge"]
            self.cost_factor[i, j] = self.cost_factor[j, i] = 1.0
            self._refresh_cost()
        elif kind == "remove_ants":
            ids = p.get("ids")
            if ids is None:
                live = np.flatnonzero(self.ant_active)
                ids = self.rng.choice(live, size=int(round(p["fraction"] * len(live))), replace=False)
            self.ant_active[list(ids)] = False
        elif kind == "restore_ants":
            self.ant_active[:] = True
            self.ant_active[list(self.cfg.disabled_ants)] = False
        elif kind == "cut_medium":
            self.medium.cut()
        elif kind == "restore_medium":
            self.medium.restore()
        elif kind == "move_city":
            self.coords[p["city"]] = p["xy"]
            self.D_true = act.distance_matrix(self.coords)
            self._refresh_cost()
        else:
            raise ValueError(f"未知的擾動事件 {kind}")
        self.log.emit("perturbation_applied", self.cycle, ev.source_module,
                      {"kind": kind, **{k: v for k, v in p.items()}}, ev.priority)

    # ---- A5 report
    def a6_report(self, _m) -> None:
        self.log.emit("report", self.cycle, "A5",
                      {"best_length": float(self.best_len), "cycles": self.cycle})
        self._reported = True

    # ================================================================== RUN
    def run(self) -> AntTSPResult:
        self.loop.reset()
        self._reported = False
        ticks = self.loop.run(until=lambda: self._reported)
        return AntTSPResult(self.best_tour, float(self.best_len), self.hist, self.log,
                            self.medium, self.cfg, ticks)



def run_aco(coords, **kw) -> AntTSPResult:
    return AntTSPSystem(coords, AntTSPConfig(**kw)).run()
