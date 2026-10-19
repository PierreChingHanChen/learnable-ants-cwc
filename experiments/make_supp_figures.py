"""
Supplementary figures of the paper (figs. S1-S6), same style as make_figures.py.
Output: figures/paper/FigS1.pdf ... FigS6.pdf (+ PNG)
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from make_figures import (W, CM, BLUE, ORANGE, AQUA, INK2, MUTED, RULE, GPT, RUL,  # noqa: E402
                          label, dots, save, reset_rng)
from common import RESULTS, bootstrap_ci  # noqa: E402

R = lambda f: os.path.join(RESULTS, f)  # noqa: E731
GREY = "#8a8984"


def mean_ci(v):
    v = np.asarray(v, float)
    lo, hi = bootstrap_ci(v)
    return v.mean(), lo, hi


# ---------------------------------------------------------------- fig. S1
def figS1():
    """Ant System on the 30-city instance: parameter sweeps (platform validation)."""
    reset_rng()
    d = pd.read_csv(R("exp1_tsp_params.csv"))
    d = d[d.instance == "random30"]
    specs = [("n_ants", "Number of ants, m", True), ("rho", "Retention coefficient, ρ", False),
             ("alpha", "Trail weight, α", False), ("beta", "Heuristic weight, β", False),
             ("Q", "Deposit constant, Q", True)]
    fig, axs = plt.subplots(1, 5, figsize=(W, 4.6 * CM))
    for ax, (p, xl, logx), L in zip(axs, specs, "ABCDE"):
        s = d[d.param == p]
        xs = sorted(s.value.unique())
        m = [mean_ci(s[s.value == x].gap_pct) for x in xs]
        mu = np.array([a[0] for a in m])
        ax.errorbar(xs, mu, yerr=[mu - [a[1] for a in m], [a[2] for a in m] - mu], fmt="o-", color=BLUE,
                    ms=3, lw=0.9, elinewidth=0.8, capsize=0)
        for x in xs:
            v = s[s.value == x].gap_pct.values
            ax.scatter(np.full(len(v), x), v, s=5, color=BLUE, alpha=0.35, lw=0)
        if logx:
            ax.set_xscale("log")
            ax.set_xticks(xs)
            ax.xaxis.set_minor_formatter(plt.NullFormatter())
            ax.minorticks_off()
            ax.set_xticklabels([f"{x:g}" if x < 1000 else f"$10^{{{int(np.log10(x))}}}$" for x in xs])
        if p == "beta":
            ax.set_yscale("symlog", linthresh=1)
        ax.set_xlabel(xl)
        if L == "A":
            ax.set_ylabel("Gap to reference optimum (%)")
        label(ax, L, dx=-0.12)
    fig.tight_layout(w_pad=0.8)
    save(fig, "FigS1")


# ---------------------------------------------------------------- fig. S2
def figS2():
    """Ant sorting: spatial entropy over time and with colony size."""
    reset_rng()
    e = pd.read_csv(R("exp3_entropy_curve.csv"))
    a = pd.read_csv(R("exp3_fig8_ants.csv"))
    fig, axs = plt.subplots(1, 2, figsize=(12 * CM, 4.8 * CM))
    ax = axs[0]
    ax.plot(e.iteration, e.entropy, color=BLUE, lw=0.9)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Spatial entropy, $E_S$")
    label(ax, "A", dx=-0.16)
    ax = axs[1]
    for i, n in enumerate(sorted(a.n_ants.unique())):
        dots(ax, i, a[a.n_ants == n].entropy_100, BLUE)
    ax.set_xticks(range(a.n_ants.nunique()))
    ax.set_xticklabels(sorted(a.n_ants.unique()))
    ax.set_xlabel("Number of ants")
    ax.set_ylabel("$E_S$ after 100 iterations")
    label(ax, "B", dx=-0.16)
    fig.tight_layout(w_pad=1.5)
    save(fig, "FigS2")


# ---------------------------------------------------------------- fig. S3
def figS3():
    """Learnable-marking control (exp11b)."""
    reset_rng()
    d = pd.read_csv(R("exp11_per_seed.csv"))
    g = lambda t: d[d.tag == t].sort_values("seed")  # noqa: E731
    gs, gp, rs, rp = g("mark05_gpt_shared"), g("mark05_gpt_private"), g("mark05_rule_shared"), g("mark05_rule_private")
    fig, axs = plt.subplots(1, 3, figsize=(W, 5.0 * CM))
    ax = axs[0]
    for x, t, c in [(0, gs, GPT), (1, gp, GPT), (2.4, rs, RUL), (3.4, rp, RUL)]:
        dots(ax, x, t.delivered, c)
    ax.set_xticks([0, 1, 2.4, 3.4])
    ax.set_xticklabels(["Shared", "Private", "Shared", "Private"])
    ax.set_ylabel("Food delivered (3,000 steps)")
    ax.text(0.5, 1.0, "Learnable", color=GPT, ha="center", transform=ax.get_xaxis_transform(), fontsize=6.5)
    ax.text(2.9, 1.0, "Rule-based", color=RUL, ha="center", transform=ax.get_xaxis_transform(), fontsize=6.5)
    label(ax, "A", dx=-0.17)
    ax = axs[1]
    for a_, b_ in zip(gs.dispersion.values, gp.dispersion.values):
        ax.plot([0, 1], [a_, b_], color=RULE, lw=0.6, zorder=1)
    dots(ax, 0, gs.dispersion, GPT, jitter=0)
    dots(ax, 1, gp.dispersion, GPT, jitter=0)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Shared", "Private"])
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("Between-ant dispersion (nats)")
    label(ax, "B", dx=-0.2)
    ax = axs[2]
    for x, t in [(0, gs), (1.3, gp)]:
        dots(ax, x - 0.22, t.mark_carry_start, MUTED)
        dots(ax, x + 0.22, t.mark_carry_end, GPT)
    ax.axhline(0.5, color=RUL, lw=0.7, ls="--")
    ax.set_xticks([0, 1.3])
    ax.set_xticklabels(["Shared", "Private"])
    ax.set_ylabel("Marked fraction of loaded moves")
    ax.text(0.98, 0.04, "grey: first 200 steps\nblue: last 500 steps", transform=ax.transAxes, ha="right",
            va="bottom", fontsize=6, color=INK2)
    label(ax, "C", dx=-0.2)
    fig.tight_layout(w_pad=1.2)
    save(fig, "FigS3")


# ---------------------------------------------------------------- fig. S4
def slope_diff(df):
    out = {}
    for s, g in df.groupby("seed"):
        sh = g.phi / g.phi.sum()
        bd = np.polyfit(g.direct_share, sh, 1)[0]
        bt = np.polyfit(g.trace_share, sh, 1)[0]
        out[s] = bd - bt
    return pd.Series(out)


def figS4():
    """Confirmatory replication of D2 (exp10b, seeds 1000-1019; Shapley on 12)."""
    reset_rng()
    G = pd.read_csv(R("exp10b_shapley_gpt.csv"))
    Rr = pd.read_csv(R("exp10b_shapley_rule.csv"))
    for df in (G, Rr):
        df["q"] = df.groupby("seed").cumcount()
        df["sh"] = df.phi / df.groupby("seed").phi.transform("sum")
    fig, axs = plt.subplots(1, 4, figsize=(W, 4.9 * CM))
    ax = axs[0]
    for df, c in [(G, GPT), (Rr, RUL)]:
        ax.scatter(df.trace_share, df.sh, s=5, color=c, alpha=0.35, lw=0)
        m = df.groupby("q")[["trace_share", "sh"]].mean()
        ax.plot(m.trace_share, m.sh, "o-", color=c, ms=3, lw=0.9)
    ax.plot([0.05, 0.5], [0.05, 0.5], ls="--", color=MUTED, lw=0.7)
    ax.set_xlabel("Trace share")
    ax.set_ylabel("Shapley share")
    label(ax, "A", dx=-0.2)
    ax = axs[1]
    for k, (df, c, off) in enumerate([(G, GPT, -0.18), (Rr, RUL, 0.18)]):
        for q in range(4):
            dots(ax, q + off, (df[df.q == q].trace_share - df[df.q == q].sh), c, jitter=0.05, size=5)
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xticks(range(4))
    ax.set_xticklabels(["Q1", "Q2", "Q3", "Q4"])
    ax.set_xlabel("Trace-share quartile")
    ax.set_ylabel("Trace minus Shapley share")
    label(ax, "B", dx=-0.2)
    ax = axs[2]
    sg = G.groupby("seed").superadd.first()
    sr = Rr.groupby("seed").superadd.first()
    dots(ax, 0, sg, GPT)
    dots(ax, 1, sr, RUL)
    ax.axhline(1, color=MUTED, lw=0.6, ls="--")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Learnable", "Rule-based"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("Superadditivity, v(N)/Σ v({g})")
    label(ax, "C", dx=-0.22)
    ax = axs[3]
    dg, dr = slope_diff(G), slope_diff(Rr)
    common = dg.index.intersection(dr.index)
    for s in common:
        ax.plot([0, 1], [dg[s], dr[s]], color=RULE, lw=0.6, zorder=1)
    dots(ax, 0, dg[common], GPT, jitter=0)
    dots(ax, 1, dr[common], RUL, jitter=0)
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Learnable", "Rule-based"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("Slope difference (direct − trace)")
    label(ax, "D", dx=-0.32)
    fig.tight_layout(w_pad=0.9)
    save(fig, "FigS4")
    print("slope diff means", dg.mean(), dr.mean(), (dg[common] - dr[common]).mean())


# ---------------------------------------------------------------- fig. S5
def figS5():
    """Trace and cause in the travelling-salesman colony (exp7)."""
    reset_rng()
    g = pd.read_csv(R("exp7_group_shapley.csv"))
    g["q"] = g.groupby("seed").cumcount()
    st = pd.read_csv(R("exp7_counterfactual_stats.csv"))
    fig, axs = plt.subplots(1, 3, figsize=(W, 5.0 * CM), gridspec_kw={"width_ratios": [1, 1, 1.5]})
    ax = axs[0]
    ax.scatter(g.provenance_share, g.shapley_share, s=6, color=BLUE, alpha=0.4, lw=0)
    m = g.groupby("q")[["provenance_share", "shapley_share"]].mean()
    ax.plot(m.provenance_share, m.shapley_share, "o-", color=BLUE, ms=3, lw=0.9)
    lim = [0.19, 0.31]
    ax.plot(lim, lim, ls="--", color=MUTED, lw=0.7)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Provenance share")
    ax.set_ylabel("Shapley share")
    label(ax, "A", dx=-0.2)
    ax = axs[1]
    suff = (g.v_single / g.v_all).groupby(g.seed).mean()
    dots(ax, 0, suff, BLUE)
    ax.set_xlim(-0.8, 0.8)
    ax.set_xticks([])
    ax.set_ylabel("Mean v({g}) / v(N)")
    label(ax, "B", dx=-0.25)
    ax = axs[2]
    y = np.arange(len(st))[::-1]
    cols = [BLUE if c.startswith("top") else (AQUA if c.startswith("bottom") else MUTED) for c in st.condition]
    ax.errorbar(st["mean"], y, xerr=[st["mean"] - st.ci_lo, st.ci_hi - st["mean"]], fmt="none",
                ecolor=cols, elinewidth=1.0)
    ax.scatter(st["mean"], y, c=cols, s=12, zorder=3)
    ax.axvline(0, color=MUTED, lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([c.replace("-", " ") for c in st.condition])
    ax.set_xlabel("Change in best tour length after removal")
    label(ax, "C", dx=-0.2)
    fig.tight_layout(w_pad=1.0)
    save(fig, "FigS5")


# ---------------------------------------------------------------- fig. S6
def figS6():
    """Paired return forks for learnable and rule-based colonies (exp12)."""
    reset_rng()
    d = np.load(R("exp12.npy"), allow_pickle=True).item()
    T2 = d["T2"]
    B = d["blocks"]
    fig, axs = plt.subplots(1, 4, figsize=(W, 4.9 * CM))
    for core, x, c in [("gpt", 0, GPT), ("rule", 1, RUL)]:
        Rr = [r for r in B if r["core"] == core]
        stp = Rr[0]["step"]
        i2 = int(np.searchsorted(stp, T2))
        post = lambda r, n: r[f"{n}_frac"][stp > T2 + 100].mean()  # noqa: E731
        dlv = lambda r, n: r[f"{n}_delivered"][-1] - r[f"{n}_delivered"][i2]  # noqa: E731
        dots(axs[0], x, [post(r, "blocked") - post(r, "control") for r in Rr], c)
        dots(axs[1], x, [dlv(r, "blocked") - dlv(r, "control") for r in Rr], c)
    for ax, yl, L in [(axs[0], "Short-corridor share,\nblocked − twin", "A"),
                      (axs[1], "Deliveries after reopening,\nblocked − twin", "B")]:
        ax.axhline(0, color=MUTED, lw=0.6)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Learnable", "Rule-based"])
        ax.set_xlim(-0.6, 1.6)
        ax.set_ylabel(yl)
        label(ax, L, dx=-0.25)
    G = [r for r in B if r["core"] == "gpt"]
    ex = np.concatenate([r["js_bc"] - r["js_cc"] for r in G])
    ax = axs[2]
    ax.hist(ex, bins=40, color=GPT, alpha=0.8)
    ax.axvline(0, color=INK2, lw=0.6)
    ax.axvline(ex.mean(), color=ORANGE, lw=0.9, ls="--")
    ax.set_xlabel("Per-ant JS(B, C1) − JS(C1, C2) (nats)")
    ax.set_ylabel("Ants (20 seeds × 30)")
    label(ax, "C", dx=-0.2)
    ax = axs[3]
    frac = [(r["js_bc"] > r["js_cc"]).mean() for r in G]
    dots(ax, 0, frac, GPT)
    ax.axhline(0.5, color=MUTED, lw=0.6, ls="--")
    ax.set_xlim(-0.8, 0.8)
    ax.set_xticks([])
    ax.set_ylabel("Fraction of ants above chance")
    label(ax, "D", dx=-0.25)
    fig.tight_layout(w_pad=1.0)
    save(fig, "FigS6")


if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2", "3", "4", "5", "6"]
    for w in which:
        globals()[f"figS{w}"]()
