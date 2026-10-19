"""Fig. 4F 的零假設：同一段歷史分岔成 封鎖支(rs1)、對照支(rs1)、對照支(rs2)；
比較 個體策略 JS(封鎖 vs 對照) 與 JS(對照 vs 對照′)（純隨機分歧）。"""
import numpy as np
from common import QUICK, pmap, RESULTS
from fig_data import ev, PROBES, STEPS, T1, T2
from miat_ants.foraging import ForagingSystem, ForagingConfig
from miat_ants.foraging.analysis import js

SEEDS = 2 if QUICK else 10


def one(seed):
    base = ForagingSystem(ForagingConfig(map_name="double_bridge", core="gpt", learn=True, seed=seed,
                                         max_steps=STEPS)).run_until(T1)
    rs1, rs2 = ev("reseed", T1, seed=31_337 * (seed + 1)), ev("reseed", T1, seed=77_777 * (seed + 1))
    b = base.fork(events_now=[rs1, ev("block_gate", T1, gate="short")],
                  perturbations=[ev("unblock_gate", T2, gate="short")]).resume()
    c1 = base.fork(events_now=[rs1]).resume()
    c2 = base.fork(events_now=[rs2]).resume()
    P = {k: r.core.policy_probe(PROBES) for k, r in (("b", b), ("c1", c1), ("c2", c2))}
    return {"seed": seed, "js_bc": js(P["b"], P["c1"]).mean(-1), "js_cc": js(P["c1"], P["c2"]).mean(-1),
            "js_bc2": js(P["b"], P["c2"]).mean(-1)}


if __name__ == "__main__":
    res = pmap(one, range(SEEDS))
    np.save(f"{RESULTS}/fig_data_null.npy", res, allow_pickle=True)
    print("saved", len(res))
