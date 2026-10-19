"""
論文主圖（Fig. 1–5）
====================================
慣例：雙欄寬 18 cm；Arial 類無襯線字（Liberation Sans）6–8 pt；分圖以粗體大寫 A、B、C 標於左上；
不加格線與圖內標題；單一種子以點表示，平均以實心標記，誤差線 = 95% bootstrap CI；
固定配色：可學習螞蟻 = 藍、規則螞蟻 = 橘、第三類 = 青；向量 PDF + 300 dpi PNG。
輸出：figures/paper/Fig1.pdf … Fig5.pdf
"""
import os

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.colors import LogNorm, LinearSegmentedColormap

from common import RESULTS, ROOT, bootstrap_ci

OUT = os.path.join(ROOT, "figures", "paper")
os.makedirs(OUT, exist_ok=True)

CM = 1 / 2.54
W = 18 * CM
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, RULE = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d4"
GPT, RUL = BLUE, ORANGE

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK, "text.color": INK,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300,
    "lines.linewidth": 1.2, "axes.titlesize": 7, "axes.grid": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
})


def label(ax, s, dx=-0.02, dy=1.0):
    ax.text(dx, dy, s, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")


def flabel(fig, s, x, y):
    fig.text(x, y, s, fontsize=9, fontweight="bold", va="top", ha="left")


_RNG = [np.random.default_rng(1)]


def reset_rng(seed=1):
    """Reset the jitter generator so that each figure is identical however the script is invoked."""
    _RNG[0] = np.random.default_rng(seed)


def dots(ax, x, vals, color, jitter=0.07, size=7, mean=True, rng=None):
    rng = rng or _RNG[0]
    v = np.asarray(vals, float)
    ax.scatter(x + rng.uniform(-jitter, jitter, len(v)), v, s=size, color=color, alpha=0.45, lw=0, zorder=2)
    if mean:
        lo, hi = bootstrap_ci(v)
        ax.errorbar(x, v.mean(), yerr=[[v.mean() - lo], [hi - v.mean()]], fmt="o", ms=3.6, color=color,
                    mec="white", mew=0.6, elinewidth=1.0, capsize=0, zorder=3)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=300)
    plt.close(fig)
    print("saved", name)


def box(ax, x, y, w, h, text, fc="white", ec=INK2, fs=6.5, bold=False, tc=INK, lw=0.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, linespacing=1.25)


def arrow(ax, p, q, color=INK2, lw=0.8, style="-|>", rad=0.0, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=7, color=color, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}", linestyle=ls, shrinkA=0, shrinkB=0))


FD = np.load(os.path.join(RESULTS, "fig_data.npy"), allow_pickle=True).item()


# ====================================================================== Fig. 1
def fig1():
    reset_rng()
    fig = plt.figure(figsize=(W, 11.2 * CM))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05], width_ratios=[1.25, 1, 1], hspace=0.55, wspace=0.42,
                          left=0.06, right=0.985, top=0.95, bottom=0.08)

    # A architecture
    ax = fig.add_subplot(gs[0, :2]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    flabel(fig, "A", 0.01, 0.985)
    box(ax, 0.01, 0.58, 0.16, 0.30, "World\n(grid, nest,\nfood)", fc="#f4f3f0")
    box(ax, 0.23, 0.58, 0.17, 0.30, "Perception token\n3 cells ahead\n15 symbols")
    box(ax, 0.46, 0.52, 0.22, 0.42, "microGPT core\n1 layer, 4 heads\n4096 parameters\ncontext 16 tokens",
        fc="#eaf2fc", ec=BLUE, bold=False, lw=1.0)
    box(ax, 0.74, 0.58, 0.17, 0.30, "Action token\nmove / turn / mark\n8 symbols")
    box(ax, 0.23, 0.04, 0.68, 0.24, "Shared pheromone medium   τ ← ρτ + Δτ   (provenance per ant)",
        fc="#eef8f3", ec=AQUA, lw=1.0)
    arrow(ax, (0.17, 0.73), (0.23, 0.73)); arrow(ax, (0.40, 0.73), (0.46, 0.73)); arrow(ax, (0.68, 0.73), (0.74, 0.73))
    arrow(ax, (0.825, 0.58), (0.825, 0.28), color=AQUA); ax.text(0.835, 0.43, "deposit", fontsize=6, color=INK2)
    arrow(ax, (0.315, 0.28), (0.315, 0.58), color=AQUA); ax.text(0.325, 0.43, "sense", fontsize=6, color=INK2)
    arrow(ax, (0.91, 0.80), (0.96, 0.80), style="-"); arrow(ax, (0.96, 0.80), (0.96, 0.96), style="-")
    arrow(ax, (0.96, 0.96), (0.085, 0.96), style="-"); arrow(ax, (0.085, 0.96), (0.085, 0.88))
    ax.text(0.52, 0.975, "act", fontsize=6, color=INK2, ha="center")
    ax.text(0.57, 0.46, "fine-tunes on its own\nsuccessful trips", fontsize=6, color=BLUE, ha="center", va="top")
    ax.text(0.0, 0.16, "× 30 ants,\nseparate weights", fontsize=6, color=INK2, va="center")

    # B token sequence
    ax = fig.add_subplot(gs[0, 2]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    flabel(fig, "B", 0.655, 0.985)
    seq = list(".NFPFPFAFXT1f1f2r1f0D")
    names = {"N": "nothing", "P": "trail ahead", "A": "food ahead", "X": "on food", "1": "nest ahead",
             "2": "nest right", "0": "at nest", "F": "forward", "T": "take", "f": "forward+mark",
             "r": "right+mark", "D": "drop"}
    per = 7
    for i, t in enumerate(seq):
        r, c = divmod(i, per)
        x, y = 0.02 + c * 0.135, 0.80 - r * 0.25
        act = t in "FLRflrTD"
        fc = BLUE if act else "white"
        ax.add_patch(Rectangle((x, y), 0.115, 0.17, fc=fc, ec=BLUE if act else INK2, lw=0.7))
        ax.text(x + 0.0575, y + 0.085, "BOS" if t == "." else t, ha="center", va="center", fontsize=6.5 if t != "." else 5,
                color="white" if act else INK, family="DejaVu Sans Mono")
    ax.add_patch(Rectangle((0.02, 0.08), 0.06, 0.07, fc="white", ec=INK2, lw=0.7))
    ax.text(0.10, 0.115, "perception", fontsize=6, va="center", color=INK2)
    ax.add_patch(Rectangle((0.48, 0.08), 0.06, 0.07, fc=BLUE, ec=BLUE, lw=0.7))
    ax.text(0.56, 0.115, "action (predicted)", fontsize=6, va="center", color=INK2)
    ax.text(0.02, -0.02, "search → take food →\ncarry home while marking → drop", fontsize=5.8, color=INK2, va="top")

    # C map
    ax = fig.add_subplot(gs[1, 0]); flabel(fig, "C", 0.01, 0.50)
    c0 = [c for c in FD["curves"] if "tau" in c][0]
    tau, walls = c0["tau"], c0["walls"]
    cmap = LinearSegmentedColormap.from_list("seqblue", ["#eaf2fc", "#9cc3ef", BLUE, "#103e78"])
    img = np.ma.masked_where(walls, np.maximum(tau, 1e-3))
    ax.imshow(np.where(walls, 1, np.nan), cmap=mpl.colors.ListedColormap(["#3d3c39"]), interpolation="nearest")
    im = ax.imshow(img, cmap=cmap, norm=LogNorm(1e-2, max(1.0, tau.max())), interpolation="nearest")
    ys, xs = np.nonzero(c0["nest"]); ax.add_patch(Rectangle((xs.min() - .5, ys.min() - .5), 3, 3, fc="none", ec=ORANGE, lw=1.0))
    ys, xs = np.nonzero(c0["food"]); ax.add_patch(Rectangle((xs.min() - .5, ys.min() - .5), 3, 3, fc="none", ec=AQUA, lw=1.0))
    ax.text(3, 17.9, "nest", fontsize=6, color=ORANGE, ha="center"); ax.text(36, 17.9, "food", fontsize=6, color=AQUA, ha="center")
    ax.text(20, 10.2, "short corridor", fontsize=5.8, color=INK, ha="center"); ax.text(20, 1.2, "long corridor", fontsize=5.8, color=INK, ha="center")
    ax.set_xticks([]); ax.set_yticks([]); [s.set_visible(False) for s in ax.spines.values()]
    ax.set_ylim(18.6, 0.2)
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.06, pad=0.04, aspect=30)
    cb.set_label("pheromone (log scale)", fontsize=6); cb.ax.tick_params(labelsize=5.5, width=0.5, length=2); cb.outline.set_linewidth(0.4)

    # D cumulative deliveries (double bridge)
    ax = fig.add_subplot(gs[1, 1]); label(ax, "D", dx=-0.22)
    for tag, col, lab in (("rule", RUL, "Rule-based"), ("gpt_bc", AQUA, "Base model"), ("gpt_learn", GPT, "Learnable")):
        cs = [c for c in FD["curves"] if c["tag"] == tag]
        st = cs[0]["step"]; Y = np.array([c["delivered"] for c in cs])
        lo, hi = np.percentile(Y, 2.5, 0), np.percentile(Y, 97.5, 0)
        ax.fill_between(st, lo, hi, color=col, alpha=0.15, lw=0); ax.plot(st, Y.mean(0), color=col, lw=1.2)
        ax.text(st[-1] + 40, Y.mean(0)[-1], lab, fontsize=6, color=INK, va="center")
    ax.set_xlim(0, 3900); ax.set_xticks([0, 1000, 2000, 3000])
    ax.set_xlabel("Step"); ax.set_ylabel("Food delivered (cumulative)")
    ax.text(0.02, 0.98, "Double bridge", transform=ax.transAxes, fontsize=6, color=INK2, va="top")

    # E final yields both maps
    ax = fig.add_subplot(gs[1, 2]); label(ax, "E", dx=-0.25)
    d = pd.read_csv(os.path.join(RESULTS, "exp9a_parity.csv"))
    for j, m in enumerate(("open_field", "double_bridge")):
        ref = d[(d["map"] == m) & (d.tag == "rule")].delivered.mean()
        for k, (tag, col) in enumerate((("rule", RUL), ("gpt_bc", AQUA), ("gpt_learn", GPT))):
            v = d[(d["map"] == m) & (d.tag == tag)].delivered / ref
            dots(ax, j + (k - 1) * 0.24, v, col, jitter=0.04)
    ax.axhline(1, color=MUTED, lw=0.6, ls=":")
    ax.set_xticks([0, 1], ["Open field", "Double bridge"]); ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("Yield relative to rule-based ants")
    save(fig, "Fig1")


# ====================================================================== Fig. 2
def fig2():
    reset_rng()
    fig, axes = plt.subplots(2, 3, figsize=(W, 10.5 * CM), gridspec_kw=dict(hspace=0.55, wspace=0.5))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.95, bottom=0.09)
    b = pd.read_csv(os.path.join(RESULTS, "exp9b_stigmergy.csv"))
    ax = axes[0, 0]; label(ax, "A", dx=-0.25)
    for k, (core, col) in enumerate((("gpt", GPT), ("rule", RUL))):
        for j, med in enumerate(("shared", "private", "cut")):
            dots(ax, j + (k - 0.5) * 0.3, b[b.tag == f"{core}_{med}"].delivered, col, jitter=0.05)
    ax.set_xticks([0, 1, 2], ["Shared", "Private", "Cut"]); ax.set_xlabel("Medium"); ax.set_ylabel("Food delivered")
    ax.text(0.98, 0.98, "Learnable", color=GPT, transform=ax.transAxes, ha="right", va="top", fontsize=6.5)
    ax.text(0.98, 0.88, "Rule-based", color=RUL, transform=ax.transAxes, ha="right", va="top", fontsize=6.5)

    g = pd.read_csv(os.path.join(RESULTS, "exp13_per_seed.csv")); g = g[g.core == "gpt"]
    s = g[g.medium == "shared"].set_index("seed"); p = g[g.medium == "private"].set_index("seed")
    ax = axes[0, 1]; label(ax, "B", dx=-0.34)
    for sd in s.index:
        ax.plot([0, 1], [s.disp[sd], p.disp[sd]], color=MUTED, lw=0.5, zorder=1)
    dots(ax, 0, s.disp, GPT, jitter=0); dots(ax, 1, p.disp, GPT, jitter=0)
    e11 = os.path.join(RESULTS, "exp11_per_seed.csv")
    if os.path.exists(e11):
        e = pd.read_csv(e11); soc = e[e.tag == "social"].dispersion
        dots(ax, 2, soc, AQUA, jitter=0.05)
        ax.set_xticks([0, 1, 2], ["Shared", "Private", "Shared +\nsocial"]); ax.set_xlim(-0.4, 2.4)
    else:
        ax.set_xticks([0, 1], ["Shared", "Private"]); ax.set_xlim(-0.4, 1.4)
    ax.set_ylabel("Between-ant dispersion (nats)"); ax.set_ylim(0, None)

    ax = axes[0, 2]; label(ax, "C", dx=-0.3)
    diff = (s.disp - p.disp).values; ref = p.disp.mean()
    lo90, hi90 = bootstrap_ci(diff, alpha=0.10)
    ax.axvspan(-0.1 * ref, 0.1 * ref, color=RULE, alpha=0.6, lw=0)
    ax.axvline(0, color=INK2, lw=0.6)
    ax.errorbar(diff.mean(), 0, xerr=[[diff.mean() - lo90], [hi90 - diff.mean()]], fmt="o", ms=4, color=GPT,
                mec="white", mew=0.6, elinewidth=1.2)
    ax.scatter(diff, np.random.default_rng(2).uniform(-0.25, 0.25, len(diff)) + 0.6, s=7, color=GPT, alpha=0.45, lw=0)
    ax.set_ylim(-0.6, 1.1); ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Shared − private dispersion (nats)")
    ax.text(0, 1.02, "±10% equivalence bound", ha="center", fontsize=6, color=INK2)

    ax = axes[1, 0]; label(ax, "D", dx=-0.25)
    base = 0.9992
    dots(ax, 0, s.legal_mass, GPT, jitter=0.05); dots(ax, 1, p.legal_mass, GPT, jitter=0.05)
    ax.axhline(base, color=INK2, lw=0.6, ls="--"); ax.text(1.75, base - 0.0006, "base model", fontsize=5.8, color=INK2, va="top", ha="right")
    ax.set_xticks([0, 1], ["Shared", "Private"]); ax.set_xlim(-0.5, 1.8)
    ax.set_ylabel("Probability on legal actions"); ax.set_ylim(0.975, 1.0005)

    ax = axes[1, 1]; label(ax, "E", dx=-0.3)
    for j, (S, lab) in enumerate(((s, "Shared"), (p, "Private"))):
        dots(ax, j - 0.15, S.disp, GPT, jitter=0.03); dots(ax, j + 0.15, S.disp_within, AQUA, jitter=0.03)
    ax.set_xticks([0, 1], ["Shared", "Private"]); ax.set_xlim(-0.5, 1.5); ax.set_ylim(0, None)
    ax.set_ylabel("Dispersion (nats)")
    ax.text(0.02, 0.15, "all actions", color=GPT, transform=ax.transAxes, fontsize=6)
    ax.text(0.02, 0.05, "within grammar", color=AQUA, transform=ax.transAxes, fontsize=6)

    ax = axes[1, 2]; label(ax, "F", dx=-0.3)
    t = pd.read_csv(os.path.join(RESULTS, "exp4a_private_vs_shared.csv"))
    for j, beta in enumerate(sorted(t.beta.unique())):
        pv = t[(t.beta == beta) & (t["mode"] == "private")].set_index("seed").best
        sv = t[(t.beta == beta) & (t["mode"] == "shared")].set_index("seed").best
        dots(ax, j, (pv / sv).values, RUL, jitter=0.05)
    ax.axhline(1, color=MUTED, lw=0.6, ls=":")
    ax.set_xticks(range(3), ["1", "2", "5"]); ax.set_xlabel("Heuristic weight β (TSP)")
    ax.set_ylabel("Collective gain L$_{private}$ / L$_{shared}$")
    save(fig, "Fig2")


# ====================================================================== Fig. 3
def fig3():
    reset_rng()
    fig = plt.figure(figsize=(W, 11 * CM))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], hspace=0.55, wspace=0.45, left=0.095, right=0.985, top=0.95, bottom=0.09)
    ax = fig.add_subplot(gs[0, :2]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    flabel(fig, "A", 0.01, 0.985)
    ax.plot([0.02, 0.36], [0.55, 0.55], color=INK, lw=2.2)
    ax.text(0.19, 0.64, "shared history: 2000 steps of learning", ha="center", fontsize=6.5)
    ax.text(0.19, 0.42, "trace share measured\n(provenance in the medium)", ha="center", fontsize=6, color=INK2, va="top")
    ax.scatter([0.36], [0.55], s=40, color=INK, zorder=3)
    ax.text(0.36, 0.30, "pause and\ncopy full state", ha="center", fontsize=6, color=INK2, va="top")
    branches = [(0.92, "unperturbed (reference)", INK), (0.77, "unperturbed, new random stream (noise)", MUTED),
                (0.60, "remove top / bottom / random ants", GPT), (0.43, "remove top-k vs random-k", GPT),
                (0.24, "keep one coalition of quartiles (16 coalitions)", AQUA)]
    for y, txt, col in branches:
        ax.annotate("", xy=(0.66, y), xytext=(0.37, 0.55),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=0.9, mutation_scale=7, connectionstyle="arc3,rad=0"))
        ax.text(0.67, y, txt, fontsize=6.2, va="center", color=INK)
    ax.text(0.515, 0.03, "1000 steps each, same reseeded random stream", ha="center", fontsize=6, color=INK2)

    sh = {c: pd.read_csv(os.path.join(RESULTS, f"exp10_shapley_{c}.csv")) for c in ("gpt", "rule")}
    for c in sh:
        sh[c]["sh"] = sh[c].groupby("seed").phi.transform(lambda x: x / x.sum())
        sh[c]["q"] = sh[c].groupby("seed").cumcount()
    ax = fig.add_subplot(gs[0, 2]); label(ax, "B", dx=-0.25)
    ax.plot([0, 0.55], [0, 0.55], color=MUTED, lw=0.6, ls="--")
    for c, col in (("gpt", GPT), ("rule", RUL)):
        d = sh[c]
        ax.scatter(d.trace_share, d.sh, s=7, color=col, alpha=0.35, lw=0)
        m = d.groupby("q")[["trace_share", "sh"]].mean()
        ax.plot(m.trace_share, m.sh, "-o", color=col, ms=3.2, mec="white", mew=0.5, lw=1.0)
    ax.set_xlim(0, 0.55); ax.set_ylim(0, 0.55); ax.set_aspect("equal")
    ax.set_xlabel("Trace share of quartile"); ax.set_ylabel("Shapley share of quartile")
    ax.text(0.53, 0.05, "Q1", fontsize=6, ha="right", color=INK2)
    ax.text(0.05, 0.50, "equality", fontsize=6, color=MUTED, rotation=45)

    ax = fig.add_subplot(gs[1, 0]); label(ax, "C", dx=-0.25)
    for k, (c, col) in enumerate((("gpt", GPT), ("rule", RUL))):
        d = sh[c]
        for q in range(4):
            dots(ax, q + (k - 0.5) * 0.3, (d[d.q == q].trace_share - d[d.q == q].sh).values, col, jitter=0.04)
    ax.axhline(0, color=INK2, lw=0.6)
    ax.set_xticks(range(4), ["Q1\n(most trace)", "Q2", "Q3", "Q4\n(least)"])
    ax.set_ylabel("Trace share − Shapley share")
    ax.text(0.98, 0.98, "Learnable", color=GPT, transform=ax.transAxes, ha="right", va="top", fontsize=6.5)
    ax.text(0.98, 0.88, "Rule-based", color=RUL, transform=ax.transAxes, ha="right", va="top", fontsize=6.5)

    ax = fig.add_subplot(gs[1, 1]); label(ax, "D", dx=-0.3)
    for k, (c, col) in enumerate((("gpt", GPT), ("rule", RUL))):
        v = sh[c].groupby("seed").superadd.first()
        dots(ax, k, v, col, jitter=0.05)
    ax.axhline(1, color=INK2, lw=0.6, ls="--"); ax.text(1.45, 1.0, "additive", fontsize=6, color=INK2, va="bottom", ha="right")
    ax.set_xticks([0, 1], ["Learnable", "Rule-based"]); ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("v(N) / Σ v({g})")

    ax = fig.add_subplot(gs[1, 2]); label(ax, "E", dx=-0.42)
    st = pd.read_csv(os.path.join(RESULTS, "exp10_counterfactual_stats.csv"))
    conds = ["top-1", "bottom-1", "random-1", "top-25%", "random-25%", "top-50%", "random-50%"]
    noise = {"gpt": 1.047, "rule": 0.908}
    ax.axvspan(-noise["gpt"], noise["gpt"], color=RULE, alpha=0.5, lw=0)
    for k, (c, col) in enumerate((("gpt", GPT), ("rule", RUL))):
        r = st[(st.core == c) & (st.outcome == "d_indirect")].set_index("condition").loc[conds]
        y = np.arange(len(conds)) + (k - 0.5) * 0.3
        ax.errorbar(r["mean"], y, xerr=[r["mean"] - r.ci_lo, r.ci_hi - r["mean"]], fmt="o", ms=3, color=col,
                    mec="white", mew=0.5, elinewidth=0.9)
    ax.axvline(0, color=INK2, lw=0.6)
    ax.set_yticks(range(len(conds)), conds); ax.invert_yaxis()
    ax.set_xlabel("Change in deliveries per survivor")
    ax.text(0, -0.9, "band: typical difference between\ntwo unperturbed futures", ha="center", fontsize=5.6, color=INK2)
    save(fig, "Fig3")


# ====================================================================== Fig. 4
def fig4():
    reset_rng()
    fig, axes = plt.subplots(2, 3, figsize=(W, 10.5 * CM), gridspec_kw=dict(hspace=0.6, wspace=0.55))
    fig.subplots_adjust(left=0.09, right=0.985, top=0.95, bottom=0.10)
    st = pd.read_csv(os.path.join(RESULTS, "exp8_topic3_stats.csv")); st = st[st.part == "control1"]
    rhos = sorted(st.rho.unique())
    ax = axes[0, 0]; label(ax, "A", dx=-0.32)
    for k, (m, col, lab) in enumerate((("perf_gap", GPT, "Competence"), ("archive_gap", RUL, "Record"))):
        r = st[st.metric == m].set_index("rho").loc[rhos]
        x = np.arange(len(rhos)) + (k - 0.5) * 0.25
        ax.errorbar(x, r["mean"], yerr=[r["mean"] - r.ci_lo, r.ci_hi - r["mean"]], fmt="o", ms=3.5, color=col,
                    mec="white", mew=0.5, elinewidth=1.0, label=lab)
    ax.axhline(0, color=INK2, lw=0.6); ax.set_xticks(range(len(rhos)), [str(r) for r in rhos]); ax.set_xlabel("Retention ρ")
    ax.set_ylabel("Δ gap to optimum (pp)"); ax.legend(loc="upper right", handletextpad=0.2)

    ax = axes[0, 1]; label(ax, "B", dx=-0.34)
    for k, (m, col, lab) in enumerate((("J_medium", AQUA, "Medium path"), ("J_best", RUL, "Record path"))):
        r = st[st.metric == m].set_index("rho").loc[rhos]
        x = np.arange(len(rhos)) + (k - 0.5) * 0.25
        ax.errorbar(x, r["mean"], yerr=[r["mean"] - r.ci_lo, r.ci_hi - r["mean"]], fmt="o", ms=3.5, color=col,
                    mec="white", mew=0.5, elinewidth=1.0, label=lab)
    ax.axhline(0, color=INK2, lw=0.6); ax.set_xticks(range(len(rhos)), [str(r) for r in rhos]); ax.set_xlabel("Retention ρ")
    ax.set_ylabel("Δ path overlap (Jaccard)"); ax.legend(loc="lower right", handletextpad=0.2)

    ax = axes[0, 2]; label(ax, "C", dx=-0.3)
    h = pd.read_csv(os.path.join(RESULTS, "exp6a_block_unblock.csv"))
    rr = np.linspace(0.25, 0.93, 100)
    ax.plot(rr, np.log(0.5) / np.log(rr), color=INK2, lw=0.8, ls="--")
    ax.text(0.62, 5.2, "ln ½ / ln ρ", fontsize=6, color=INK2)
    for rho in sorted(h.rho.unique()):
        dots(ax, rho, h[h.rho == rho].blocked_edge_half_life, AQUA, jitter=0.008)
    ax.set_xlabel("Retention ρ"); ax.set_ylabel("Pheromone half-life (cycles)")

    E12 = os.path.join(RESULTS, "exp12.npy")
    D12 = np.load(E12, allow_pickle=True).item() if os.path.exists(E12) else FD
    B = D12["blocks"]; T1, T2 = D12["T1"], D12["T2"]
    for j, (core, col, lab, L) in enumerate((("gpt", GPT, "Learnable ants", "D"), ("rule", RUL, "Rule-based ants", "E"))):
        ax = axes[1, j]; label(ax, L, dx=-0.27)
        R = [b for b in B if b["core"] == core]; stp = R[0]["step"]
        for name, ls, c in (("control", "-", MUTED), ("blocked", "-", col)):
            Y = np.array([b[f"{name}_frac"] for b in R])
            if name == "blocked":
                Y = np.where((stp > T1) & (stp <= T2), np.nan, Y)
            ax.plot(stp, np.nanmean(Y, 0) if name == "control" else Y.mean(0), color=c, lw=1.0, ls=ls)
        ax.axvspan(T1, T2, color=RULE, alpha=0.5, lw=0)
        ax.set_ylim(0, 1); ax.set_xlabel("Step"); ax.set_ylabel("Short-corridor share of crossings")
        ax.text(0.02, 0.04, lab, transform=ax.transAxes, fontsize=6.5, color=INK)
        ax.text((T1 + T2) / 2, 0.45, "short corridor\nblocked", ha="center", va="center", fontsize=5.8, color=INK2)
        ax.text(0.98, 0.04, "grey: unblocked branch", transform=ax.transAxes, fontsize=5.6, color=MUTED, ha="right")

    ax = axes[1, 2]; label(ax, "F", dx=-0.34)
    N = [b for b in B if b["core"] == "gpt" and "js_cc" in b] or list(np.load(os.path.join(RESULTS, "fig_data_null.npy"), allow_pickle=True))
    cc = np.array([r["js_cc"].mean() for r in N]); bc = np.array([r["js_bc"].mean() for r in N])
    for i in range(len(N)):
        ax.plot([0, 1], [cc[i], bc[i]], color=RULE, lw=0.6, zorder=1)
    dots(ax, 0, cc, MUTED, jitter=0); dots(ax, 1, bc, GPT, jitter=0)
    ax.set_xticks([0, 1], ["two unblocked\nbranches", "blocked vs\nunblocked"]); ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("Per-ant policy divergence (JS, nats)"); ax.set_ylim(0, None)
    ax.text(0.5, 1.0, "Learnable ants, end of run", transform=ax.transAxes, ha="center", va="bottom", fontsize=6, color=INK2)
    save(fig, "Fig4")


# ====================================================================== Fig. 5
def fig5():
    reset_rng()
    fig = plt.figure(figsize=(W, 8.2 * CM)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    rows = [(0.70, "Collective"), (0.42, "Medium"), (0.14, "Individuals\nand records")]
    for y, t in rows:
        ax.text(0.10, y + 0.08, t, ha="right", va="center", fontsize=7, fontweight="bold", color=INK2)
    cols = [(0.14, "D1  Coordination", ["Yield ×1.6 with a\nshared medium",
                                         "Coordination is held\nin the shared field",
                                         "Policies stay as diverse\nas with private media;\nmost divergence within grammar"]),
            (0.43, "D2  Responsibility", ["Outcome over-determined;\nno ant is necessary",
                                          "Provenance concentrates\ncredit in fewer hands",
                                          "Top-trace quartile: 40% of trace,\n31% of causal (Shapley) share"]),
            (0.72, "D3  Memory", ["Competence recovers\nafter the perturbation",
                                  "Forgets at a tunable rate\n(half-life ln ½ / ln ρ)",
                                  "Archived solution and\nindividual policies\ndo not return"])]
    for x, head, items in cols:
        ax.text(x + 0.13, 0.96, head, ha="center", va="center", fontsize=7.5, fontweight="bold")
        for (y, _), txt, (fc, ec) in zip(rows, items, [("white", INK2), ("#eef8f3", AQUA), ("white", INK2)]):
            box(ax, x, y, 0.26, 0.20, txt, fc=fc, ec=ec, fs=6.3, lw=1.0 if ec == AQUA else 0.7)
        arrow(ax, (x + 0.13, 0.62), (x + 0.13, 0.70), color=AQUA)
        arrow(ax, (x + 0.13, 0.34), (x + 0.13, 0.42), color=MUTED, style="-", ls=(0, (2, 2)))
        ax.text(x + 0.14, 0.38, "≠", fontsize=8, color=INK2, va="center")
    save(fig, "Fig5")


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["1", "2", "3", "4", "5"]
    for w in which:
        globals()[f"fig{w}"]()
