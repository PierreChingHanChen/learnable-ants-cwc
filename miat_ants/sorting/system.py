"""
A0 螞蟻–自動分揀（聚類）系統（MIAT 2.0 重寫版）
==============================================

IDEF0 功能分解
--------------
A0  以蟻群把隨機分布的異質物資分揀成同質聚落
 ├─ A1  初始化          A11 放置物資、A12 放置螞蟻
 ├─ A2  個體行為        (族群 GRAFCET G2：每隻螞蟻一個同構控制器)
 │    ├─ A21 隨機移動
 │    ├─ A22 評估拿起（式 6、8）
 │    └─ A23 評估放下（式 7、8）
 ├─ A3  量測聚類程度    (空間熵，式 9、10)
 └─ A4  紀錄與事件處理  (外部擾動、終止判斷)

共享介質：物資網格本身（sematectonic stigmergy——工作成果即訊號）。

GRAFCET
-------
G0（主控制器）
  X0(init) --T0: A1 完成--> X1(運行一回合) --T1: 回合步數到--> X2(量測)
  X2 --T2: 量測完成--> X3(紀錄/事件) --T3a: ¬finished--> X1
                                     --T3b:  finished--> X4(terminal)
G2（族群控制器，n = 螞蟻數；移動 Action 只在 G0.X1 時執行）
  X20(空手漫遊) --T20: G0.X1 ∧ 腳下有物資--> X21(評估拿起)
  X21 --T21a: 評估完成 ∧ 拿起--> X22(搬運漫遊)
      --T21b: 評估完成 ∧ 未拿起--> X20
  X22 --T22: G0.X1 ∧ 腳下為空格--> X23(評估放下)
  X23 --T23a: 評估完成 ∧ 放下--> X20
      --T23b: 評估完成 ∧ 未放下--> X22
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from ..core.events import Event, EventLog, EventQueue
from ..core.grafcet import Grafcet, SuperLoop
from ..core import metrics
from . import actions as act


@dataclass
class AntSortConfig:
    H: int = 40
    W: int = 40
    n_types: int = 2
    n_per_type: int = 100
    n_ants: int = 40
    k1: float = 0.05
    k2: float = 0.15
    radius: int = 1
    dissim_a: float = 1.0
    vmax: int = 1                  # 速度 V_x ∈ [1, vmax]
    steps_per_iteration: int = 20  # 一個「迭代」包含的 clock 數（原論文未載明，依表2數值量級校準）
    max_iterations: int = 200
    entropy_block: int = 8
    seed: Optional[int] = None
    # 主題一：感知模式
    sense_mode: str = "local"      # 'local'：依鄰域 f；'blind'：f 隨機（無 stigmergy）
    sense_noise: float = 0.0       # f 加上高斯雜訊 σ
    # 主題二
    log_actions: bool = True       # pick/drop 寫入事件紀錄
    # 主題三
    perturbations: Sequence[Event] = field(default_factory=list)
    record_trace: bool = False
    snapshot_at: Sequence[int] = field(default_factory=list)   # 在這些迭代保存網格快照


@dataclass
class AntSortResult:
    history: Dict[str, list]
    type_grid: np.ndarray
    id_grid: np.ndarray
    events: EventLog
    cfg: AntSortConfig
    ticks: int
    conflicts: int


class AntSortSystem:
    def __init__(self, cfg: AntSortConfig):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.log = EventLog()
        self.queue = EventQueue(cfg.perturbations)
        self._build_model()

    # ================================================================ MODEL
    def _build_model(self) -> None:
        c = self.cfg
        g0 = Grafcet("G0", idef0="A0", event_log=self.log)
        g2 = Grafcet("G2", n=c.n_ants, idef0="A2", event_log=self.log)
        self.g0, self.g2 = g0, g2

        g0.add_step("X0", self.a1_initialize, "P1", initial=True, desc="初始化", idef0="A1")
        g0.add_step("X1", self.a_iteration_clock, "N", desc="運行一回合", idef0="A2")
        g0.add_step("X2", self.a3_measure, "P1", desc="量測空間熵", idef0="A3")
        g0.add_step("X3", self.a4_record_and_events, "P1", desc="紀錄／事件／終止判斷", idef0="A4")
        g0.add_step("X4", self.a5_report, "P1", terminal=True, desc="輸出結果", idef0="A4")
        g0.add_transition("T0", ["X0"], ["X1"], lambda: g0.done["X0"], "init_done")
        g0.add_transition("T1", ["X1"], ["X2"], lambda: g0.done["X1"], "iteration_done")
        g0.add_transition("T2", ["X2"], ["X3"], lambda: g0.done["X2"], "measure_done")
        g0.add_transition("T3a", ["X3"], ["X1"], lambda: g0.done["X3"] & (not self.finished), "record_done ∧ ¬finished")
        g0.add_transition("T3b", ["X3"], ["X4"], lambda: g0.done["X3"] & self.finished, "record_done ∧ finished")

        g2.add_step("X20", self.a21_move, "N", initial=True, desc="空手漫遊", idef0="A21")
        g2.add_step("X21", self.a22_eval_pick, "P1", desc="評估拿起", idef0="A22")
        g2.add_step("X22", self.a21_move, "N", desc="搬運漫遊", idef0="A21")
        g2.add_step("X23", self.a23_eval_drop, "P1", desc="評估放下", idef0="A23")
        g2.add_transition("T20", ["X20"], ["X21"], lambda: self.on_object() if g0.X["X1"].any() else False, "G0.X1 ∧ on_object")
        g2.add_transition("T21a", ["X21"], ["X22"], lambda: g2.done["X21"] & self.pick_ok, "pick_eval_done ∧ picked")
        g2.add_transition("T21b", ["X21"], ["X20"], lambda: g2.done["X21"] & ~self.pick_ok, "pick_eval_done ∧ ¬picked")
        g2.add_transition("T22", ["X22"], ["X23"], lambda: self.on_empty() if g0.X["X1"].any() else False, "G0.X1 ∧ on_empty_cell")
        g2.add_transition("T23a", ["X23"], ["X20"], lambda: g2.done["X23"] & self.drop_ok, "drop_eval_done ∧ dropped")
        g2.add_transition("T23b", ["X23"], ["X22"], lambda: g2.done["X23"] & ~self.drop_ok, "drop_eval_done ∧ ¬dropped")

        for g in (g0, g2):
            g.record_trace = c.record_trace
            issues = g.validate()
            if issues:
                raise ValueError(f"{g.name} 模型審查未通過: {issues}")
        self.loop = SuperLoop([g0, g2])

    # ============================================================ CONDITIONS
    def on_object(self) -> np.ndarray:
        r, c = self.pos[:, 0], self.pos[:, 1]
        return self.alive & (self.type_grid[r, c] >= 0)

    def on_empty(self) -> np.ndarray:
        r, c = self.pos[:, 0], self.pos[:, 1]
        return self.alive & (self.type_grid[r, c] < 0)

    # =============================================================== ACTIONS
    def a1_initialize(self, _m) -> None:
        c = self.cfg
        self.type_grid, self.id_grid = act.place_objects(c.H, c.W, c.n_types, c.n_per_type, self.rng)
        self.obj_type = np.repeat(np.arange(c.n_types), c.n_per_type)
        self.pos = act.place_ants(c.H, c.W, c.n_ants, self.rng)
        self.speed = self.rng.integers(1, c.vmax + 1, size=c.n_ants)
        self.carry = -np.ones(c.n_ants, dtype=int)          # 攜帶的物資 id
        self.alive = np.ones(c.n_ants, dtype=bool)
        self.blind = c.sense_mode == "blind"
        self.pick_ok = np.zeros(c.n_ants, dtype=bool)
        self.drop_ok = np.zeros(c.n_ants, dtype=bool)
        self.last_dropper = -np.ones(c.n_types * c.n_per_type, dtype=int)
        self.iteration = 0
        self.iter_ticks = 0
        self.finished = False
        self.conflicts = 0
        self.hist: Dict[str, list] = {"iteration": [], "entropy": [], "carrying": [],
                                      "n_alive": [], "blind": []}
        self.snapshots = {0: self.type_grid.copy()}
        self.hist["iteration"].append(0)
        self.hist["entropy"].append(self._entropy())
        self.hist["carrying"].append(0)
        self.hist["n_alive"].append(int(c.n_ants))
        self.hist["blind"].append(self.blind)
        self.g0.mark_done("X0")

    def a_iteration_clock(self, _m) -> None:
        self.iter_ticks += 1
        if self.iter_ticks >= self.cfg.steps_per_iteration:
            self.g0.mark_done("X1")

    def _f(self, obj_types: np.ndarray, pos: np.ndarray) -> np.ndarray:
        c = self.cfg
        if self.blind:
            f = self.rng.random(len(obj_types))
        else:
            counts = act.neighbor_type_counts(self.type_grid, c.n_types, c.radius)
            f = act.local_density(obj_types, pos, counts, c.radius, c.dissim_a)
        if c.sense_noise > 0:
            f = np.clip(f + self.rng.normal(0, c.sense_noise, len(f)), 0, 1)
        return f

    def a21_move(self, m: np.ndarray) -> None:
        if not self.g0.X["X1"].any():
            return                                         # 只在 G0.X1 時移動
        m = m & self.alive
        if not m.any():
            return
        self.pos[m] = act.random_moves(self.pos[m], self.speed[m], self.cfg.H, self.cfg.W, self.rng)

    def a22_eval_pick(self, m: np.ndarray) -> None:
        idx = np.flatnonzero(m)
        r, c = self.pos[idx, 0], self.pos[idx, 1]
        oid = self.id_grid[r, c]
        otype = self.type_grid[r, c]
        f = self._f(otype, self.pos[idx])
        p = act.p_pick(f, self.cfg.k1)
        R = self.rng.random(len(idx))
        want = (R < p) & (oid >= 0)
        granted, conf = act.arbitrate(self.pos[idx], want)
        self.conflicts += conf
        ok = np.zeros(self.cfg.n_ants, dtype=bool)
        ok[idx] = granted
        self.pick_ok = np.where(m, ok, self.pick_ok)
        for k_local in np.flatnonzero(granted):
            k = idx[k_local]
            self.carry[k] = oid[k_local]
            self.type_grid[r[k_local], c[k_local]] = -1
            self.id_grid[r[k_local], c[k_local]] = -1
            if self.cfg.log_actions:
                self._log("pick", k, oid[k_local], r[k_local], c[k_local], f[k_local], p[k_local])
        self.g2.mark_done("X21", m)

    def a23_eval_drop(self, m: np.ndarray) -> None:
        idx = np.flatnonzero(m)
        oid = self.carry[idx]
        otype = self.obj_type[oid]
        f = self._f(otype, self.pos[idx])
        p = act.p_deposit(f, self.cfg.k2)
        R = self.rng.random(len(idx))
        r, c = self.pos[idx, 0], self.pos[idx, 1]
        want = (R < p) & (self.type_grid[r, c] < 0)
        granted, conf = act.arbitrate(self.pos[idx], want)
        self.conflicts += conf
        ok = np.zeros(self.cfg.n_ants, dtype=bool)
        ok[idx] = granted
        self.drop_ok = np.where(m, ok, self.drop_ok)
        for k_local in np.flatnonzero(granted):
            k = idx[k_local]
            o = oid[k_local]
            self.type_grid[r[k_local], c[k_local]] = self.obj_type[o]
            self.id_grid[r[k_local], c[k_local]] = o
            self.carry[k] = -1
            self.last_dropper[o] = k
            if self.cfg.log_actions:
                self._log("drop", k, o, r[k_local], c[k_local], f[k_local], p[k_local])
        self.g2.mark_done("X23", m)

    def _log(self, kind, k, o, r, c, f, p) -> None:
        self.log.emit(kind, self.loop.clock, f"ant:{int(k)}",
                      {"obj": int(o), "type": int(self.obj_type[o]), "cell": [int(r), int(c)],
                       "f": round(float(f), 4), "p": round(float(p), 4),
                       "iteration": self.iteration})

    def _entropy(self) -> float:
        return metrics.spatial_entropy(self.type_grid, self.cfg.n_types, self.cfg.entropy_block)

    def a3_measure(self, _m) -> None:
        self.iteration += 1
        self.hist["iteration"].append(self.iteration)
        self.hist["entropy"].append(self._entropy())
        self.hist["carrying"].append(int((self.carry >= 0).sum()))
        self.hist["n_alive"].append(int(self.alive.sum()))
        self.hist["blind"].append(self.blind)
        if self.iteration in self.cfg.snapshot_at:
            self.snapshots[self.iteration] = self.type_grid.copy()
        self.g0.mark_done("X2")

    def a4_record_and_events(self, _m) -> None:
        for ev in self.queue.pop_due(self.iteration):
            self._apply_perturbation(ev)
        self.iter_ticks = 0
        self.finished = self.iteration >= self.cfg.max_iterations
        self.g0.mark_done("X3")

    def _apply_perturbation(self, ev: Event) -> None:
        p, kind = ev.payload, ev.event_type
        c = self.cfg
        if kind == "scramble_region":
            r0, r1, c0, c1 = p["region"]
            sub_t = self.type_grid[r0:r1, c0:c1]
            sub_i = self.id_grid[r0:r1, c0:c1]
            flat = self.rng.permutation(sub_t.size)
            self.type_grid[r0:r1, c0:c1] = sub_t.reshape(-1)[flat].reshape(sub_t.shape)
            self.id_grid[r0:r1, c0:c1] = sub_i.reshape(-1)[flat].reshape(sub_i.shape)
        elif kind == "scramble_all":
            flat = self.rng.permutation(self.type_grid.size)
            self.type_grid = self.type_grid.reshape(-1)[flat].reshape(c.H, c.W)
            self.id_grid = self.id_grid.reshape(-1)[flat].reshape(c.H, c.W)
        elif kind == "remove_ants":
            live = np.flatnonzero(self.alive)
            ids = p.get("ids")
            if ids is None:
                ids = self.rng.choice(live, size=int(round(p["fraction"] * len(live))), replace=False)
            self.alive[list(ids)] = False   # 被移除的螞蟻若攜帶物資，物資隨之凍結（不在網格上）
        elif kind == "restore_ants":
            self.alive[:] = True
        elif kind == "cut_sensing":
            self.blind = True
        elif kind == "restore_sensing":
            self.blind = self.cfg.sense_mode == "blind"
        else:
            raise ValueError(f"未知的擾動事件 {kind}")
        self.log.emit("perturbation_applied", self.iteration, ev.source_module,
                      {"kind": kind, **p}, ev.priority)

    def a5_report(self, _m) -> None:
        self.log.emit("report", self.iteration, "A4", {"entropy": self.hist["entropy"][-1]})
        self._reported = True

    # ================================================================== RUN
    def run(self) -> AntSortResult:
        self.loop.reset()
        self._reported = False
        ticks = self.loop.run(until=lambda: self._reported)
        return AntSortResult(self.hist, self.type_grid, self.id_grid, self.log, self.cfg,
                             ticks, self.conflicts)


def run_sort(**kw) -> AntSortResult:
    return AntSortSystem(AntSortConfig(**kw)).run()
