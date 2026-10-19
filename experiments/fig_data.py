"""
產生主圖所需、先前未存檔的時間序列資料 → results/fig_data.npz
  (1) 雙橋上三種核心的累積送達曲線（5 個種子）＋一張學習型蟻群的費洛蒙快照
  (2) 封鎖／解封短橋的配對分岔（每個種子：同一段歷史在第 T1 步分成「封鎖→解封」與「不封鎖」兩支）
      GPT 螞蟻另量測兩支結尾時每隻螞蟻策略的 JS 距離（個體是否帶著改變回來）
"""
import numpy as np

from common import QUICK, pmap, RESULTS
from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.foraging import ForagingSystem, ForagingConfig
from miat_ants.foraging.analysis import make_probes, js

import os
SEEDS_CURVE = 2 if QUICK else int(os.environ.get("FIG_SEEDS_CURVE", "20"))
SEEDS_BLOCK = 2 if QUICK else int(os.environ.get("FIG_SEEDS_BLOCK", "0"))   # exp12 取代
STEPS = 1200 if QUICK else 3000
T1, T2 = (400, 800) if QUICK else (1000, 2000)
PROBES = make_probes(ForagingSystem(ForagingConfig(map_name="double_bridge", core="rule", seed=999,
                                                   max_steps=800, collect_episodes=True)).run().episodes)


def curve(args):
    tag, seed = args
    kw = {"rule": dict(core="rule"), "gpt_bc": dict(core="gpt", learn=False),
          "gpt_learn": dict(core="gpt", learn=True)}[tag]
    r = ForagingSystem(ForagingConfig(map_name="double_bridge", seed=seed, max_steps=STEPS, **kw)).run()
    out = {"tag": tag, "seed": seed, "step": np.array(r.history["step"]),
           "delivered": np.array(r.history["delivered"])}
    if tag == "gpt_learn" and seed == 0:
        out["tau"] = r.world.medium.snapshot().copy()
        out["walls"] = r.world.spec.walls.copy()
        out["nest"] = r.world.spec.nest.copy()
        out["food"] = (r.world.spec.food > 0)
    return out


def ev(kind, t, **p):
    return Event(kind, t, "experiment", p, PRIORITY_ENV, "interrupt")


def gate_series(h):
    gs, gl = np.diff([0] + h["gate_short"]), np.diff([0] + h["gate_long"])
    return gs / np.maximum(gs + gl, 1), gs + gl


def block(args):
    core, seed = args
    base = ForagingSystem(ForagingConfig(map_name="double_bridge", core=core, learn=True, seed=seed,
                                         max_steps=STEPS)).run_until(T1)
    rs = ev("reseed", T1, seed=31_337 * (seed + 1))
    rb = base.fork(events_now=[rs, ev("block_gate", T1, gate="short")],
                   perturbations=[ev("unblock_gate", T2, gate="short")]).resume()
    rc = base.fork(events_now=[rs]).resume()
    out = {"core": core, "seed": seed, "step": np.array(rb.history["step"])}
    for name, r in (("blocked", rb), ("control", rc)):
        f, n = gate_series(r.history)
        out[f"{name}_frac"], out[f"{name}_n"] = f, n
        out[f"{name}_delivered"] = np.array(r.history["delivered"])
    if core == "gpt":
        pb, pc = rb.core.policy_probe(PROBES), rc.core.policy_probe(PROBES)
        out["ant_js"] = js(pb, pc).mean(-1)                       # (A,) 每隻螞蟻兩支之間的平均 JS
        out["ant_js_null"] = js(pc, base.core.policy_probe(PROBES)).mean(-1)   # 參考：對照支相對分岔點的漂移
    return out


def main():
    cj = [(t, s) for t in ("rule", "gpt_bc", "gpt_learn") for s in range(SEEDS_CURVE)]
    bj = [(c, s) for c in ("gpt", "rule") for s in range(SEEDS_BLOCK)]
    res = pmap(lambda_free, [("c", j) for j in cj] + [("b", j) for j in bj])
    curves = [r for k, r in res if k == "c"]
    blocks = [r for k, r in res if k == "b"]
    np.save(f"{RESULTS}/fig_data.npy", {"curves": curves, "blocks": blocks, "T1": T1, "T2": T2}, allow_pickle=True)
    print("saved", len(curves), len(blocks))


def lambda_free(x):
    k, j = x
    return k, (curve(j) if k == "c" else block(j))


if __name__ == "__main__":
    main()
