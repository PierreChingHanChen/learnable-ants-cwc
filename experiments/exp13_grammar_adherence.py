"""
實驗13（D1 延伸）：分化但守法？——可學習螞蟻對控制文法的遵守度
==============================================================
靈感來自「雙字母語言」研究的白箱指標（狀態預測、轉移合法率）：
把規則螞蟻（teacher）的有限狀態控制邏輯寫成「文法」：每個感知詞 → 合法行動集合。
  搜尋：X→{T}；W→{L,R}；A→{F}；B→{L}；C→{R}；P/Q/S/N→{F,L,R}
  攜帶：0→{D}；w→{l,r}；1/2/3/4→{f,l,r}
指標
  合法率（deployment）：實際執行中，行動屬於前一個感知詞之合法集合的比例（全部螞蟻、全部步）。
  合法質量（probe）：每隻螞蟻在 96 個探針上下文下，放在合法行動上的機率總和（平均）。
  文法內分散度：把每隻螞蟻的分布限制在合法集合內並重新正規化後，兩兩 JS 的平均。
問題：學習讓螞蟻彼此分化（exp9c），這種分化是「違反控制邏輯」還是「在文法允許的空間內各自選擇」？
"""
import numpy as np
import matplotlib.pyplot as plt

from common import QUICK, SERIES, INK2, save_csv, save_fig, write_summary, pmap, bootstrap_ci, paired_stats
from miat_ants.foraging import ForagingSystem, ForagingConfig
from miat_ants.foraging import vocab as V
from miat_ants.foraging.analysis import make_probes, dispersion, js
from miat_ants.foraging.cores import GPTCore
from miat_ants.foraging.system import BASE_WEIGHTS
from miat_ants.microgpt import MicroGPT

import os
SEEDS = 2 if QUICK else int(os.environ.get("EXP13_SEEDS", "20"))
STEPS = 1000 if QUICK else 3000
MEDIA = ("shared", "private")

GRAMMAR = {"X": "T", "W": "LR", "A": "F", "B": "L", "C": "R", "P": "FLR", "Q": "FLR", "S": "FLR", "N": "FLR",
           "0": "D", "w": "lr", "1": "flr", "2": "flr", "3": "flr", "4": "flr"}
ACT = [V.ITOS[i] for i in V.ACTION_IDS]                       # probe 輸出的行動順序
LEGAL = np.zeros((V.V, len(ACT)), bool)                        # 感知詞 id → 合法行動遮罩
for o, acts in GRAMMAR.items():
    for a in acts:
        LEGAL[V.STOI[o], ACT.index(a)] = True

PROBES = make_probes(ForagingSystem(ForagingConfig(map_name="double_bridge", core="rule", seed=999,
                                                   max_steps=800, collect_episodes=True)).run().episodes)
PMASK = LEGAL[PROBES[:, -1]]                                   # (n_ctx, K)


def deploy_legality(episodes):
    ok = tot = 0
    for e in episodes:
        for i in range(1, len(e) - 1, 2):                      # e = [BOS, o, a, o, a, ...]
            o, a = e[i], e[i + 1]
            ok += LEGAL[o, ACT.index(V.ITOS[a])]
            tot += 1
    return ok / max(1, tot)


def within_grammar(probes):
    p = np.where(PMASK[None], probes, 0.0)
    p = p / np.maximum(p.sum(-1, keepdims=True), 1e-12)
    return p


def run(args):
    core, med, seed = args
    r = ForagingSystem(ForagingConfig(map_name="double_bridge", core=core, learn=True, seed=seed,
                                      max_steps=STEPS, medium_mode=med, collect_episodes=True,
                                      probe_contexts=PROBES if core == "gpt" else None)).run()
    out = {"core": core, "medium": med, "seed": seed, "delivered": r.delivered,
           "deploy_legal": deploy_legality(r.episodes)}
    if r.probes:
        P = np.array(r.probes)                                   # (epochs, A, n_ctx, K)
        mass = (P * PMASK[None, None]).sum(-1).mean((-1))        # (epochs, A)
        out.update({"legal_mass_t": mass.mean(1), "legal_mass_ants": mass[-1],
                    "disp_t": np.array([dispersion(ep) for ep in P]),
                    "disp_within_t": np.array([dispersion(within_grammar(ep)) for ep in P]),
                    "steps": np.array(r.history["step"])})
    return out


def main():
    base = GPTCore(1, np.random.default_rng(0), MicroGPT.load(BASE_WEIGHTS), "shared").policy_probe(PROBES)
    base_mass = float((base[0] * PMASK).sum(-1).mean())
    jobs = [(c, m, s) for c in ("gpt", "rule") for m in MEDIA for s in range(SEEDS)]
    res = pmap(run, jobs)
    G = {m: [r for r in res if r["core"] == "gpt" and r["medium"] == m] for m in MEDIA}
    R = {m: [r for r in res if r["core"] == "rule" and r["medium"] == m] for m in MEDIA}

    summ = ["## 實驗13（D1 延伸）：分化但守法？可學習螞蟻對控制文法的遵守度", "",
            f"設定：雙橋、30 隻螞蟻、{STEPS} 步、{SEEDS} 個種子；文法 = 規則螞蟻每個感知詞允許的行動集合。", "",
            f"- 行為複製基礎模型在探針上的合法質量 = {base_mass:.4f}", "",
            "| 核心 | 介質 | 實際執行合法率 [95% CI] | 探針合法質量（最終）[95% CI] | 最低單隻螞蟻 | 總分散度 | 文法內分散度 |",
            "|---|---|---|---|---|---|---|"]
    rows = []
    for m in MEDIA:
        for core, S in (("rule", R[m]), ("gpt", G[m])):
            dl = [r["deploy_legal"] for r in S]
            row = {"core": core, "medium": m, "deploy_legal": np.mean(dl), "legal_mass": np.nan,
                   "min_ant_mass": np.nan, "disp": np.nan, "disp_within": np.nan}
            cells = [f"{np.mean(dl):.4f} [{bootstrap_ci(dl)[0]:.4f}, {bootstrap_ci(dl)[1]:.4f}]"]
            if core == "gpt":
                lm = [r["legal_mass_t"][-1] for r in S]
                mn = min(float(r["legal_mass_ants"].min()) for r in S)
                d = [r["disp_t"][-1] for r in S]
                dw = [r["disp_within_t"][-1] for r in S]
                cells += [f"{np.mean(lm):.4f} [{bootstrap_ci(lm)[0]:.4f}, {bootstrap_ci(lm)[1]:.4f}]", f"{mn:.4f}",
                          f"{np.mean(d):.4f}", f"{np.mean(dw):.4f}"]
                row.update({"legal_mass": np.mean(lm), "min_ant_mass": mn, "disp": np.mean(d), "disp_within": np.mean(dw)})
            else:
                cells += ["—", "—", "—", "—"]
            summ.append(f"| {'GPT＋學習' if core == 'gpt' else '規則'} | {m} | " + " | ".join(cells) + " |")
            rows.append(row)
    # 學習是否降低合法質量？（第一個 epoch vs 最後，配對）
    for m in MEDIA:
        d = [r["legal_mass_t"][-1] - r["legal_mass_t"][0] for r in G[m]]
        st = paired_stats(d)
        frac = [r["disp_within_t"][-1] / r["disp_t"][-1] for r in G[m]]
        summ += ["", f"- [{m}] 學習前後合法質量變化 = {st['mean']:+.4f} [{st['ci_lo']:+.4f}, {st['ci_hi']:+.4f}]，p = {st['p']:.3g}；"
                 f"文法內分散度 / 總分散度 = {np.mean(frac):.2f}"]
    dl_s = [r["deploy_legal"] for r in G["shared"]]
    dl_p = [r["deploy_legal"] for r in G["private"]]
    st = paired_stats(np.array(dl_s) - np.array(dl_p))
    summ.append(f"- 實際執行合法率 shared − private（配對）= {st['mean']:+.4f} [{st['ci_lo']:+.4f}, {st['ci_hi']:+.4f}]，p = {st['p']:.3g}")
    save_csv("exp13_grammar.csv", rows)
    save_csv("exp13_per_seed.csv", [{"core": r["core"], "medium": r["medium"], "seed": r["seed"],
                                     "delivered": r["delivered"], "deploy_legal": r["deploy_legal"],
                                     "legal_mass": r["legal_mass_t"][-1] if "disp_t" in r else np.nan,
                                     "disp": r["disp_t"][-1] if "disp_t" in r else np.nan,
                                     "disp_within": r["disp_within_t"][-1] if "disp_t" in r else np.nan}
                                    for r in res])

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6))
    for k, m in enumerate(MEDIA):
        steps = G[m][0]["steps"]
        axes[0].plot(steps, np.mean([r["legal_mass_t"] for r in G[m]], 0), color=SERIES[k], label=m)
        axes[1].plot(steps, np.mean([r["disp_t"] for r in G[m]], 0), color=SERIES[k], label=f"{m}：總分散度")
        axes[1].plot(steps, np.mean([r["disp_within_t"] for r in G[m]], 0), color=SERIES[k], ls="--",
                     label=f"{m}：文法內分散度")
    axes[0].axhline(base_mass, color=INK2, lw=0.8, ls=":", label="基礎模型")
    axes[0].set_ylabel("合法行動上的機率質量"); axes[0].set_title("學習後仍遵守控制文法")
    axes[1].set_ylabel("兩兩平均 JS（nats）"); axes[1].set_title("分化發生在文法允許的空間內")
    for ax in axes:
        ax.set_xlabel("步"); ax.legend(fontsize=8)
    save_fig(fig, "exp13_grammar.png")
    write_summary("exp13", summ)


if __name__ == "__main__":
    main()
