"""
主題一（延伸）：microGPT 螞蟻語言模型
====================================
(a) 功能對等與學習：規則螞蟻 vs GPT（只做行為複製）vs GPT（行為複製＋線上自我模仿），兩種地圖。
(b) Stigmergy：雙橋上，GPT＋線上學習在 共享／私有／切斷 介質下的送達量與短橋比例
    （規則螞蟻同條件作為對照）。
(c) 方言與慣例：(b) 的 GPT 螞蟻在固定探針上下文下的行動分布——
    個體間分散度（方言）與相對基礎模型的漂移；以及標記（f/l/r）行為的變化。
(d) 可逆性：雙橋上封鎖短橋（第 T1 步）再解封（第 T2 步），比較規則螞蟻與 GPT＋學習螞蟻
    的短橋比例軌跡（學習型 agent 是否「記住」擾動？）。
"""
import numpy as np
import matplotlib.pyplot as plt

from common import (QUICK, SERIES, INK2, save_csv, save_fig, write_summary, pmap, bootstrap_ci)
from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.foraging import ForagingSystem, ForagingConfig
from miat_ants.foraging.analysis import make_probes, dispersion, drift
from miat_ants.foraging.cores import GPTCore
from miat_ants.foraging.system import BASE_WEIGHTS
from miat_ants.microgpt import MicroGPT

import os
SEEDS = 2 if QUICK else int(os.environ.get("EXP9_SEEDS", "20"))
SKIP_D = os.environ.get("EXP9_SKIP_D", "1") == "1"   # (d) 已由 exp12 的配對分岔取代
STEPS = 1200 if QUICK else 3000
T1, T2 = (400, 800) if QUICK else (1000, 2000)

PROBES = make_probes(ForagingSystem(ForagingConfig(map_name="double_bridge", core="rule", seed=999,
                                                   max_steps=800, collect_episodes=True)).run().episodes)


def env(kind, t, **p):
    return Event(kind, t, "environment", p, PRIORITY_ENV, "interrupt")


def run(args):
    tag, kw = args
    r = ForagingSystem(ForagingConfig(max_steps=STEPS, **kw)).run()
    h = r.history
    out = {"tag": tag, "map": kw.get("map_name"), "core": kw.get("core"), "seed": kw.get("seed"),
           "delivered": r.delivered, "hist": h,
           "short_frac": h["gate_short"][-1] / max(1, h["gate_short"][-1] + h["gate_long"][-1]),
           "timeouts": h["timeouts"][-1]}
    if r.probes:
        out["probes"] = np.array(r.probes)          # (epochs, A, n_ctx, K)
    return out


def gate_series(h):
    gs, gl = np.diff([0] + h["gate_short"]), np.diff([0] + h["gate_long"])
    return gs / np.maximum(gs + gl, 1)


def main():
    summ = ["## 實驗9（主題一延伸）：microGPT 螞蟻語言模型", "",
            f"設定：30 隻螞蟻、{STEPS} 步、{SEEDS} 個種子；模型約 4 千參數（24 詞、上下文 16）。", ""]
    base = MicroGPT.load(BASE_WEIGHTS)
    base_probe = GPTCore(1, np.random.default_rng(0), base, "shared").policy_probe(PROBES)[0]

    # ---------------- (a)
    jobs = []
    for m in ("open_field", "double_bridge"):
        for s in range(SEEDS):
            jobs += [("rule", dict(map_name=m, core="rule", seed=s)),
                     ("gpt_bc", dict(map_name=m, core="gpt", learn=False, seed=s)),
                     ("gpt_learn", dict(map_name=m, core="gpt", learn=True, seed=s))]
    ra = pmap(run, jobs)
    rows = [{k: v for k, v in r.items() if k not in ("hist", "probes")} for r in ra]
    save_csv("exp9a_parity.csv", rows)
    summ += ["### (a) 功能對等與學習", "", "| 地圖 | 核心 | 送達量 平均 [95% CI] | 相對規則螞蟻 | 短橋比例 | 逾時回合 |",
             "|---|---|---|---|---|---|"]
    for m in ("open_field", "double_bridge"):
        ref = np.mean([r["delivered"] for r in rows if r["map"] == m and r["tag"] == "rule"])
        for tag, lab in (("rule", "規則螞蟻"), ("gpt_bc", "GPT（BC）"), ("gpt_learn", "GPT（BC＋線上學習）")):
            R = [r for r in rows if r["map"] == m and r["tag"] == tag]
            d = [r["delivered"] for r in R]
            lo, hi = bootstrap_ci(d)
            sf = np.mean([r["short_frac"] for r in R]) if m == "double_bridge" else float("nan")
            summ.append(f"| {m} | {lab} | {np.mean(d):.0f} [{lo:.0f}, {hi:.0f}] | {np.mean(d) / ref:.2f} | "
                        f"{sf:.3f} | {np.mean([r['timeouts'] for r in R]):.0f} |")
    summ.append("")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6))
    for ax, m in zip(axes, ("open_field", "double_bridge")):
        for k, (tag, lab) in enumerate((("rule", "規則螞蟻"), ("gpt_bc", "GPT（BC）"), ("gpt_learn", "GPT（BC＋線上學習）"))):
            R = [r for r in ra if r["map"] == m and r["tag"] == tag]
            ax.plot(R[0]["hist"]["step"], np.mean([r["hist"]["delivered"] for r in R], 0), color=SERIES[k], label=lab)
        ax.set_xlabel("步"); ax.set_ylabel("累積送達量"); ax.set_title({"open_field": "開闊地圖", "double_bridge": "雙橋"}[m])
    axes[0].legend()
    save_fig(fig, "exp9a_parity.png")

    # ---------------- (b)(c)
    jobs = []
    for s in range(SEEDS):
        for med in ("shared", "private", "cut"):
            kw = dict(map_name="double_bridge", seed=s, medium_mode="private" if med == "private" else "shared",
                      perturbations=[env("cut_medium", 0)] if med == "cut" else [])
            jobs.append((f"gpt_{med}", dict(core="gpt", learn=True, probe_contexts=PROBES, **kw)))
            jobs.append((f"rule_{med}", dict(core="rule", **kw)))
    rb = pmap(run, jobs)
    rows_b = [{k: v for k, v in r.items() if k not in ("hist", "probes")} for r in rb]
    summ += ["### (b) Stigmergy：介質條件（雙橋）", "",
             "| 核心 | 介質 | 送達量 [95% CI] | 短橋比例 | 搜尋時標記率 | 攜帶時標記率 |", "|---|---|---|---|---|---|"]
    for core in ("rule", "gpt"):
        for med in ("shared", "private", "cut"):
            R = [r for r in rb if r["tag"] == f"{core}_{med}"]
            d = [r["delivered"] for r in R]
            lo, hi = bootstrap_ci(d)
            ms = np.mean([np.mean(r["hist"]["mark_rate_search"][-10:]) for r in R])
            mc = np.mean([np.mean(r["hist"]["mark_rate_carry"][-10:]) for r in R])
            rows_b_ = {"core": core, "medium": med}
            summ.append(f"| {'規則' if core == 'rule' else 'GPT＋學習'} | {med} | {np.mean(d):.0f} [{lo:.0f}, {hi:.0f}] | "
                        f"{np.mean([r['short_frac'] for r in R]):.3f} | {ms:.3f} | {mc:.3f} |")
    save_csv("exp9b_stigmergy.csv", rows_b)
    summ.append("")

    # (c) dialect
    summ += ["### (c) 方言與慣例（GPT＋學習，固定 96 個探針上下文）", "",
             "| 介質 | 最終個體間分散度（nats）[95% CI] | 相對 BC 基礎模型的漂移 [95% CI] |", "|---|---|---|"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6))
    crow = []
    for k, med in enumerate(("shared", "private", "cut")):
        R = [r for r in rb if r["tag"] == f"gpt_{med}"]
        disp = np.array([[dispersion(ep) for ep in r["probes"]] for r in R])
        dr = np.array([[drift(ep, base_probe) for ep in r["probes"]] for r in R])
        steps = R[0]["hist"]["step"]
        axes[0].plot(steps, disp.mean(0), color=SERIES[k], label=med)
        axes[1].plot(steps, dr.mean(0), color=SERIES[k], label=med)
        fd, fr = disp[:, -1], dr[:, -1]
        crow += [{"medium": med, "seed": i, "dispersion": a, "drift": b} for i, (a, b) in enumerate(zip(fd, fr))]
        summ.append(f"| {med} | {fd.mean():.4f} [{bootstrap_ci(fd)[0]:.4f}, {bootstrap_ci(fd)[1]:.4f}] | "
                    f"{fr.mean():.4f} [{bootstrap_ci(fr)[0]:.4f}, {bootstrap_ci(fr)[1]:.4f}] |")
    save_csv("exp9c_dialect.csv", crow)
    axes[0].set_title("方言：個體間行動分布的分散度"); axes[0].set_ylabel("兩兩平均 JS（nats）")
    axes[1].set_title("漂移：相對行為複製基礎模型"); axes[1].set_ylabel("平均 JS（nats）")
    for ax in axes:
        ax.set_xlabel("步"); ax.legend()
    save_fig(fig, "exp9c_dialect.png")
    summ.append("")

    # ---------------- (d) block / unblock short bridge
    if SKIP_D:
        write_summary("exp9", summ)
        return
    jobs = []
    for s in range(SEEDS):
        ev = [env("block_gate", T1, gate="short"), env("unblock_gate", T2, gate="short")]
        jobs.append(("rule", dict(map_name="double_bridge", core="rule", seed=s, perturbations=ev)))
        jobs.append(("gpt_learn", dict(map_name="double_bridge", core="gpt", learn=True, seed=s, perturbations=ev)))
    rd = pmap(run, jobs)
    summ += [f"### (d) 可逆性：第 {T1} 步封鎖短橋、第 {T2} 步解封", "",
             "| 核心 | 封鎖前短橋比例 | 封鎖期間 | 解封後（最後 500 步） | 送達量 |", "|---|---|---|---|---|"]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    drow = []
    for k, (tag, lab) in enumerate((("rule", "規則螞蟻"), ("gpt_learn", "GPT＋學習"))):
        R = [r for r in rd if r["tag"] == tag]
        ser = np.array([gate_series(r["hist"]) for r in R])
        steps = np.array(R[0]["hist"]["step"])
        pre = ser[:, (steps > T1 - 500) & (steps <= T1)].mean()
        dur = ser[:, (steps > T1 + 100) & (steps <= T2)].mean()
        post = ser[:, steps > STEPS - 500].mean()
        drow.append({"core": tag, "pre": pre, "during": dur, "post": post,
                     "delivered": np.mean([r["delivered"] for r in R])})
        summ.append(f"| {lab} | {pre:.3f} | {dur:.3f} | {post:.3f} | {np.mean([r['delivered'] for r in R]):.0f} |")
        ax.plot(steps, ser.mean(0), color=SERIES[k], label=lab, lw=1.6)
    save_csv("exp9d_block_unblock.csv", drow)
    ax.axvspan(T1, T2, color="#e4e3df", alpha=0.6, lw=0)
    ax.set_xlabel("步"); ax.set_ylabel("每 epoch 短橋通過比例"); ax.set_ylim(0, 1); ax.legend()
    ax.set_title("封鎖／解封短橋")
    save_fig(fig, "exp9d_block_unblock.png")
    write_summary("exp9", summ)


if __name__ == "__main__":
    main()
