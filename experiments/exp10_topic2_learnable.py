"""
實驗10（主題二・可學習螞蟻）：痕跡不等於原因？——microGPT 螞蟻在雙橋上的多手問題
================================================================================
問題：在可學習螞蟻群體中，「在介質中留下最多痕跡的個體」是否就是「因果上最重要的個體」？

設計（分岔式配對反事實；每個種子一段共同歷史）
  1. 暖機：30 隻 GPT 螞蟻（個別權重、線上自我模仿）在雙橋上執行 T_WARM 步，開啟來源追蹤。
     每隻螞蟻因為自己的歷史而分化（權重、位置、攜帶狀態皆不同）——不再是可互換的個體。
  2. 痕跡（trace share）：暖機後半段（T_WARM/2 → T_WARM），各螞蟻在「可被感知的路徑」
     （τ ≥ 門檻）上的費洛蒙來源占比，取時間平均。這是「紀錄／日誌」所能看到的責任。
  3. 分岔：在第 T_WARM 步把系統複製成多個分支，所有分支以同一個重設種子繼續 T_TEST 步：
       full（完整）、full′（另一個重設種子：自然變異的雜訊底線）、
       top-1 / bottom-1 / random-1 / top-25% / random-25% / top-50% / random-50%（依痕跡排名移除）
  4. 結果（測試窗內）：
       Δ_total    = 送達量(移除) − 送達量(完整)
       Δ_indirect = 倖存者平均每隻送達量的變化（同一批螞蟻在兩個分支中的差）
                    → 被移除者透過介質對「他者」的因果貢獻；排除了被移除者自己的直接產出。
     關鍵比較：Δ(top-k) − Δ(random-k)。若痕跡＝原因，依痕跡移除應比隨機移除傷害更大（更負）。
  5. 群組 Shapley 值（SHAPLEY_SEEDS 個種子）：依痕跡占比把螞蟻分成四個四分位群組，
     v(S) = 只保留群組 S 時測試窗的送達量（v(∅)=0），16 個聯盟全部執行，計算精確 Shapley 值，
     與「痕跡占比」及「直接產出占比」比較；並計算超加成性 v(N) / Σ_g v({g})。
  對照：規則螞蟻以完全相同的流程執行（無學習；個體差異只來自位置與狀態）。
"""
import itertools
import math

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

from common import (QUICK, SERIES, INK2, save_csv, save_fig, write_summary,
                    pmap, bootstrap_ci, holm, paired_stats)
from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.foraging import ForagingSystem, ForagingConfig

M = 30
T_WARM, T_TEST = (600, 400) if QUICK else (2000, 1000)
import os
SEEDS = 2 if QUICK else int(os.environ.get("EXP10_SEEDS", "20"))
SHAPLEY_SEEDS = 1 if QUICK else int(os.environ.get("EXP10_SHAPLEY", "8"))
SEED0 = int(os.environ.get("EXP10_SEED0", "0"))
TAG = os.environ.get("EXP10_TAG", "")
CORES = ("gpt", "rule")
CONDS = ["top-1", "bottom-1", "random-1", "top-25%", "random-25%", "top-50%", "random-50%"]
GROUPS = ["Q1(痕跡最多)", "Q2", "Q3", "Q4(痕跡最少)"]
CORE_LABEL = {"gpt": "GPT 螞蟻（學習）", "rule": "規則螞蟻"}


def ev(kind, **p):
    return Event(kind, T_WARM, "experiment", p, PRIORITY_ENV, "interrupt")


def window_outcome(res, h_warm_idx):
    """測試窗內的結果：總送達量、每隻螞蟻送達量、短橋比例。"""
    h = res.history
    db = np.array(h["delivered_by"])
    per_ant = db[-1] - db[h_warm_idx]
    gs = h["gate_short"][-1] - h["gate_short"][h_warm_idx]
    gl = h["gate_long"][-1] - h["gate_long"][h_warm_idx]
    return {"total": int(per_ant.sum()), "per_ant": per_ant, "short_frac": gs / max(1, gs + gl)}


def run_seed(args):
    core, seed, do_shapley = args
    cfg = ForagingConfig(map_name="double_bridge", n_ants=M, core=core, learn=True, seed=seed,
                         max_steps=T_WARM + T_TEST, track_provenance=True)
    base = ForagingSystem(cfg).run_until(T_WARM)
    h = base.hist
    steps = np.array(h["step"])
    iw = int(np.flatnonzero(steps == T_WARM)[0])                       # 暖機結束的 epoch 索引
    win = (steps > T_WARM // 2) & (steps <= T_WARM)
    ct = np.array(h["contrib_trail"])[win]                               # (epochs, A)
    trace = (ct / np.maximum(ct.sum(1, keepdims=True), 1e-12)).mean(0)   # 時間平均占比
    db = np.array(h["delivered_by"])
    direct_warm = db[iw] - db[int(np.flatnonzero(steps == T_WARM // 2)[0])]   # 暖機後半段的直接產出

    reseed = 1_000_003 * (seed + 1)
    branch = lambda extra=(), rs=reseed: window_outcome(
        base.fork(events_now=[ev("reseed", seed=rs), *extra]).resume(), iw)

    full = branch()
    full2 = branch(rs=reseed + 1)
    order = np.argsort(trace)[::-1]
    perm = np.random.default_rng(77_000 + seed).permutation(M)
    sets = {"top-1": order[:1], "bottom-1": order[-1:], "random-1": perm[:1],
            "top-25%": order[:M // 4], "random-25%": perm[:M // 4],
            "top-50%": order[:M // 2], "random-50%": perm[:M // 2]}
    out = {"core": core, "seed": seed, "trace": trace, "direct_warm": direct_warm,
           "full": full, "noise": {}, "cond": {}}

    def effects(o, removed):
        surv = np.setdiff1d(np.arange(M), removed)
        return {"d_total": o["total"] - full["total"],
                "d_indirect": float((o["per_ant"][surv] - full["per_ant"][surv]).mean()),
                "additive_expect": -int(full["per_ant"][removed].sum()),
                "removed_trace": float(trace[removed].sum()),
                "removed_direct": float(full["per_ant"][removed].sum() / max(1, full["total"])),
                "d_short": o["short_frac"] - full["short_frac"]}

    out["noise"] = effects(full2, np.array([], int))
    for name, rem in sets.items():
        out["cond"][name] = effects(branch([ev("remove_ants", ids=rem.tolist())]), rem)

    if do_shapley:
        groups = np.array_split(order, 4)
        v = {frozenset(): 0.0, frozenset(range(4)): float(full["total"])}
        for r in (1, 2, 3):
            for S in itertools.combinations(range(4), r):
                keep = np.concatenate([groups[g] for g in S])
                rem = np.setdiff1d(np.arange(M), keep)
                v[frozenset(S)] = float(branch([ev("remove_ants", ids=rem.tolist())])["total"])
        phi = shapley_exact(list(range(4)), v)
        out["shapley"] = {
            "phi": [phi[g] for g in range(4)],
            "trace_share": [float(trace[groups[g]].sum()) for g in range(4)],
            "direct_share": [float(full["per_ant"][groups[g]].sum() / max(1, full["total"])) for g in range(4)],
            "size": [len(groups[g]) for g in range(4)],
            "superadd": v[frozenset(range(4))] / max(1e-9, sum(v[frozenset([g])] for g in range(4))),
        }
    return out


def shapley_exact(players, v):
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


def fmt(st, nd=2):
    return (f"{st['mean']:+.{nd}f} | [{st['ci_lo']:+.{nd}f}, {st['ci_hi']:+.{nd}f}] | "
            f"{st['d_z']:+.2f} | {st['p']:.3g}")


def main():
    jobs = [(c, s, s - SEED0 < SHAPLEY_SEEDS) for c in CORES for s in range(SEED0, SEED0 + SEEDS)]
    jobs.sort(key=lambda j: (not j[2], j[0] != "gpt"))          # 最耗時的先排，平行效率較好
    res = pmap(run_seed, jobs)
    by = {c: sorted([r for r in res if r["core"] == c], key=lambda r: r["seed"]) for c in CORES}

    summ = [f"## 實驗10{TAG}（主題二・可學習螞蟻）：痕跡不等於原因？", "",
            f"設定：雙橋、{M} 隻螞蟻；暖機 {T_WARM} 步（線上學習、來源追蹤）後分岔，測試窗 {T_TEST} 步；"
            f"{SEEDS} 個種子（配對）；群組 Shapley {SHAPLEY_SEEDS} 個種子。",
            "痕跡占比 = 暖機後半段在可感知路徑（τ ≥ 門檻）上的費洛蒙來源占比（時間平均）。",
            "Δ_indirect = 倖存者平均每隻送達量的變化（被移除者透過介質對他者的因果貢獻）。", ""]
    rows, cmp_rows, fig_data = [], [], {}

    for core in CORES:
        R = by[core]
        lab = CORE_LABEL[core]
        tr_all = np.concatenate([r["trace"] for r in R])
        dw_all = np.concatenate([r["direct_warm"] for r in R])
        from miat_ants.core.metrics import gini, effective_number
        G = [gini(r["trace"]) for r in R]
        NE = [effective_number(r["trace"]) for r in R]
        rho_td = spearmanr(tr_all, dw_all)
        noise_tot = [r["noise"]["d_total"] for r in R]
        noise_ind = [r["noise"]["d_indirect"] for r in R]
        summ += [f"### {lab}", "",
                 f"- 痕跡分散度：Gini = {np.mean(G):.3f}（95% CI {bootstrap_ci(G)[0]:.3f}–{bootstrap_ci(G)[1]:.3f}）；"
                 f"N_eff = {np.mean(NE):.1f} / {M}",
                 f"- 痕跡占比 vs 暖機期直接產出：Spearman ρ = {rho_td.statistic:+.3f}（p={rho_td.pvalue:.2g}，n={len(tr_all)}）",
                 f"- 完整蟻群測試窗送達量 = {np.mean([r['full']['total'] for r in R]):.1f}；"
                 f"自然變異（重設種子）|Δ_total| 平均 = {np.mean(np.abs(noise_tot)):.1f}，"
                 f"|Δ_indirect| 平均 = {np.mean(np.abs(noise_ind)):.3f}", ""]

        for outcome, title, nd in (("d_indirect", "Δ_indirect（倖存者每隻送達量的變化）", 3),
                                   ("d_total", "Δ_total（總送達量的變化）", 1)):
            stats = [paired_stats([r["cond"][c][outcome] for r in R]) for c in CONDS]
            adj = holm([s["p"] for s in stats])
            summ += [f"**{title}**", "", "| 條件 | 移除者痕跡占比 | 加成預期 Δ | Δ 平均 | 95% CI | d_z | Wilcoxon p | Holm p |",
                     "|---|---|---|---|---|---|---|---|"]
            for c, st, pa in zip(CONDS, stats, adj):
                rt = np.mean([r["cond"][c]["removed_trace"] for r in R])
                ae = np.mean([r["cond"][c]["additive_expect"] for r in R])
                summ.append(f"| {c} | {rt:.3f} | {ae:+.1f} | {fmt(st, nd)} | {pa:.3g} |")
                rows.append({"core": core, "outcome": outcome, "condition": c, **st, "p_holm": pa,
                             "removed_trace": rt, "additive_expect": ae})
            summ.append("")
            fig_data[(core, outcome)] = stats

        summ += ["**關鍵比較：依痕跡移除 vs 隨機移除相同數量（配對；負值 = 依痕跡移除傷害更大）**", "",
                 "| k | 指標 | Δ(top) − Δ(random) | 95% CI | d_z | Wilcoxon p |", "|---|---|---|---|---|---|"]
        for k in ("1", "25%", "50%"):
            for outcome, nd in (("d_indirect", 3), ("d_total", 1)):
                d = [r["cond"][f"top-{k}"][outcome] - r["cond"][f"random-{k}"][outcome] for r in R]
                st = paired_stats(d)
                cmp_rows.append({"core": core, "k": k, "outcome": outcome, **st})
                summ.append(f"| {k} | {outcome} | {fmt(st, nd)} |")
                fig_data[(core, "cmp", k, outcome)] = st
        summ.append("")

        SR = [r for r in R if "shapley" in r]
        if SR:
            phi = np.array([r["shapley"]["phi"] for r in SR])
            phi_sh = phi / phi.sum(1, keepdims=True)
            ts = np.array([r["shapley"]["trace_share"] for r in SR])
            ds = np.array([r["shapley"]["direct_share"] for r in SR])
            sa = [r["shapley"]["superadd"] for r in SR]
            r1 = spearmanr(ts.ravel(), phi_sh.ravel())
            r2 = spearmanr(ds.ravel(), phi_sh.ravel())
            summ += ["**群組 Shapley 值**（v(S) = 只保留群組 S 時的測試窗送達量）", "",
                     "| 群組 | 痕跡占比 | 直接產出占比 | Shapley 占比 |", "|---|---|---|---|"]
            for g in range(4):
                summ.append(f"| {GROUPS[g]} | {ts[:, g].mean():.3f} | {ds[:, g].mean():.3f} | {phi_sh[:, g].mean():.3f} |")
            summ += ["",
                     f"- 痕跡占比 vs Shapley 占比：Spearman ρ = {r1.statistic:+.3f}（p={r1.pvalue:.2g}，n={phi_sh.size}）",
                     f"- 直接產出占比 vs Shapley 占比：Spearman ρ = {r2.statistic:+.3f}（p={r2.pvalue:.2g}）",
                     f"- 超加成性 v(N)/Σ v({{g}}) = {np.mean(sa):.3f}（95% CI {bootstrap_ci(sa)[0]:.3f}–{bootstrap_ci(sa)[1]:.3f}；"
                     f">1 表示合在一起比各自單獨的總和更多：介質中的協同）", ""]
            fig_data[(core, "shapley")] = (ts, phi_sh)
            save_csv(f"exp10{TAG}_shapley_{core}.csv",
                     [{"seed": r["seed"], "group": GROUPS[g], "trace_share": r["shapley"]["trace_share"][g],
                       "direct_share": r["shapley"]["direct_share"][g], "phi": r["shapley"]["phi"][g],
                       "superadd": r["shapley"]["superadd"]} for r in SR for g in range(4)])

    save_csv(f"exp10{TAG}_counterfactual_stats.csv", rows)
    save_csv(f"exp10{TAG}_top_vs_random.csv", cmp_rows)
    save_csv(f"exp10{TAG}_noise.csv", [{"core": r["core"], "seed": r["seed"], **r["noise"]} for r in res])
    save_csv(f"exp10{TAG}_per_seed.csv", [{"core": r["core"], "seed": r["seed"], "condition": c, **r["cond"][c]}
                                    for r in res for c in CONDS])

    # ------------------------------------------------------------------ 圖
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.0), gridspec_kw={"width_ratios": [1.5, 1, 1]})
    ax = axes[0]
    y = np.arange(len(CONDS))
    for i, core in enumerate(CORES):
        st = fig_data[(core, "d_indirect")]
        m = np.array([s["mean"] for s in st]); lo = np.array([s["ci_lo"] for s in st]); hi = np.array([s["ci_hi"] for s in st])
        ax.errorbar(m, y + (i - 0.5) * 0.25, xerr=[m - lo, hi - m], fmt="o", color=SERIES[i], capsize=3,
                    label=CORE_LABEL[core])
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y, CONDS); ax.invert_yaxis()
    ax.set_xlabel("Δ_indirect：倖存者每隻送達量的變化")
    ax.set_title("移除誰，會傷害到其他螞蟻？")

    ax = axes[1]
    ks = ["1", "25%", "50%"]
    for i, core in enumerate(CORES):
        st = [fig_data[(core, "cmp", k, "d_indirect")] for k in ks]
        m = np.array([s["mean"] for s in st]); lo = np.array([s["ci_lo"] for s in st]); hi = np.array([s["ci_hi"] for s in st])
        x = np.arange(3) + (i - 0.5) * 0.2
        ax.errorbar(x, m, yerr=[m - lo, hi - m], fmt="o", color=SERIES[i], capsize=3, label=CORE_LABEL[core])
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks(range(3), [f"k = {k}" for k in ks])
    ax.set_ylabel("Δ(依痕跡) − Δ(隨機)")
    ax.set_title("痕跡排名能預測因果傷害嗎？\n（< 0：依痕跡移除傷害更大）")
    ax.legend(loc="upper left", fontsize=9)

    ax = axes[2]
    for i, core in enumerate(CORES):
        if (core, "shapley") in fig_data:
            ts, ps = fig_data[(core, "shapley")]
            ax.scatter(ts.ravel(), ps.ravel(), s=22, color=SERIES[i], alpha=0.8, label=CORE_LABEL[core])
    lim = [0, max(0.5, ax.get_xlim()[1], ax.get_ylim()[1])]
    ax.plot(lim, lim, color=INK2, lw=0.8, ls="--")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("群組痕跡占比"); ax.set_ylabel("群組 Shapley 占比")
    ax.set_title("痕跡 vs 因果貢獻（四分位群組）")
    fig.tight_layout()
    save_fig(fig, f"exp10{TAG}_trace_vs_cause.png")
    write_summary(f"exp10{TAG}", summ)


if __name__ == "__main__":
    main()
