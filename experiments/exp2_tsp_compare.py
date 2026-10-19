"""
重現原論文 表1：42 城市 TSP，螞蟻演算法 vs 模擬退火 vs 遺傳演算法，各執行 10 次。
注意：原論文 42 城市座標已不可得，改用固定亂數種子之 42 城市（可替換為 TSPLIB dantzig42）。
"""
import time

import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, save_csv, save_fig, write_summary
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.tsp.baselines import simulated_annealing, genetic_algorithm

RUNS = 3 if QUICK else 10
CYCLES = 60 if QUICK else 150


def main():
    coords = random_cities(42, seed=42)
    rows, best_tours = [], {}
    for run in range(RUNS):
        t = time.time()
        r = AntTSPSystem(coords, AntTSPConfig(n_ants=42, max_cycles=CYCLES, seed=run,
                                              track_provenance=False)).run()
        rows.append({"method": "ACO", "run": run, "best": r.best_length, "sec": time.time() - t})
        best_tours.setdefault("ACO", (r.best_length, r.best_tour))
        if r.best_length < best_tours["ACO"][0]:
            best_tours["ACO"] = (r.best_length, r.best_tour)
        # 讓 SA／GA 的評估次數與 ACO 相近：m × cycles 個完整巡迴 ≈ 42×150 = 6300 巡迴
        t = time.time()
        _, L = simulated_annealing(coords, n_evals=(50_000 if QUICK else 250_000), seed=run)
        rows.append({"method": "SA", "run": run, "best": L, "sec": time.time() - t})
        t = time.time()
        _, L = genetic_algorithm(coords, pop=100, generations=(300 if QUICK else 1500), seed=run)
        rows.append({"method": "GA", "run": run, "best": L, "sec": time.time() - t})
        print("run", run, "done")
    save_csv("exp2_tsp_compare.csv", rows)

    summ = ["## 實驗2：42 城市 TSP 三種演算法比較（表1 重現）", "",
            f"各執行 {RUNS} 次。", "",
            "| 方法 | 最佳解 | 平均最佳解 | 標準差 | 平均秒數 |", "|---|---|---|---|---|"]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    for k, m in enumerate(["ACO", "SA", "GA"]):
        v = np.array([r["best"] for r in rows if r["method"] == m])
        sec = np.mean([r["sec"] for r in rows if r["method"] == m])
        summ.append(f"| {m} | {v.min():.1f} | {v.mean():.1f} | {v.std():.1f} | {sec:.1f} |")
        ax.scatter(np.full(len(v), k) + np.linspace(-0.12, 0.12, len(v)), v, color=SERIES[k], s=36, zorder=3)
        ax.hlines(v.mean(), k - 0.25, k + 0.25, color=SERIES[k], lw=2)
    ax.set_xticks([0, 1, 2], ["螞蟻演算法", "模擬退火", "遺傳演算法"])
    ax.set_ylabel("巡迴長度（愈低愈好）")
    ax.set_title(f"表1 重現：42 城市，各 {RUNS} 次（橫線＝平均）")
    save_fig(fig, "exp2_tsp_compare.png")

    L, tour = best_tours["ACO"]
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    t = list(tour) + [tour[0]]
    ax.plot(coords[t, 0], coords[t, 1], color=SERIES[0], lw=1.6)
    ax.scatter(coords[:, 0], coords[:, 1], color="#0b0b0b", s=14, zorder=3)
    ax.set_aspect("equal")
    ax.set_title(f"圖4(b) 重現：ACO 最佳巡迴 L={L:.1f}")
    save_fig(fig, "exp2_aco_best_tour.png")
    write_summary("exp2", summ)


if __name__ == "__main__":
    main()
