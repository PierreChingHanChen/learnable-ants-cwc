"""
重現原論文 圖3：螞蟻–TSP 參數實驗（5×5 網格，已知最佳解 24+√2）
參數掃描：螞蟻數、ρ、α、β、Q。每組重複 SEEDS 次，紀錄最佳解平均與標準差。
"""
import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, INK2, save_csv, save_fig, write_summary
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, grid_cities, grid_optimum, random_cities

SEEDS = 2 if QUICK else 5
CYCLES = 40 if QUICK else 100
BASE = dict(n_ants=25, alpha=1.0, beta=5.0, rho=0.5, Q=100.0, max_cycles=CYCLES,
            track_provenance=False)
SWEEPS = {
    "n_ants": [5, 10, 25, 50, 75],
    "rho": [0.1, 0.3, 0.5, 0.7, 0.9],
    "alpha": [0.5, 1, 2, 5, 8],
    "beta": [0, 1, 2, 5, 8],
    "Q": [1, 10, 100, 1000, 10000],
}
LABEL = {"n_ants": "螞蟻數 m", "rho": "殘留係數 ρ", "alpha": "α", "beta": "β", "Q": "費洛蒙數量 Q"}


def sweep(coords, ref, tag):
    rows = []
    for param, values in SWEEPS.items():
        for v in values:
            for s in range(SEEDS):
                cfg = AntTSPConfig(**{**BASE, param: v, "seed": 1000 + s})
                r = AntTSPSystem(coords, cfg).run()
                rows.append({"instance": tag, "param": param, "value": v, "seed": s, "best": r.best_length,
                             "gap_pct": 100 * (r.best_length / ref - 1)})
            print(tag, param, v, "done")
    return rows


def main():
    # 實例一：原論文 5×5 網格（已知最佳解）；實例二：30 城市隨機（較難，參數差異較明顯）
    grid = grid_cities()
    opt = grid_optimum()
    rows = sweep(grid, opt, "grid5x5")
    rnd = random_cities(30, seed=30)
    rows_r = sweep(rnd, 1.0, "random30")
    ref = min(r["best"] for r in rows_r)          # 以全部實驗中找到的最佳值為參考
    for r in rows_r:
        r["gap_pct"] = 100 * (r["best"] / ref - 1)
    rows += rows_r
    save_csv("exp1_tsp_params.csv", rows)

    fig, axes = plt.subplots(1, 5, figsize=(16, 3.6), sharey=True)
    summ = ["## 實驗1：螞蟻–TSP 參數（圖3 重現）", "",
            f"重複 {SEEDS} 次、{CYCLES} 週期。數值為與參考最佳解的平均差距（%）。"
            f"5×5 網格最佳解 {opt:.3f}；30 城市以所有實驗找到的最短 {ref:.1f} 為參考。", ""]
    for ax, (param, values) in zip(axes, SWEEPS.items()):
        xs = np.arange(len(values))
        for k, (tag, lab) in enumerate((("grid5x5", "5×5 網格"), ("random30", "30 城市隨機"))):
            sel = lambda v: [r["gap_pct"] for r in rows if r["instance"] == tag and r["param"] == param and r["value"] == v]
            means = [np.mean(sel(v)) for v in values]
            sds = [np.std(sel(v)) for v in values]
            ax.errorbar(xs + (k - 0.5) * 0.12, means, yerr=sds, color=SERIES[k], marker="o", capsize=3, label=lab)
            summ.append(f"- [{lab}] {LABEL[param]}: " + ", ".join(f"{v}→{m:.2f}%" for v, m in zip(values, means)))
        ax.set_xticks(xs, [str(v) for v in values])
        ax.set_xlabel(LABEL[param])
        ax.set_yscale("symlog", linthresh=1)
    axes[0].set_ylabel("與參考最佳解差距 (%)")
    axes[0].legend(loc="upper right")
    fig.suptitle("圖3 重現：參數對解題品質的影響", x=0.01, ha="left", fontweight="bold")
    save_fig(fig, "exp1_tsp_params.png")
    write_summary("exp1", summ)


if __name__ == "__main__":
    main()
