"""
主題三（對照實驗）：「遲滯」是真的嗎？
=====================================
原 exp6 的兩個混淆：(i) 封路前的路徑不一定是最佳解；(ii) 沒有「不封路」的對照組，
「解封後沒回到原路徑」可能只是正常的持續優化／漂移。

對照一（配對對照組）：冷啟動，同一種子各跑「不封路」與「封路→解封」。
    比較 T_END 時：蟻群當下表現（最後 20 週期本週期最佳的平均差距）、存檔最佳解差距、
    介質路徑（集體記憶）與 T1 的相似度、存檔路徑與 T1 的相似度。
    → 若擾動組與對照組無差異，則「沒回到原路徑」只是漂移，不是遲滯。

對照二（從最佳解出發）：暖啟動——介質預先寫入已知最佳解 L*（穩態費洛蒙量），
    存檔最佳解也設為 L*。封鎖 L* 上的一條邊、之後解封。
    問：解封後 W = T_END − T2 個週期內，蟻群能否「重新找回」L*？
    比較基準：同一種子的冷啟動蟻群從零開始，在同樣 W 個週期內「初次找到」L* 的比例。
    → 若重新找回的比例顯著低於初次找到，表示擾動留下的痕跡（繞道上的費洛蒙）
      阻礙了回歸——這才是可主張的遲滯（路徑依賴）。
統計：配對 Wilcoxon + bootstrap 95% CI（連續量）；McNemar 精確檢定（配對二元量）；
      比例附 Clopper–Pearson 95% CI。
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binomtest

from common import (QUICK, SERIES, INK2, save_csv, save_fig, write_summary,
                    pmap, paired_stats)
from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.core.metrics import edge_jaccard
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities, run_aco
from miat_ants.tsp import actions as act

N, M, Q = 30, 30, 100.0
T1, T2, T_END = (40, 90, 140) if QUICK else (60, 140, 220)
W = T_END - T2
import os
SEEDS = 4 if QUICK else int(os.environ.get("EXP8_SEEDS", "50"))
RHOS = (0.5, 0.9) if QUICK else (0.3, 0.5, 0.9)
COORDS = random_cities(N, seed=30)
D = act.distance_matrix(COORDS)
TOL = 1e-6


def reference_optimum():
    """多次 ACO + 2-opt 取得參考最佳解（30 城市下各次結果一致，視為最佳解）。"""
    best = None
    for s in range(4):
        r = run_aco(COORDS, n_ants=M, max_cycles=150, seed=900 + s, track_provenance=False)
        t = act.two_opt(r.best_tour, D)
        L = act.tour_length(t, D)
        if best is None or L < best[0] - 1e-9:
            best = (L, t)
    return best


OPT_LEN, OPT_TOUR = reference_optimum()


def ev(kind, t, edge):
    return Event(kind, t, "environment", {"edge": list(edge), "factor": 1000.0}, PRIORITY_ENV, "interrupt")


THRESH = (0.0, 0.5, 1.0)     # 「找到」的判準：與 L* 差距 ≤ 0%、0.5%、1%


def first_hit(series, start, pct=0.0):
    lim = OPT_LEN * (1 + pct / 100) + TOL
    for k in range(start, len(series)):
        if series[k] <= lim:
            return k - start
    return -1


def summarize(h, ref_best, ref_med):
    cb = np.array(h["cycle_best"])
    return {"perf_gap": 100 * (cb[-20:].mean() / OPT_LEN - 1),
            "archive_gap": 100 * (h["best_so_far"][-1] / OPT_LEN - 1),
            "J_medium": edge_jaccard(h["medium_tour"][-1], ref_med),
            "J_best": edge_jaccard(h["best_tour"][-1], ref_best)}


def one(args):
    start, rho, seed = args
    kw = dict(n_ants=M, rho=rho, Q=Q, max_cycles=T_END, seed=seed, track_provenance=False,
              record_medium_tour=True)
    if start == "warm":
        kw.update(init_tour=OPT_TOUR, init_best=True, init_boost=M * Q / OPT_LEN / (1 - rho))
    ctrl = AntTSPSystem(COORDS, AntTSPConfig(**kw)).run()
    h0 = ctrl.history
    ref_best, ref_med = h0["best_tour"][T1], h0["medium_tour"][T1]
    target = OPT_TOUR if start == "warm" else ref_best
    edges = act.tour_edge_list(target)
    e = edges[seed % len(edges)]
    pert = AntTSPSystem(COORDS, AntTSPConfig(**kw, perturbations=[ev("block_edge", T1, e),
                                                                   ev("unblock_edge", T2, e)])).run()
    h1 = pert.history
    assert h1["best_tour"][T1] == ref_best           # 配對：擾動前完全相同
    row = {"start": start, "rho": rho, "seed": seed, "blocked_edge": f"{e[0]}-{e[1]}",
           "T1_archive_gap": 100 * (h0["best_so_far"][T1] / OPT_LEN - 1)}
    row.update({f"ctrl_{k}": v for k, v in summarize(h0, ref_best, ref_med).items()})
    row.update({f"pert_{k}": v for k, v in summarize(h1, ref_best, ref_med).items()})
    # 冷啟動：從零開始初次找到 L* 所需週期；暖啟動：解封後重新找回 L* 所需週期
    for pct in THRESH:
        row[f"fresh_hit_{pct}"] = first_hit(h0["best_so_far"], 0, pct) if start == "cold" else None
        row[f"rehit_{pct}"] = first_hit(h1["best_so_far"], T2 + 1, pct) if start == "warm" else None
    row["pert_traj"] = [100 * (x / OPT_LEN - 1) for x in h1["cycle_best"]]
    row["ctrl_traj"] = [100 * (x / OPT_LEN - 1) for x in h0["cycle_best"]]
    return row


def mcnemar_exact(a, b):
    """配對二元：a 成功 b 失敗的數目 vs 反之，雙尾精確檢定。"""
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    p = 1.0 if n10 + n01 == 0 else float(binomtest(n10, n10 + n01, 0.5).pvalue)
    return p, n10, n01


def prop_ci(k, n):
    ci = binomtest(k, n).proportion_ci(method="exact")
    return ci.low, ci.high


def main():
    jobs = [(st, rho, s) for st in ("cold", "warm") for rho in RHOS for s in range(SEEDS)]
    rows = pmap(one, jobs)
    save_csv("exp8_topic3_controls.csv", [{k: v for k, v in r.items() if not k.endswith("_traj")} for r in rows])
    from common import RESULTS
    np.savez_compressed(f"{RESULTS}/exp8_trajectories.npz",
                        keys=np.array([f"{r['start']}|{r['rho']}|{r['seed']}" for r in rows]),
                        ctrl=np.array([r["ctrl_traj"] for r in rows]), pert=np.array([r["pert_traj"] for r in rows]))

    summ = ["## 實驗8（主題三・對照實驗）：「遲滯」是真的嗎？", "",
            f"設定：{N} 城市、{M} 隻螞蟻；T1={T1} 封路、T2={T2} 解封、T_END={T_END}；每格 {SEEDS} 個配對種子。",
            f"參考最佳解 L* = {OPT_LEN:.3f}（多次 ACO + 2-opt 結果一致）。", ""]

    # ---------------- 對照一
    summ += ["### 對照一：冷啟動，擾動組 − 對照組（配對）", "",
             "| ρ | 指標 | 對照 | 擾動 | 差（擾動−對照）[95% CI] | Wilcoxon p |", "|---|---|---|---|---|---|"]
    metrics = [("perf_gap", "當下表現差距%"), ("archive_gap", "存檔最佳差距%"),
               ("J_medium", "介質路徑 vs T1 (J)"), ("J_best", "存檔路徑 vs T1 (J)")]
    st_rows = []
    for rho in RHOS:
        R = [r for r in rows if r["start"] == "cold" and r["rho"] == rho]
        for key, lab in metrics:
            c = np.array([r[f"ctrl_{key}"] for r in R]); p_ = np.array([r[f"pert_{key}"] for r in R])
            ps = paired_stats(p_ - c)
            st_rows.append({"part": "control1", "rho": rho, "metric": key, "ctrl": c.mean(), "pert": p_.mean(), **ps})
            summ.append(f"| {rho} | {lab} | {c.mean():.3f} | {p_.mean():.3f} | {ps['mean']:+.3f} "
                        f"[{ps['ci_lo']:+.3f}, {ps['ci_hi']:+.3f}] | {ps['p']:.3g} |")
    summ.append("")

    # ---------------- 對照二
    summ += [f"### 對照二：從最佳解出發——解封後 {W} 週期內「重新找回」vs 冷啟動 {W} 週期內「初次找到」", "",
             "「找到」以三種判準計：與 L* 差距 ≤ 0%（精確）、≤ 0.5%、≤ 1%。", "",
             "| ρ | 判準 | 初次找到（冷）[95% CI] | 重新找回（暖＋擾動）[95% CI] | McNemar p（配對）| "
             "所需週期中位數（初次／重新） |", "|---|---|---|---|---|---|"]
    for rho in RHOS:
        Rc = {r["seed"]: r for r in rows if r["start"] == "cold" and r["rho"] == rho}
        Rw = {r["seed"]: r for r in rows if r["start"] == "warm" and r["rho"] == rho}
        seeds = sorted(Rc)
        for pct in THRESH:
            fresh = [0 <= Rc[s][f"fresh_hit_{pct}"] <= W for s in seeds]
            reh = [Rw[s][f"rehit_{pct}"] >= 0 for s in seeds]
            p, n10, n01 = mcnemar_exact(fresh, reh)
            fl, fh = prop_ci(sum(fresh), len(seeds)); rl, rh = prop_ci(sum(reh), len(seeds))
            tf = [Rc[s][f"fresh_hit_{pct}"] for s in seeds if 0 <= Rc[s][f"fresh_hit_{pct}"] <= W]
            tr = [Rw[s][f"rehit_{pct}"] for s in seeds if Rw[s][f"rehit_{pct}"] >= 0]
            st_rows.append({"part": "control2", "rho": rho, "metric": f"fresh_vs_rehit_{pct}",
                            "ctrl": np.mean(fresh), "pert": np.mean(reh), "mean": np.mean(reh) - np.mean(fresh),
                            "ci_lo": rl, "ci_hi": rh, "d_z": float("nan"), "p": p, "n": len(seeds)})
            med = lambda x: f"{np.median(x):.0f}" if x else "—"
            summ.append(f"| {rho} | ≤{pct}% | {np.mean(fresh):.2f} [{fl:.2f}, {fh:.2f}] | "
                        f"{np.mean(reh):.2f} [{rl:.2f}, {rh:.2f}] | {p:.3g}（{n10} vs {n01}）| {med(tf)}／{med(tr)} |")
    pooled = {pct: ([], []) for pct in THRESH}
    for rho in RHOS:
        Rc = {r["seed"]: r for r in rows if r["start"] == "cold" and r["rho"] == rho}
        Rw = {r["seed"]: r for r in rows if r["start"] == "warm" and r["rho"] == rho}
        for s in sorted(Rc):
            for pct in THRESH:
                pooled[pct][0].append(0 <= Rc[s][f"fresh_hit_{pct}"] <= W)
                pooled[pct][1].append(Rw[s][f"rehit_{pct}"] >= 0)
    summ += ["", f"合併 {len(RHOS)} 個 ρ（每判準 n = {len(RHOS) * SEEDS} 對）：", ""]
    for pct in THRESH:
        f_, r_ = pooled[pct]
        p, n10, n01 = mcnemar_exact(f_, r_)
        summ.append(f"- ≤{pct}%：初次找到 {np.mean(f_):.2f}，重新找回 {np.mean(r_):.2f}，McNemar p = {p:.3g}（{n10} vs {n01}）")
    save_csv("exp8_topic3_stats.csv", st_rows)
    summ.append("")

    # ---------------- 圖
    fig, axes = plt.subplots(2, len(RHOS), figsize=(4.2 * len(RHOS), 6.4), sharex=True)
    for i, st in enumerate(("cold", "warm")):
        for j, rho in enumerate(RHOS):
            ax = axes[i, j]
            R = [r for r in rows if r["start"] == st and r["rho"] == rho]
            ax.plot(np.mean([r["ctrl_traj"] for r in R], axis=0), color=SERIES[0], lw=1.4, label="對照（不封路）")
            ax.plot(np.mean([r["pert_traj"] for r in R], axis=0), color=SERIES[1], lw=1.4, label="封路→解封")
            ax.axvspan(T1, T2, color="#e4e3df", alpha=0.6, lw=0)
            ax.set_ylim(0, 10)
            ax.set_title(f"{'冷啟動' if st == 'cold' else '暖啟動（最佳解）'}  ρ={rho}", fontsize=10)
            if j == 0:
                ax.set_ylabel("本週期最佳與 L* 差距 (%)")
            if i == 1:
                ax.set_xlabel("週期")
    axes[0, 0].legend(loc="upper right", fontsize=8)
    fig.suptitle(f"擾動與對照（{SEEDS} 個配對種子平均；灰區＝封路期間）", x=0.01, ha="left", fontweight="bold")
    save_fig(fig, "exp8_topic3_controls.png")
    write_summary("exp8", summ)


if __name__ == "__main__":
    main()
