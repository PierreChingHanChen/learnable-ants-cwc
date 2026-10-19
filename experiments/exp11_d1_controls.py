"""
實驗11（D1 的兩個對照）
======================
(a) 社會學習正對照：共享介質下開啟 social=True（每隻螞蟻也模仿他者的成功回合）。
    若分散度指標偵測得到趨同，社會學習應使分散度下降。對照組 = exp9 的共享介質 GPT 螞蟻（同種子，social=False）。
(b) 標記可學習：以「攜帶時只有 50% 機率標記」的教師做行為複製，得到新的基礎模型，
    讓標記行為有被線上學習改變的空間；在共享／私有介質下比較分散度、標記率變化與送達量。
    同條件的規則教師（mark_p = 0.5）作為參考。
"""
import os
import numpy as np

from common import QUICK, pmap, RESULTS, save_csv
from miat_ants.foraging import ForagingSystem, ForagingConfig
from miat_ants.foraging.analysis import make_probes, dispersion
from miat_ants.foraging.system import WEIGHTS_DIR

SEEDS = 2 if QUICK else int(os.environ.get("EXP11_SEEDS", "20"))
STEPS = 1200 if QUICK else 3000
MARK_P = 0.5
W05 = os.path.join(WEIGHTS_DIR, "base_bc_mark05.npz")
PROBES = make_probes(ForagingSystem(ForagingConfig(map_name="double_bridge", core="rule", seed=999,
                                                   max_steps=800, collect_episodes=True)).run().episodes)


def run(args):
    tag, seed = args
    kw = dict(map_name="double_bridge", seed=seed, max_steps=STEPS)
    if tag == "social":
        kw.update(core="gpt", learn=True, social=True, probe_contexts=PROBES)
    elif tag.startswith("mark05_gpt"):
        kw.update(core="gpt", learn=True, base_weights=W05, probe_contexts=PROBES,
                  medium_mode=tag.split("_")[-1])
    else:   # mark05_rule_<medium>
        kw.update(core="rule", rule_mark_p=MARK_P, medium_mode=tag.split("_")[-1])
    r = ForagingSystem(ForagingConfig(**kw)).run()
    h = r.history
    out = {"tag": tag, "seed": seed, "delivered": r.delivered,
           "short_frac": h["gate_short"][-1] / max(1, h["gate_short"][-1] + h["gate_long"][-1]),
           "mark_carry_start": float(np.mean(h["mark_rate_carry"][:4])),
           "mark_carry_end": float(np.mean(h["mark_rate_carry"][-10:]))}
    if r.probes:
        out["dispersion"] = dispersion(r.probes[-1])
        out["dispersion_start"] = dispersion(r.probes[0])
    return out


def main():
    if not os.path.exists(W05):
        from miat_ants.foraging.pretrain import pretrain
        pretrain(n_runs=2 if QUICK else 6, steps=800 if QUICK else 1500, train_steps=600 if QUICK else 3000,
                 out=W05, mark_p=MARK_P)
    tags = ["social", "mark05_gpt_shared", "mark05_gpt_private", "mark05_rule_shared", "mark05_rule_private"]
    jobs = [(t, s) for t in tags for s in range(SEEDS)]
    jobs.sort(key=lambda j: "rule" in j[0])           # 耗時的 GPT 先排
    res = pmap(run, jobs)
    keys = ["tag", "seed", "delivered", "short_frac", "mark_carry_start", "mark_carry_end", "dispersion", "dispersion_start"]
    save_csv("exp11_per_seed.csv", [{k: r.get(k, np.nan) for k in keys} for r in res])
    print("saved", len(res))


if __name__ == "__main__":
    main()
