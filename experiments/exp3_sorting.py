"""
重現原論文 圖7、圖8、表2：螞蟻–自動分類系統
 圖7：1000 迭代的空間熵收斂
 圖8：螞蟻數（10/20/50/100）與 100 迭代後的空間熵
 表2：k1、k2 對 100/500/1000 迭代空間熵的影響
"""
import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, INK2, save_csv, save_fig, write_summary
from miat_ants.sorting import AntSortSystem, AntSortConfig

ITERS = 300 if QUICK else 1000
SEEDS = 2 if QUICK else 3
CHECK = [100, 300] if QUICK else [100, 500, 1000]
K_TABLE = [(0.05, 0.10), (0.05, 0.15), (0.05, 0.20), (0.05, 0.30),
           (0.02, 0.20), (0.04, 0.20), (0.08, 0.20), (0.15, 0.20)]


def snapshot_grid(ax, grid, title):
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(["#fcfcfb", SERIES[0], SERIES[1]])
    ax.imshow(grid + 1, cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    ax.set_title(title, fontsize=10)


def main():
    summ = ["## 實驗3：螞蟻–自動分類系統（圖7、圖8、表2 重現）", ""]

    # ---- 圖7 + 圖6 快照
    sysm = AntSortSystem(AntSortConfig(seed=11, max_iterations=ITERS, log_actions=False,
                                       snapshot_at=[50, 200, ITERS]))
    r = sysm.run()
    e = r.history["entropy"]
    save_csv("exp3_entropy_curve.csv", [{"iteration": i, "entropy": v} for i, v in zip(r.history["iteration"], e)])
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(r.history["iteration"], e, color=SERIES[0])
    ax.set_xlabel("迭代"); ax.set_ylabel("空間熵 E_S")
    ax.set_title(f"圖7 重現：{ITERS} 迭代的空間熵")
    save_fig(fig, "exp3_fig7_entropy.png")
    grids = sysm.snapshots
    fig, axes = plt.subplots(1, len(grids), figsize=(3 * len(grids), 3.2))
    for ax, (k, g) in zip(axes, sorted(grids.items())):
        snapshot_grid(ax, g, f"迭代 {k}")
    save_fig(fig, "exp3_fig6_snapshots.png")
    summ.append(f"- 圖7：E_S 由 {e[0]:.3f} 降至 {e[-1]:.3f}（最低 {min(e):.3f}）")

    # ---- 圖8
    rows8 = []
    for n_ants in (10, 20, 50, 100):
        for s in range(SEEDS):
            rr = AntSortSystem(AntSortConfig(seed=100 + s, n_ants=n_ants, max_iterations=100, log_actions=False)).run()
            rows8.append({"n_ants": n_ants, "seed": s, "entropy_100": rr.history["entropy"][-1]})
    save_csv("exp3_fig8_ants.csv", rows8)
    fig, ax = plt.subplots(figsize=(5, 3.4))
    xs = [10, 20, 50, 100]
    m = [np.mean([r_["entropy_100"] for r_ in rows8 if r_["n_ants"] == n]) for n in xs]
    sd = [np.std([r_["entropy_100"] for r_ in rows8 if r_["n_ants"] == n]) for n in xs]
    ax.errorbar(range(4), m, yerr=sd, color=SERIES[0], marker="o", capsize=3)
    ax.set_xticks(range(4), [str(x) for x in xs]); ax.set_xlabel("螞蟻數"); ax.set_ylabel("100 迭代後 E_S")
    ax.set_title("圖8 重現：螞蟻數與聚類程度")
    save_fig(fig, "exp3_fig8_ants.png")
    summ.append("- 圖8：" + ", ".join(f"{n} 隻→{v:.3f}" for n, v in zip(xs, m)))

    # ---- 表2
    rows2 = []
    for k1, k2 in K_TABLE:
        vals = {c: [] for c in CHECK}
        for s in range(SEEDS):
            rr = AntSortSystem(AntSortConfig(seed=200 + s, k1=k1, k2=k2, max_iterations=max(CHECK), log_actions=False)).run()
            for c in CHECK:
                vals[c].append(rr.history["entropy"][c])
        rows2.append({"k1": k1, "k2": k2, **{f"ES({c})": round(float(np.mean(vals[c])), 3) for c in CHECK}})
        print("k1,k2", k1, k2, "done")
    save_csv("exp3_table2_k1k2.csv", rows2)
    summ += ["", "表2 重現（平均 %d 次）：" % SEEDS, "",
             "| k1 | k2 | " + " | ".join(f"ES({c})" for c in CHECK) + " |",
             "|---|---|" + "---|" * len(CHECK)]
    for r_ in rows2:
        summ.append(f"| {r_['k1']} | {r_['k2']} | " + " | ".join(str(r_[f'ES({c})']) for c in CHECK) + " |")
    write_summary("exp3", summ)


if __name__ == "__main__":
    main()
