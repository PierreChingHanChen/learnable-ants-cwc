"""
主題三：交織的可逆性——擾動、遺忘與恢復
=====================================
(a) 封路／解封：在第 T1 週期封鎖目前最佳巡迴上的一條邊，T2 週期解封。
    依殘留係數 ρ 比較：恢復時間、被封邊上費洛蒙的半衰期（遺忘）、
    解封後是否回到原路徑（可逆性 vs 遲滯 hysteresis）。
(b) 切斷介質（原論文 4.2.3「溶解集體智能」）與移除半數螞蟻，再恢復。
(c) 分揀：全域打亂後的恢復。
"""
import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, INK2, save_csv, save_fig, write_summary
from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.core.metrics import edge_jaccard, half_life, recovery_time
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.tsp.actions import tour_edge_list
from miat_ants.sorting import AntSortSystem, AntSortConfig

N, M = 30, 30
T1, T2, T_END = (30, 70, 110) if QUICK else (60, 140, 220)
SEEDS = 2 if QUICK else 4
RHOS = (0.3, 0.5, 0.7, 0.9)


def env_event(kind, t, **payload):
    return Event(kind, t, "environment", payload, PRIORITY_ENV, "interrupt")


def main():
    coords = random_cities(N, seed=30)
    summ = ["## 實驗6（主題三）：可逆性", ""]

    # ---------------- (a) block / unblock
    rows, curves, watch = [], {}, {}
    for rho in RHOS:
        for s in range(SEEDS):
            pre = AntTSPSystem(coords, AntTSPConfig(n_ants=M, rho=rho, max_cycles=T1 + 1, seed=s,
                                                    track_provenance=False)).run()
            pre_tour = pre.history["best_tour"][T1]
            e = tour_edge_list(pre_tour)[0]
            ev = [env_event("block_edge", T1, edge=list(e), factor=1000.0),
                  env_event("unblock_edge", T2, edge=list(e))]
            r = AntTSPSystem(coords, AntTSPConfig(n_ants=M, rho=rho, max_cycles=T_END, seed=s,
                                                  perturbations=ev, watch_edges=[e],
                                                  track_provenance=False)).run()
            h = r.history
            assert edge_jaccard(h["best_tour"][T1], pre_tour) == 1.0   # 同種子 → 擾動前完全一致
            cb = np.array(h["cycle_best"])
            target = cb[T1 + 1:T2].min()
            w = np.array([x[0] for x in h["watch"]])
            final_tour = h["best_tour"][-1]
            rows.append({"rho": rho, "seed": s,
                         "pre_len": h["best_so_far"][T1],
                         "recovery_cycles": recovery_time(cb, T1 + 1, target),
                         "blocked_edge_half_life": half_life(w, T1 + 1),
                         "theory_half_life": np.log(0.5) / np.log(rho),
                         "jaccard_final_vs_pre": edge_jaccard(final_tour, pre_tour),
                         "edge_readopted": tuple(sorted(e)) in {tuple(sorted(x)) for x in tour_edge_list(final_tour)},
                         "final_len": h["best_so_far"][-1]})
            curves.setdefault(rho, []).append(cb / h["best_so_far"][T1])
            watch.setdefault(rho, []).append(w)
        print("rho", rho, "done")
    save_csv("exp6a_block_unblock.csv", rows)
    summ += ["(a) 封路於第 %d 週期、解封於第 %d 週期（%d 個種子平均）：" % (T1, T2, SEEDS), "",
             "| ρ | 恢復週期 | 被封邊費洛蒙半衰期（實測／理論 ln½/lnρ） | 解封後與原路徑 Jaccard | 重新採用原邊比例 |",
             "|---|---|---|---|---|"]
    for rho in RHOS:
        R = [x for x in rows if x["rho"] == rho]
        summ.append(f"| {rho} | {np.mean([x['recovery_cycles'] for x in R]):.1f} | "
                    f"{np.nanmean([x['blocked_edge_half_life'] for x in R]):.1f} / {R[0]['theory_half_life']:.2f} | "
                    f"{np.mean([x['jaccard_final_vs_pre'] for x in R]):.3f} | "
                    f"{np.mean([x['edge_readopted'] for x in R]):.2f} |")
    summ.append("")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6))
    for k, rho in enumerate(RHOS):
        axes[0].plot(np.mean(curves[rho], axis=0), color=SERIES[k], label=f"ρ={rho}", lw=1.6)
        axes[1].semilogy(np.mean(watch[rho], axis=0), color=SERIES[k], label=f"ρ={rho}", lw=1.6)
    for ax in axes:
        ax.axvspan(T1, T2, color="#e4e3df", alpha=0.6, lw=0)
        ax.text(T1 + 1, ax.get_ylim()[1], " 封路期間", va="top", color=INK2, fontsize=9)
        ax.set_xlabel("週期"); ax.legend(ncol=2)
    axes[0].set_ylabel("本週期最佳／擾動前最佳"); axes[0].set_title("擾動與恢復")
    axes[1].set_ylabel("被封邊上的費洛蒙（log）"); axes[1].set_title("遺忘：費洛蒙蒸發")
    save_fig(fig, "exp6a_block_unblock.png")

    # ---------------- (b) cut medium / remove ants
    conds = {
        "切斷介質後恢復": [env_event("cut_medium", T1), env_event("restore_medium", T2)],
        "移除半數螞蟻後恢復": [env_event("remove_ants", T1, fraction=0.5), env_event("restore_ants", T2)],
    }
    rows_b, cm = [], {}
    for lab, evs in conds.items():
        arr = []
        for s in range(SEEDS):
            r = AntTSPSystem(coords, AntTSPConfig(n_ants=M, max_cycles=T_END, seed=s, perturbations=evs,
                                                  track_provenance=False)).run()
            h = r.history
            base = np.mean(h["cycle_mean"][T1 - 10:T1 + 1])
            arr.append(np.array(h["cycle_mean"]) / base)
            during = np.mean(h["cycle_mean"][T1 + 2:T2]) / base
            after = np.mean(h["cycle_mean"][T2 + 2:T2 + 12]) / base
            rows_b.append({"condition": lab, "seed": s, "during_ratio": during, "after_ratio": after,
                           "consensus_before": h["consensus"][T1], "consensus_during": h["consensus"][T2 - 1]})
        cm[lab] = np.mean(arr, axis=0)
    save_csv("exp6b_cut_remove.csv", rows_b)
    for lab in conds:
        R = [x for x in rows_b if x["condition"] == lab]
        summ.append(f"(b) {lab}：擾動期間螞蟻平均巡迴長／擾動前 = {np.mean([x['during_ratio'] for x in R]):.3f}，"
                    f"恢復後 10 週期 = {np.mean([x['after_ratio'] for x in R]):.3f}")
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for k, (lab, c) in enumerate(cm.items()):
        ax.plot(c, color=SERIES[k], label=lab, lw=1.6)
    ax.axvspan(T1, T2, color="#e4e3df", alpha=0.6, lw=0)
    ax.set_xlabel("週期"); ax.set_ylabel("螞蟻平均巡迴長／擾動前"); ax.legend()
    ax.set_title("溶解與重組：切斷介質 vs 移除個體")
    save_fig(fig, "exp6b_cut_remove.png")

    # ---------------- (c) sorting scramble
    its = 200 if QUICK else 600
    t_s = its // 2
    es, rows_c = [], []
    for s in range(SEEDS):
        r = AntSortSystem(AntSortConfig(seed=s, max_iterations=its, log_actions=False,
                                        perturbations=[env_event("scramble_all", t_s)])).run()
        e = np.array(r.history["entropy"])
        es.append(e)
        pre = e[t_s - 20:t_s + 1].mean()
        rows_c.append({"seed": s, "pre_entropy": pre, "post_scramble": e[t_s + 1],
                       "recovery_iterations": recovery_time(e, t_s + 1, pre, tol=0.03),
                       "first_descent_iterations": recovery_time(e, 0, pre, tol=0.03)})
    save_csv("exp6c_sorting_scramble.csv", rows_c)
    summ.append(f"(c) 分揀打亂於第 {t_s} 迭代：恢復到擾動前熵所需迭代 "
                f"{np.mean([x['recovery_iterations'] for x in rows_c]):.1f}（初次形成所需 "
                f"{np.mean([x['first_descent_iterations'] for x in rows_c]):.1f}）；-1 表示未恢復")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(np.mean(es, axis=0), color=SERIES[0])
    ax.axvline(t_s, color=INK2, lw=1, ls="--")
    ax.text(t_s, ax.get_ylim()[1], " 全域打亂", va="top", color=INK2, fontsize=9)
    ax.set_xlabel("迭代"); ax.set_ylabel("空間熵 E_S"); ax.set_title("分揀：打亂後的自我修復")
    save_fig(fig, "exp6c_sorting_scramble.png")
    write_summary("exp6", summ)


if __name__ == "__main__":
    main()
