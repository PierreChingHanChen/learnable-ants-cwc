"""
實驗12（D3・可學習螞蟻）：恢復而不回歸——配對分岔的封鎖／解封實驗
================================================================
每個種子：學習 T1 步後暫停並複製完整狀態，分成三支：
  B  ：同一重設種子 rs1，封鎖短橋至 T2 後解封
  C1 ：同一重設種子 rs1，不封鎖（配對對照）
  C2 ：另一重設種子 rs2，不封鎖（純隨機分歧的基準）
量測（解封後 T2+100 至結束）：
  * 短橋比例差  B − C1
  * 解封後送達量差 B − C1（並以 C2 − C1 的自然變異為參考）
  * 每隻螞蟻策略在 96 個探針上下文上的 JS：JS(B, C1) vs JS(C1, C2)（GPT 螞蟻）
規則螞蟻以相同流程作為對照（無個體學習狀態）。
"""
import os
import numpy as np

from common import QUICK, pmap, RESULTS, paired_stats, bootstrap_ci, write_summary, save_csv
from miat_ants.core.events import Event, PRIORITY_ENV
from miat_ants.foraging import ForagingSystem, ForagingConfig
from miat_ants.foraging.analysis import make_probes, js

SEEDS = 2 if QUICK else int(os.environ.get("EXP12_SEEDS", "20"))
STEPS = 1200 if QUICK else 3000
T1, T2 = (400, 800) if QUICK else (1000, 2000)
PROBES = make_probes(ForagingSystem(ForagingConfig(map_name="double_bridge", core="rule", seed=999,
                                                   max_steps=800, collect_episodes=True)).run().episodes)


def ev(kind, t, **p):
    return Event(kind, t, "experiment", p, PRIORITY_ENV, "interrupt")


def gate_series(h):
    gs, gl = np.diff([0] + h["gate_short"]), np.diff([0] + h["gate_long"])
    return gs / np.maximum(gs + gl, 1), gs + gl


def one(args):
    core, seed = args
    base = ForagingSystem(ForagingConfig(map_name="double_bridge", core=core, learn=True, seed=seed,
                                         max_steps=STEPS)).run_until(T1)
    rs1, rs2 = ev("reseed", T1, seed=31_337 * (seed + 1)), ev("reseed", T1, seed=77_777 * (seed + 1))
    rb = base.fork(events_now=[rs1, ev("block_gate", T1, gate="short")],
                   perturbations=[ev("unblock_gate", T2, gate="short")]).resume()
    rc = base.fork(events_now=[rs1]).resume()
    rc2 = base.fork(events_now=[rs2]).resume()
    out = {"core": core, "seed": seed, "step": np.array(rb.history["step"])}
    for name, r in (("blocked", rb), ("control", rc), ("control2", rc2)):
        f, n = gate_series(r.history)
        out[f"{name}_frac"], out[f"{name}_n"] = f, n
        out[f"{name}_delivered"] = np.array(r.history["delivered"])
    if core == "gpt":
        P = {k: r.core.policy_probe(PROBES) for k, r in (("b", rb), ("c1", rc), ("c2", rc2))}
        out["js_bc"] = js(P["b"], P["c1"]).mean(-1)
        out["js_cc"] = js(P["c1"], P["c2"]).mean(-1)
        out["js_bc2"] = js(P["b"], P["c2"]).mean(-1)
    return out


def fmt(st, nd=3):
    return f"{st['mean']:+.{nd}f} [{st['ci_lo']:+.{nd}f}, {st['ci_hi']:+.{nd}f}]，d_z = {st['d_z']:+.2f}，p = {st['p']:.3g}"


def main():
    res = pmap(one, [(c, s) for c in ("gpt", "rule") for s in range(SEEDS)])
    np.save(os.path.join(RESULTS, "exp12.npy"), {"blocks": res, "T1": T1, "T2": T2}, allow_pickle=True)
    summ = ["## 實驗12（D3・可學習螞蟻）：恢復而不回歸——配對分岔", "",
            f"設定：雙橋、30 隻螞蟻；學習 {T1} 步後分岔；封鎖短橋 {T1}–{T2} 步；執行至 {STEPS} 步；{SEEDS} 個種子。", ""]
    rows = []
    for core in ("gpt", "rule"):
        R = [r for r in res if r["core"] == core]
        stp = R[0]["step"]
        post = lambda r, n: r[f"{n}_frac"][stp > T2 + 100].mean()
        i2 = int(np.searchsorted(stp, T2))
        dlv = lambda r, n: r[f"{n}_delivered"][-1] - r[f"{n}_delivered"][i2]
        sd = paired_stats([post(r, "blocked") - post(r, "control") for r in R])
        sn = paired_stats([post(r, "control2") - post(r, "control") for r in R])
        dd = paired_stats([dlv(r, "blocked") - dlv(r, "control") for r in R])
        dn = [dlv(r, "control2") - dlv(r, "control") for r in R]
        base_dlv = np.mean([dlv(r, "control") for r in R])
        lab = "GPT 螞蟻" if core == "gpt" else "規則螞蟻"
        summ += [f"### {lab}", "",
                 f"- 解封後短橋比例：對照 {np.mean([post(r, 'control') for r in R]):.3f}，封鎖支 {np.mean([post(r, 'blocked') for r in R]):.3f}",
                 f"- 短橋比例差（封鎖 − 對照）= {fmt(sd)}",
                 f"- 參考：兩個未封鎖分支之差（C2 − C1）= {fmt(sn)}",
                 f"- 解封後送達量：對照 {base_dlv:.1f}；差（封鎖 − 對照）= {fmt(dd, 1)}",
                 f"- 自然變異 |C2 − C1| 平均 = {np.mean(np.abs(dn)):.1f}；"
                 f"送達量差相對對照 = {100 * dd['mean'] / base_dlv:+.1f}%（95% CI {100 * dd['ci_lo'] / base_dlv:+.1f}% 至 {100 * dd['ci_hi'] / base_dlv:+.1f}%）"]
        rows.append({"core": core, "metric": "short_frac_diff", **sd})
        rows.append({"core": core, "metric": "delivered_diff", **dd})
        if core == "gpt":
            bc = np.array([r["js_bc"].mean() for r in R]); cc = np.array([r["js_cc"].mean() for r in R])
            bc2 = np.array([r["js_bc2"].mean() for r in R])
            s1 = paired_stats(bc - cc); s2 = paired_stats(bc2 - cc)
            frac_up = np.mean([(r["js_bc"] > r["js_cc"]).mean() for r in R])
            summ += [f"- 每隻螞蟻策略 JS：封鎖 vs 對照 = {bc.mean():.4f}，兩個對照之間 = {cc.mean():.4f}（nats）",
                     f"- 配對差 JS(B,C1) − JS(C1,C2) = {fmt(s1, 4)}；以 C2 為對照時 = {fmt(s2, 4)}",
                     f"- 每個種子中 JS(B,C1) > JS(C1,C2) 的螞蟻比例平均 = {frac_up:.2f}",
                     f"- 種子層級方向一致：{int((bc > cc).sum())}/{len(bc)} 個種子"]
            rows.append({"core": core, "metric": "js_excess", **s1})
            rows.append({"core": core, "metric": "js_excess_alt", **s2})
        summ.append("")
    save_csv("exp12_stats.csv", rows)
    write_summary("exp12", summ)


if __name__ == "__main__":
    main()
