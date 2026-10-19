"""
主題二：多手問題——分散式責任的可操作化
=====================================
(a) 來源歸因（provenance）：最終最佳巡迴上的費洛蒙，各來自哪隻螞蟻？
    → Gini 係數、有效貢獻者數 N_eff（many hands 的量化）
(b) 但書因果（but-for / 反事實）：移除貢獻最大的個體，結果是否改變？
    與「隨機種子造成的自然變異」比較；再比較移除前 25%／50% 貢獻者（集體反事實）。
(c) 分揀系統：最終聚落的「作者」分布（最後放下者）與每個物資被多少隻螞蟻經手。
所有判斷都回溯到事件紀錄（Event contract），並輸出 CSV 供質性分析。
"""
import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, INK2, RESULTS, save_csv, save_fig, write_summary
from miat_ants.core.metrics import gini, effective_number
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.tsp.actions import tour_edge_list
from miat_ants.sorting import AntSortSystem, AntSortConfig
from miat_ants.sorting.actions import neighbor_type_counts, local_density

N, M = 30, 20
CYCLES = 60 if QUICK else 100
SEEDS = 3 if QUICK else 8


HET = 0.5   # 個體異質性（同質時螞蟻可互換，見 fungibility 檢查）


def run(coords, **kw):
    kw.setdefault("heterogeneity", HET)
    return AntTSPSystem(coords, AntTSPConfig(n_ants=M, max_cycles=CYCLES, **kw)).run()


def main():
    coords = random_cities(N, seed=30)
    summ = ["## 實驗5（主題二）：分散式責任", ""]

    # ---------------- (a) provenance
    r = run(coords, seed=0, log_deposits=True)
    share = r.medium.provenance_share(tour_edge_list(r.best_tour))
    env, ants = share[0], share[1:]
    order = np.argsort(ants)[::-1]
    r.events.to_csv(f"{RESULTS}/exp5_tsp_event_log.csv")
    save_csv("exp5a_provenance.csv", [{"ant": int(k), "share": float(ants[k])} for k in range(M)])
    g, neff = gini(ants), effective_number(ants)
    summ += [f"(a) 最佳巡迴 L={r.best_length:.1f}；環境初始量占 {env:.2e}；"
             f"螞蟻貢獻 Gini={g:.3f}、N_eff={neff:.1f}/{M}；最大單一貢獻 {ants.max():.3f}", ""]

    # ---------------- (b) counterfactual
    natural = [run(coords, seed=s, track_provenance=False).best_length for s in range(SEEDS)]
    base_mean, base_sd = np.mean(natural), np.std(natural)
    rows = [{"condition": "full colony", "removed": "", "best_mean": base_mean, "best_sd": base_sd}]
    conds = [("top-1 contributor", [int(order[0])]),
             ("bottom-1 contributor", [int(order[-1])]),
             ("top 25% contributors", [int(k) for k in order[:M // 4]]),
             ("random 25%", [int(k) for k in np.random.default_rng(1).choice(M, M // 4, replace=False)]),
             ("top 50% contributors", [int(k) for k in order[:M // 2]])]
    for lab, rem in conds:
        vals = [run(coords, seed=s, disabled_ants=rem, track_provenance=False).best_length for s in range(SEEDS)]
        rows.append({"condition": lab, "removed": " ".join(map(str, rem)),
                     "best_mean": float(np.mean(vals)), "best_sd": float(np.std(vals))})
        print(lab, "done")
    save_csv("exp5b_counterfactual.csv", rows)
    # 可互換性（fungibility）檢查：同質蟻群、同一種子，移除「哪一隻」是否有差別？
    hom = [run(coords, seed=0, heterogeneity=0.0, disabled_ants=[k], track_provenance=False).best_length
           for k in range(M)]
    summ.append(f"(b0) 同質蟻群可互換性：同一種子下分別移除 {M} 隻中的任一隻，結果種類數 = "
                f"{len(set(np.round(hom, 6)))}（=1 表示個體身分在因果上無關，只有數量有關）")
    summ.append(f"(b) 異質蟻群（h={HET}）反事實（{SEEDS} 個種子）：完整蟻群 {base_mean:.1f} ± {base_sd:.1f}")
    for row in rows[1:]:
        d = row["best_mean"] - base_mean
        summ.append(f"   - 移除 {row['condition']}: {row['best_mean']:.1f} ± {row['best_sd']:.1f}"
                    f"（Δ={d:+.1f}；Δ/自然變異={d / base_sd if base_sd > 0 else float('nan'):+.2f}）")
    summ.append("")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6))
    axes[0].bar(range(M), ants[order], color=SERIES[0], width=0.8)
    axes[0].axhline(1 / M, color=INK2, lw=1, ls="--")
    axes[0].text(M - 0.5, 1 / M, " 均分 1/m", va="bottom", ha="right", color=INK2, fontsize=9)
    axes[0].set_xlabel("螞蟻（依貢獻排序）"); axes[0].set_ylabel("最佳巡迴上費洛蒙占比")
    axes[0].set_title(f"來源歸因：Gini={g:.2f}，N_eff={neff:.1f}")
    labs = [x["condition"] for x in rows]
    axes[0].set_xticks(range(0, M, 5))
    for i, x in enumerate(rows):
        axes[1].errorbar(x["best_mean"], i, xerr=x["best_sd"], fmt="o", capsize=3,
                         color=SERIES[0] if i == 0 else SERIES[1])
    axes[1].axvline(base_mean, color=INK2, lw=1, ls="--")
    axes[1].set_yticks(range(len(rows)), labs); axes[1].invert_yaxis()
    axes[1].set_xlabel("最佳巡迴長度（平均 ± 標準差）"); axes[1].set_title("反事實：移除誰會改變結果？")
    save_fig(fig, "exp5ab_tsp_responsibility.png")

    # ---------------- (c) sorting authorship
    its = 150 if QUICK else 400
    sysm = AntSortSystem(AntSortConfig(seed=3, max_iterations=its, log_actions=True))
    rs = sysm.run()
    rs.events.to_csv(f"{RESULTS}/exp5_sorting_event_log.csv")
    tg, ig = rs.type_grid, rs.id_grid
    cells = np.argwhere(ig >= 0)
    counts = neighbor_type_counts(tg, 2, 1)
    f = local_density(tg[cells[:, 0], cells[:, 1]], cells, counts)
    clustered = ig[cells[:, 0], cells[:, 1]][f >= 0.5]
    authors = sysm.last_dropper[clustered]
    authors = authors[authors >= 0]
    auth_share = np.bincount(authors, minlength=sysm.cfg.n_ants).astype(float)
    auth_share /= max(auth_share.sum(), 1)
    touches = {}
    for e in rs.events.filter("drop"):
        touches.setdefault(e.payload["obj"], set()).add(e.source_module)
    n_hands = np.array([len(touches.get(o, ())) for o in range(200)])
    save_csv("exp5c_sorting_authorship.csv", [{"ant": k, "author_share": float(auth_share[k])}
                                              for k in range(sysm.cfg.n_ants)])
    summ += [f"(c) 分揀 {its} 迭代：聚落中物資 {len(clustered)}/200 個；"
             f"作者 Gini={gini(auth_share):.3f}、N_eff={effective_number(auth_share):.1f}/{sysm.cfg.n_ants}；"
             f"每個物資平均經手 {n_hands.mean():.1f} 隻螞蟻（最多 {n_hands.max()}）；"
             f"事件總數 {len(rs.events)}"]
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.hist(n_hands, bins=np.arange(n_hands.max() + 2) - 0.5, color=SERIES[0], rwidth=0.85)
    ax.set_xlabel("經手（放下過）該物資的螞蟻數"); ax.set_ylabel("物資數")
    ax.set_title("分揀：每個物資的「多手」程度")
    save_fig(fig, "exp5c_sorting_many_hands.png")
    write_summary("exp5", summ)


if __name__ == "__main__":
    main()
