"""
主題二（統計加強）：多手問題的量化——配對反事實、多重比較校正、第二種歸因方法
=============================================================================

(1) 配對反事實（SEEDS 個種子；同一種子下比較「完整蟻群」與「移除某些個體」）
    條件：top-1 / bottom-1 / random-1 / top-25% / random-25% / top-50% / random-50%
    → 每個條件：Δ 平均、95% bootstrap CI、Cohen's d_z、Wilcoxon p、Holm 校正
    → 關鍵比較：top-k vs random-k（「貢獻排名」能否預測「因果重要性」？）
(2) 責任分散度的跨種子分布：Gini、N_eff、最大單一占比的 95% CI；
    個體性向（α_k、β_k）與貢獻占比的 Spearman 相關（責任是否追蹤「性格」？）
(3) 第二種歸因：群組 Shapley 值。把螞蟻依來源占比分成四個四分位群組，
    以 v(S) = L_random − L(S) 計算精確 Shapley 值，與來源占比比較；
    並計算協同指數 充分度 = mean_i v({i}) / v(N)（單一群組能否獨力達成結果：過度決定）。
"""
import itertools
import math

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

from common import (QUICK, SERIES, INK2, save_csv, save_fig, write_summary,
                    pmap, bootstrap_ci, holm, paired_stats)
from miat_ants.core.metrics import gini, effective_number
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.tsp import actions as act

N, M = 30, 20
CYCLES = 50 if QUICK else 100
HET = 0.5
SEEDS = 6 if QUICK else 32
SHAPLEY_SEEDS = 3 if QUICK else 10
COORDS = random_cities(N, seed=30)


def _cfg(seed, **kw):
    return AntTSPConfig(n_ants=M, max_cycles=CYCLES, heterogeneity=HET, seed=seed, **kw)


def full_run(seed):
    sysm = AntTSPSystem(COORDS, _cfg(seed))
    r = sysm.run()
    share = r.medium.provenance_share(act.tour_edge_list(r.best_tour))[1:]
    return {"seed": seed, "best": r.best_length, "share": share,
            "alpha": sysm.ant_alpha.copy(), "beta": sysm.ant_beta.copy()}


def removal_run(args):
    seed, removed = args
    r = AntTSPSystem(COORDS, _cfg(seed, disabled_ants=list(removed), track_provenance=False)).run()
    return r.best_length


def coalition_run(args):
    seed, members = args
    disabled = [k for k in range(M) if k not in set(members)]
    r = AntTSPSystem(COORDS, _cfg(seed, disabled_ants=disabled, track_provenance=False)).run()
    return r.best_length


def shapley_exact(players, v):
    """players: 群組名稱清單；v: frozenset -> value。回傳 dict。"""
    n = len(players)
    phi = {p: 0.0 for p in players}
    for p in players:
        others = [q for q in players if q != p]
        for r in range(n):
            for S in itertools.combinations(others, r):
                S = frozenset(S)
                w = math.factorial(len(S)) * math.factorial(n - len(S) - 1) / math.factorial(n)
                phi[p] += w * (v[S | {p}] - v[S])
    return phi


def main():
    summ = ["## 實驗7（主題二・統計加強）：多手問題的量化", "",
            f"設定：{N} 城市、{M} 隻異質螞蟻（h={HET}）、{CYCLES} 週期、{SEEDS} 個種子（配對設計）。", ""]

    # ------------------------------------------------------------ (1)(2) 完整蟻群
    fulls = pmap(full_run, range(SEEDS))
    conds = {}
    jobs = []
    for f in fulls:
        s = f["seed"]
        order = np.argsort(f["share"])[::-1]
        rng = np.random.default_rng(10_000 + s)
        perm = rng.permutation(M)
        c = {"top-1": order[:1], "bottom-1": order[-1:], "random-1": perm[:1],
             "top-25%": order[:M // 4], "random-25%": perm[:M // 4],
             "top-50%": order[:M // 2], "random-50%": perm[:M // 2]}
        for name, rem in c.items():
            jobs.append((name, s, tuple(int(x) for x in rem)))
    lens = pmap(removal_run, [(s, rem) for _, s, rem in jobs])
    for (name, s, rem), L in zip(jobs, lens):
        conds.setdefault(name, {})[s] = L
    base = {f["seed"]: f["best"] for f in fulls}

    rows, names = [], list(conds.keys())
    stats = []
    for name in names:
        d = [conds[name][s] - base[s] for s in range(SEEDS)]
        st = paired_stats(d)
        stats.append(st)
    adj = holm([st["p"] for st in stats])
    summ += ["### (1) 配對反事實：移除後最佳巡迴長度的變化 Δ = L(移除) − L(完整)", "",
             "| 條件 | Δ 平均 | 95% CI | d_z | Wilcoxon p | Holm 校正 p |", "|---|---|---|---|---|---|"]
    for name, st, pa in zip(names, stats, adj):
        rows.append({"condition": name, **st, "p_holm": pa})
        summ.append(f"| {name} | {st['mean']:+.2f} | [{st['ci_lo']:+.2f}, {st['ci_hi']:+.2f}] | "
                    f"{st['d_z']:+.2f} | {st['p']:.3g} | {pa:.3g} |")
    save_csv("exp7_counterfactual_stats.csv", rows)

    # top-k vs random-k
    summ += ["", "關鍵比較：依來源占比移除 vs 隨機移除相同數量（配對）", "",
             "| k | Δ(top) − Δ(random) 平均 | 95% CI | d_z | Wilcoxon p |", "|---|---|---|---|---|"]
    cmp_rows = []
    for k_name in ("1", "25%", "50%"):
        d = [conds[f"top-{k_name}"][s] - conds[f"random-{k_name}"][s] for s in range(SEEDS)]
        st = paired_stats(d)
        cmp_rows.append({"k": k_name, **st})
        summ.append(f"| {k_name} | {st['mean']:+.2f} | [{st['ci_lo']:+.2f}, {st['ci_hi']:+.2f}] | "
                    f"{st['d_z']:+.2f} | {st['p']:.3g} |")
    save_csv("exp7_top_vs_random.csv", cmp_rows)

    # (2) dispersion
    G = [gini(f["share"]) for f in fulls]
    NE = [effective_number(f["share"]) for f in fulls]
    MX = [float(np.max(f["share"])) for f in fulls]
    a_all = np.concatenate([f["alpha"] for f in fulls])
    b_all = np.concatenate([f["beta"] for f in fulls])
    sh_all = np.concatenate([f["share"] for f in fulls])
    ra = spearmanr(a_all, sh_all)
    rb = spearmanr(b_all, sh_all)
    save_csv("exp7_dispersion.csv", [{"seed": f["seed"], "gini": g, "n_eff": ne, "max_share": mx}
                                     for f, g, ne, mx in zip(fulls, G, NE, MX)])
    summ += ["", "### (2) 責任分散度（跨種子）", "",
             f"- Gini = {np.mean(G):.3f}，95% CI {bootstrap_ci(G)[0]:.3f}–{bootstrap_ci(G)[1]:.3f}",
             f"- N_eff = {np.mean(NE):.2f} / {M}，95% CI {bootstrap_ci(NE)[0]:.2f}–{bootstrap_ci(NE)[1]:.2f}",
             f"- 最大單一占比 = {np.mean(MX):.3f}，95% CI {bootstrap_ci(MX)[0]:.3f}–{bootstrap_ci(MX)[1]:.3f}（均分 = {1 / M:.3f}）",
             f"- 個體性向與貢獻占比：Spearman ρ(α, share) = {ra.statistic:+.3f}（p={ra.pvalue:.2g}）；"
             f"ρ(β, share) = {rb.statistic:+.3f}（p={rb.pvalue:.2g}），n={len(sh_all)}", ""]

    # ------------------------------------------------------------ (3) group Shapley
    rand_rng = np.random.default_rng(0)
    D = act.distance_matrix(COORDS)
    L_rand = float(np.mean([act.tour_length(rand_rng.permutation(N), D) for _ in range(2000)]))
    groups = ["Q1(最高)", "Q2", "Q3", "Q4(最低)"]
    sh_rows, cjobs, meta = [], [], []
    for f in fulls[:SHAPLEY_SEEDS]:
        order = np.argsort(f["share"])[::-1]
        members = {g: order[i * (M // 4):(i + 1) * (M // 4)].tolist() for i, g in enumerate(groups)}
        for r in range(1, 5):
            for S in itertools.combinations(groups, r):
                ants = sum((members[g] for g in S), [])
                cjobs.append((f["seed"], tuple(ants)))
                meta.append((f["seed"], frozenset(S)))
        f["members"] = members
    cl = pmap(coalition_run, cjobs)
    vals = {}
    for (s, S), L in zip(meta, cl):
        vals.setdefault(s, {frozenset(): 0.0})[S] = L_rand - L
    prov_g, shap_g, syn = [], [], []
    for f in fulls[:SHAPLEY_SEEDS]:
        s = f["seed"]
        v = vals[s]
        phi = shapley_exact(groups, v)
        vN = v[frozenset(groups)]
        synergy = (vN - sum(v[frozenset([g])] for g in groups)) / vN
        suff = float(np.mean([v[frozenset([g])] / vN for g in groups]))   # 單一群組的充分度
        syn.append(suff)
        for g in groups:
            ps = float(np.sum(f["share"][f["members"][g]]))
            prov_g.append(ps)
            shap_g.append(phi[g] / vN)
            sh_rows.append({"seed": s, "group": g, "provenance_share": ps, "shapley_share": phi[g] / vN,
                            "v_single": v[frozenset([g])], "v_all": vN, "synergy": synergy})
    save_csv("exp7_group_shapley.csv", sh_rows)
    rs = spearmanr(prov_g, shap_g)
    mean_by_g = {g: (np.mean([r["provenance_share"] for r in sh_rows if r["group"] == g]),
                     np.mean([r["shapley_share"] for r in sh_rows if r["group"] == g])) for g in groups}
    summ += ["### (3) 第二種歸因：群組 Shapley 值（%d 個種子）" % SHAPLEY_SEEDS, "",
             f"v(S) = L_random − L(S)，L_random = {L_rand:.1f}（隨機巡迴期望長度）", "",
             "| 群組（依來源占比四分位） | 來源占比 | Shapley 占比 |", "|---|---|---|"]
    for g in groups:
        summ.append(f"| {g} | {mean_by_g[g][0]:.3f} | {mean_by_g[g][1]:.3f} |")
    summ += ["", f"- 兩種歸因的 Spearman ρ = {rs.statistic:+.3f}（p={rs.pvalue:.2g}，n={len(prov_g)}）",
             f"- 單一群組充分度 = mean_g v({{g}}) / v(N) = {np.mean(syn):.4f}，"
             f"95% CI {bootstrap_ci(syn)[0]:.4f}–{bootstrap_ci(syn)[1]:.4f}"
             "（接近 1＝任何四分之一的蟻群單獨即可達成幾乎全部成果：結果被「過度決定」，"
             "沒有任何群組是必要條件）",
             "- 注意：v 以隨機巡迴為基準，因此充分度衡量的是「相對於無秩序」的成果；"
             "最後幾個百分點的品質差異請看 (1) 的配對反事實。", ""]

    # ------------------------------------------------------------ figures
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.9))
    ax = axes[0]
    for i, (name, st) in enumerate(zip(names, stats)):
        color = SERIES[1] if name.startswith("top") else (SERIES[0] if name.startswith("random") else SERIES[2])
        ax.errorbar(st["mean"], i, xerr=[[st["mean"] - st["ci_lo"]], [st["ci_hi"] - st["mean"]]],
                    fmt="o", capsize=3, color=color)
        ax.text(st["ci_hi"], i, f"  p_Holm={adj[i]:.2g}", va="center", fontsize=8, color=INK2)
    ax.axvline(0, color=INK2, lw=1, ls="--")
    ax.set_yticks(range(len(names)), names); ax.invert_yaxis()
    ax.set_xlabel("Δ 最佳巡迴長度（移除 − 完整），95% CI")
    ax.set_title(f"配對反事實（{SEEDS} 個種子）")
    ax = axes[1]
    x = np.arange(len(groups))
    ax.bar(x - 0.18, [mean_by_g[g][0] for g in groups], width=0.34, color=SERIES[0], label="來源占比（provenance）")
    ax.bar(x + 0.18, [mean_by_g[g][1] for g in groups], width=0.34, color=SERIES[1], label="Shapley 占比")
    ax.axhline(0.25, color=INK2, lw=1, ls="--")
    ax.set_xticks(x, groups); ax.set_ylabel("占比")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.set_title(f"兩種歸因的比較（Spearman ρ={rs.statistic:+.2f}）")
    save_fig(fig, "exp7_topic2_stats.png")
    write_summary("exp7", summ)


if __name__ == "__main__":
    main()
