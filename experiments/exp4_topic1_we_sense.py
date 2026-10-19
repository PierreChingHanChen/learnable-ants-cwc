"""
主題一：數位費洛蒙與「我們感」(We-sense)
=======================================
(a) I think vs We sense：同一演算法，介質 private（各自一份）vs shared（共用）
    → 集體增益 G = L_private / L_shared、路徑共識指數 C
(b) 感知一致性（原論文 5.1.1）：介質讀取延遲 d、讀取雜訊 σ 對集體解題的影響
(c) 分揀系統：local（依鄰域感知）vs blind（不感知介質）vs 感知雜訊
"""
import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, INK2, save_csv, save_fig, write_summary
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.sorting import AntSortSystem, AntSortConfig

import os
SEEDS = 2 if QUICK else int(os.environ.get("EXP4_SEEDS", "20"))
CYCLES = 60 if QUICK else 120
N = 30
BASE = dict(n_ants=30, max_cycles=CYCLES, track_provenance=False)
BETAS = (1.0, 2.0, 5.0)
BETA_SHOW = 2.0        # 圖中呈現的 β；(b) 感知一致性也在此 β 下進行


def run(coords, **kw):
    return AntTSPSystem(coords, AntTSPConfig(**{**BASE, **kw})).run()


def main():
    coords = random_cities(N, seed=30)
    summ = ["## 實驗4（主題一）：stigmergy 與 We-sense", ""]

    # ---------------- (a) private vs shared
    # β 愈大，個體愈依賴自身啟發式（能見度），介質的角色愈小；故掃描 β
    rows, curves, cons = [], {}, {}
    for beta in BETAS:
        for mode in ("private", "shared"):
            for s in range(SEEDS):
                r = run(coords, medium_mode=mode, beta=beta, seed=s)
                rows.append({"beta": beta, "mode": mode, "seed": s, "best": r.best_length,
                             "final_consensus": r.history["consensus"][-1]})
                curves.setdefault((beta, mode), []).append(r.history["best_so_far"])
                cons.setdefault((beta, mode), []).append(r.history["consensus"])
    save_csv("exp4a_private_vs_shared.csv", rows)
    summ += [f"(a) {N} 城市、{SEEDS} 次：", "",
             "| β | L_private (I) | L_shared (We) | 集體增益 G | C_private | C_shared |", "|---|---|---|---|---|---|"]
    for beta in BETAS:
        f = lambda mode, key: np.mean([r[key] for r in rows if r["mode"] == mode and r["beta"] == beta])
        summ.append(f"| {beta} | {f('private','best'):.1f} | {f('shared','best'):.1f} | "
                    f"{f('private','best') / f('shared','best'):.3f} | {f('private','final_consensus'):.3f} | "
                    f"{f('shared','final_consensus'):.3f} |")
    summ.append("")
    curves = {m: curves[(BETA_SHOW, m)] for m in ("shared", "private")}
    cons = {m: cons[(BETA_SHOW, m)] for m in ("shared", "private")}

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    for k, mode in enumerate(("shared", "private")):
        lab = "共享介質（We sense）" if mode == "shared" else "私有介質（I think）"
        axes[0].plot(np.mean(curves[mode], axis=0), color=SERIES[k], label=lab)
        axes[1].plot(np.mean(cons[mode], axis=0), color=SERIES[k], label=lab)
    axes[0].set_xlabel("週期"); axes[0].set_ylabel("目前最佳巡迴長度")
    axes[0].set_title(f"集體解題品質（β={BETA_SHOW}）"); axes[0].legend()
    axes[1].set_xlabel("週期"); axes[1].set_ylabel("路徑共識指數 C")
    axes[1].set_title("介質上的共識形成"); axes[1].legend()
    save_fig(fig, "exp4a_private_vs_shared.png")

    # ---------------- (b) perceptual consistency
    rows_b = []
    for d in (0, 1, 3, 6):
        for s in range(SEEDS):
            r = run(coords, sense_delay=d, beta=BETA_SHOW, seed=s)
            rows_b.append({"factor": "delay", "level": d, "seed": s, "best": r.best_length,
                           "consensus": r.history["consensus"][-1]})
    for sig in (0.0, 0.5, 1.0, 2.0):
        for s in range(SEEDS):
            r = run(coords, sense_noise=sig, beta=BETA_SHOW, seed=s)
            rows_b.append({"factor": "noise", "level": sig, "seed": s, "best": r.best_length,
                           "consensus": r.history["consensus"][-1]})
    save_csv("exp4b_perceptual_consistency.csv", rows_b)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.4), sharey=True)
    for ax, fac, lab in ((axes[0], "delay", "讀取延遲 d（週期）"), (axes[1], "noise", "讀取雜訊 σ")):
        lv = sorted({r["level"] for r in rows_b if r["factor"] == fac})
        m = [np.mean([r["best"] for r in rows_b if r["factor"] == fac and r["level"] == l]) for l in lv]
        sd = [np.std([r["best"] for r in rows_b if r["factor"] == fac and r["level"] == l]) for l in lv]
        ax.errorbar(range(len(lv)), m, yerr=sd, color=SERIES[0], marker="o", capsize=3)
        ax.set_xticks(range(len(lv)), [str(l) for l in lv]); ax.set_xlabel(lab)
        summ.append(f"(b) {lab}: " + ", ".join(f"{l}→{v:.1f}" for l, v in zip(lv, m)))
    axes[0].set_ylabel("最佳巡迴長度")
    fig.suptitle(f"感知一致性：介質讀取延遲與雜訊（β={BETA_SHOW}）", x=0.01, ha="left", fontweight="bold")
    save_fig(fig, "exp4b_perceptual_consistency.png")

    # ---------------- (c) sorting
    its = 150 if QUICK else 400
    rows_c, cur = [], {}
    for lab, kw in (("local", {}), ("noise σ=0.2", {"sense_noise": 0.2}),
                    ("noise σ=0.5", {"sense_noise": 0.5}), ("blind", {"sense_mode": "blind"})):
        es = []
        for s in range(SEEDS):
            r = AntSortSystem(AntSortConfig(seed=s, max_iterations=its, log_actions=False, **kw)).run()
            es.append(r.history["entropy"])
            rows_c.append({"condition": lab, "seed": s, "final_entropy": r.history["entropy"][-1]})
        cur[lab] = np.mean(es, axis=0)
    save_csv("exp4c_sorting_sensing.csv", rows_c)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for k, (lab, e) in enumerate(cur.items()):
        ax.plot(e, color=SERIES[k], label=lab)
        summ.append(f"(c) 分揀 {lab}: 最終 E_S={e[-1]:.3f}")
    ax.set_xlabel("迭代"); ax.set_ylabel("空間熵 E_S"); ax.legend()
    ax.set_title("分揀：感知介質（作品即訊號）的必要性")
    save_fig(fig, "exp4c_sorting_sensing.png")
    write_summary("exp4", summ)


if __name__ == "__main__":
    main()
