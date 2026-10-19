"""
論文修訂用的統合分析（exp9 20 種子、exp11、exp10b、exp13 20 種子；exp12 的統計由 exp12 腳本自行輸出）
輸出：results/summary_revision.md
等價檢定：等價界在擴充實驗執行前已寫入草稿（私有介質平均分散度的 ±10%）。
  - TOST：兩個單尾配對 t 檢定，p_TOST = max(p_lower, p_upper)
  - 另以 90% bootstrap 信賴區間是否完全落在等價界內作為確認
"""
import os
import numpy as np
import pandas as pd
from scipy import stats

from common import RESULTS, paired_stats, bootstrap_ci, write_summary

R = lambda f: pd.read_csv(os.path.join(RESULTS, f))


def tost(diff, bound):
    d = np.asarray(diff, float)
    lo = stats.ttest_1samp(d, -bound, alternative="greater").pvalue
    hi = stats.ttest_1samp(d, bound, alternative="less").pvalue
    ci90 = bootstrap_ci(d, alpha=0.10)
    return {"mean": d.mean(), "bound": bound, "p_tost": max(lo, hi), "ci90_lo": ci90[0], "ci90_hi": ci90[1],
            "ci_inside": (ci90[0] > -bound) and (ci90[1] < bound)}


def f(st, nd=3):
    return f"{st['mean']:+.{nd}f} [{st['ci_lo']:+.{nd}f}, {st['ci_hi']:+.{nd}f}]（d_z = {st['d_z']:+.2f}，Wilcoxon p = {st['p']:.3g}，n = {st['n']}）"


def ft(t, nd=4):
    return (f"差 = {t['mean']:+.{nd}f}，等價界 ±{t['bound']:.{nd}f}，90% CI [{t['ci90_lo']:+.{nd}f}, {t['ci90_hi']:+.{nd}f}]，"
            f"p_TOST = {t['p_tost']:.3g}，{'落在等價界內' if t['ci_inside'] else '未完全落在等價界內'}")


def main():
    S = ["# 修訂分析摘要", ""]

    # ---------------- exp9（20 種子）
    a = R("exp9a_parity.csv"); b = R("exp9b_stigmergy.csv"); c = R("exp9c_dialect.csv")
    n9 = a.seed.nunique()
    S += [f"## exp9：功能對等與介質（{n9} 個種子）", "", "| 地圖 | 核心 | 送達量 [95% CI] | 相對規則 | 短橋比例 |", "|---|---|---|---|---|"]
    for m in ("open_field", "double_bridge"):
        ref = a[(a["map"] == m) & (a.tag == "rule")].delivered.mean()
        for tag in ("rule", "gpt_bc", "gpt_learn"):
            d = a[(a["map"] == m) & (a.tag == tag)]
            lo, hi = bootstrap_ci(d.delivered)
            S.append(f"| {m} | {tag} | {d.delivered.mean():.0f} [{lo:.0f}, {hi:.0f}] | {d.delivered.mean() / ref:.2f} | "
                     f"{d.short_frac.mean() if m == 'double_bridge' else float('nan'):.3f} |")
    for m in ("open_field", "double_bridge"):
        x = a[(a["map"] == m)].pivot(index="seed", columns="tag", values="delivered")
        S.append(f"- [{m}] 學習 − 規則：{f(paired_stats(x.gpt_learn - x.rule), 1)}；學習 − BC：{f(paired_stats(x.gpt_learn - x.gpt_bc), 1)}")
    S += ["", "| 核心 | 介質 | 送達量 [95% CI] | 短橋比例 |", "|---|---|---|---|"]
    for core in ("gpt", "rule"):
        for med in ("shared", "private", "cut"):
            d = b[b.tag == f"{core}_{med}"]
            lo, hi = bootstrap_ci(d.delivered)
            S.append(f"| {core} | {med} | {d.delivered.mean():.0f} [{lo:.0f}, {hi:.0f}] | {d.short_frac.mean():.3f} |")
    for core in ("gpt", "rule"):
        x = b[b.core == core].pivot(index="seed", columns="tag", values="delivered")
        ratio = x[f"{core}_shared"].mean() / x[f"{core}_private"].mean()
        S.append(f"- [{core}] 共享 − 私有送達量：{f(paired_stats(x[f'{core}_shared'] - x[f'{core}_private']), 1)}；比值 {ratio:.2f}")
    cs = c.pivot(index="seed", columns="medium", values="dispersion")
    cd = c.pivot(index="seed", columns="medium", values="drift")
    bound = 0.10 * cs["private"].mean()
    t1 = tost(cs["shared"] - cs["private"], bound)
    S += ["", "**D1 分散度（主要等價檢定）**", "",
          f"- 分散度：共享 {cs['shared'].mean():.4f}，私有 {cs['private'].mean():.4f}，切斷 {cs['cut'].mean():.4f} nats",
          f"- 共享 − 私有：{f(paired_stats(cs['shared'] - cs['private']), 4)}",
          f"- TOST：{ft(t1)}",
          f"- 漂移：共享 {cd['shared'].mean():.4f}，私有 {cd['private'].mean():.4f}；差 {f(paired_stats(cd['shared'] - cd['private']), 4)}",
          f"- 切斷 − 私有分散度：{f(paired_stats(cs['cut'] - cs['private']), 4)}", ""]

    # ---------------- exp11
    if os.path.exists(os.path.join(RESULTS, "exp11_per_seed.csv")):
        e = R("exp11_per_seed.csv")
        soc = e[e.tag == "social"].set_index("seed").dispersion
        base = cs["shared"].loc[soc.index]
        S += ["## exp11a：社會學習正對照", "",
              f"- 共享介質分散度：無社會學習 {base.mean():.4f}，有社會學習 {soc.mean():.4f} nats（下降 {100 * (1 - soc.mean() / base.mean()):.0f}%）",
              f"- 配對差（社會 − 無社會）：{f(paired_stats(soc - base), 4)}",
              f"- 每個種子都下降：{int((soc < base).sum())}/{len(soc)}"]
        ds = e[e.tag == "social"].set_index("seed").delivered
        db = b[b.tag == "gpt_shared"].set_index("seed").delivered.loc[ds.index]
        S += [f"- 送達量（社會 − 無社會）：{f(paired_stats(ds - db), 1)}", ""]
        g = {t: e[e.tag == t].set_index("seed") for t in e.tag.unique()}
        sh, pr = g["mark05_gpt_shared"], g["mark05_gpt_private"]
        b2 = 0.10 * pr.dispersion.mean()
        t2 = tost(sh.dispersion - pr.dispersion, b2)
        S += ["## exp11b：標記可學習（教師標記機率 0.5）", "",
              f"- GPT 送達量：共享 {sh.delivered.mean():.0f}，私有 {pr.delivered.mean():.0f}；差 {f(paired_stats(sh.delivered - pr.delivered), 1)}；比值 {sh.delivered.mean() / pr.delivered.mean():.2f}",
              f"- 規則（mark_p 0.5）送達量：共享 {g['mark05_rule_shared'].delivered.mean():.0f}，私有 {g['mark05_rule_private'].delivered.mean():.0f}",
              f"- GPT 分散度：共享 {sh.dispersion.mean():.4f}，私有 {pr.dispersion.mean():.4f}；差 {f(paired_stats(sh.dispersion - pr.dispersion), 4)}",
              f"- TOST：{ft(t2)}",
              f"- 攜帶時標記率（共享）：開始 {sh.mark_carry_start.mean():.3f} → 結束 {sh.mark_carry_end.mean():.3f}；變化 {f(paired_stats(sh.mark_carry_end - sh.mark_carry_start))}",
              f"- 攜帶時標記率（私有）：開始 {pr.mark_carry_start.mean():.3f} → 結束 {pr.mark_carry_end.mean():.3f}；變化 {f(paired_stats(pr.mark_carry_end - pr.mark_carry_start))}",
              f"- 結束時標記率 共享 − 私有：{f(paired_stats(sh.mark_carry_end - pr.mark_carry_end))}",
              f"- 規則（mark_p 0.5）標記率：{g['mark05_rule_shared'].mark_carry_end.mean():.3f}", ""]

    # ---------------- exp13（20 種子）
    if os.path.exists(os.path.join(RESULTS, "exp13_per_seed.csv")):
        g13 = R("exp13_per_seed.csv"); gg = g13[g13.core == "gpt"]
        s13 = gg[gg.medium == "shared"].set_index("seed"); p13 = gg[gg.medium == "private"].set_index("seed")
        S += [f"## exp13：控制文法（{gg.seed.nunique()} 個種子）", "",
              f"- 執行合法率：共享 {s13.deploy_legal.mean():.4f} [{bootstrap_ci(s13.deploy_legal)[0]:.4f}, {bootstrap_ci(s13.deploy_legal)[1]:.4f}]，私有 {p13.deploy_legal.mean():.4f} [{bootstrap_ci(p13.deploy_legal)[0]:.4f}, {bootstrap_ci(p13.deploy_legal)[1]:.4f}]",
              f"- 合法質量：共享 {s13.legal_mass.mean():.4f}，私有 {p13.legal_mass.mean():.4f}；共享 − 私有 {f(paired_stats(s13.legal_mass - p13.legal_mass), 4)}",
              f"- 文法內分散度 / 總分散度：共享 {np.mean(s13.disp_within / s13.disp):.2f}，私有 {np.mean(p13.disp_within / p13.disp):.2f}", ""]

    # ---------------- exp10b（驗證性重做，新種子）
    if os.path.exists(os.path.join(RESULTS, "exp10b_shapley_gpt.csv")):
        S += ["## exp10b：D2 驗證性重做（種子 1000 起）", ""]
        slopes = {}
        for core in ("gpt", "rule"):
            d = R(f"exp10b_shapley_{core}.csv")
            d["sh"] = d.groupby("seed").phi.transform(lambda x: x / x.sum())
            d["q"] = d.groupby("seed").cumcount()
            q1 = d[d.q == 0]; q4 = d[d.q == 3]
            sa = d.groupby("seed").superadd.first()
            w1 = stats.wilcoxon(q1.trace_share - q1.sh, alternative="greater").pvalue
            w4 = stats.wilcoxon(q4.trace_share - q4.sh, alternative="less").pvalue
            ws = stats.wilcoxon(sa - 1, alternative="greater").pvalue
            S += [f"### {core}（{d.seed.nunique()} 個 Shapley 種子）",
                  f"- Q1：痕跡 {q1.trace_share.mean():.3f}，Shapley {q1.sh.mean():.3f}；差 {f(paired_stats(q1.trace_share - q1.sh))}；單尾 p = {w1:.3g}",
                  f"- Q4：痕跡 {q4.trace_share.mean():.3f}，Shapley {q4.sh.mean():.3f}；差 {f(paired_stats(q4.trace_share - q4.sh))}；單尾 p = {w4:.3g}",
                  f"- 超加成性：{sa.mean():.3f} [{bootstrap_ci(sa)[0]:.3f}, {bootstrap_ci(sa)[1]:.3f}]；單尾 p（> 1）= {ws:.3g}",
                  f"- ρ(痕跡, Shapley) = {stats.spearmanr(d.trace_share, d.sh).statistic:+.3f}；ρ(直接產出, Shapley) = {stats.spearmanr(d.direct_share, d.sh).statistic:+.3f}"]
            sl = {}
            for sd, gdf in d.groupby("seed"):
                sl[sd] = (np.polyfit(gdf.direct_share, gdf.sh, 1)[0], np.polyfit(gdf.trace_share, gdf.sh, 1)[0])
            slopes[core] = pd.DataFrame(sl, index=["b_direct", "b_trace"]).T
            S.append("")
        common = slopes["gpt"].index.intersection(slopes["rule"].index)
        gd, rd = slopes["gpt"].loc[common], slopes["rule"].loc[common]
        rel = (gd.b_direct - gd.b_trace) - (rd.b_direct - rd.b_trace)
        S += ["### 預先指定檢定：學習是否把貢獻移向直接產出",
              f"- 每個種子內，Shapley 占比對「直接產出占比」與「痕跡占比」的斜率差（直接 − 痕跡）：GPT {np.mean(gd.b_direct - gd.b_trace):+.3f}，規則 {np.mean(rd.b_direct - rd.b_trace):+.3f}",
              f"- 差異（GPT − 規則，同種子配對）：{f(paired_stats(rel))}；單尾 p（GPT > 規則）= {stats.wilcoxon(rel, alternative='greater').pvalue:.3g}", ""]
        cf = R("exp10b_top_vs_random.csv")
        S += ["### 依痕跡移除 vs 隨機移除（間接效果）"]
        for _, r in cf[cf.outcome == "d_indirect"].iterrows():
            S.append(f"- [{r.core}] k = {r.k}：{r['mean']:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]，p = {r.p:.3g}")
        st = R("exp10b_counterfactual_stats.csv")
        S += ["", "### 單隻移除的總效果（GPT）"]
        for _, r in st[(st.core == "gpt") & (st.outcome == "d_total") & st.condition.str.endswith("-1")].iterrows():
            S.append(f"- {r.condition}：{r['mean']:+.1f} [{r.ci_lo:+.1f}, {r.ci_hi:+.1f}]")
        nz = R("exp10b_noise.csv")
        S += [f"- 自然變異 |Δ_total| 平均（GPT）= {nz[nz.core == 'gpt'].d_total.abs().mean():.1f}", ""]
    write_summary("revision", S)


if __name__ == "__main__":
    main()
