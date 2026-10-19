"""
擴充範例（主題一）：以自訂策略取代式(1)，作為日後接入 LLM 代理人的範本。

這裡示範兩種策略：
  greedy_follower : 只跟隨費洛蒙最強的邊（純從眾，無探索）
  llm_stub        : LLM 代理人的介面樣板——把「觀察」轉成文字提示，
                    再把回覆解析成下一城市。此處以規則模擬回覆，未呼叫任何 API。
"""
import numpy as np

from common import save_csv
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities


def greedy_follower(agent, cur, allowed, tau_row, eta_row, rng):
    w = np.where(allowed, tau_row, -np.inf)
    return int(np.argmax(w))


def llm_stub(agent, cur, allowed, tau_row, eta_row, rng):
    cand = np.flatnonzero(allowed)
    top = cand[np.argsort(-(tau_row[cand] * eta_row[cand] ** 2))[:5]]
    prompt = (f"你是第 {agent} 號代理人，位於城市 {cur}。候選城市與（費洛蒙, 1/距離）："
              + "; ".join(f"{j}:({tau_row[j]:.2f},{eta_row[j]:.3f})" for j in top)
              + "。請只回覆一個城市編號。")
    reply = str(top[0]) if rng.random() < 0.8 else str(rng.choice(top))   # ← 在此替換為真正的 LLM 呼叫
    j = int(reply.strip())
    return j if allowed[j] else int(top[0])


if __name__ == "__main__":
    coords = random_cities(30, seed=30)
    rows = []
    for name, pol in (("Ant System 式(1)", None), ("greedy_follower", greedy_follower), ("llm_stub", llm_stub)):
        r = AntTSPSystem(coords, AntTSPConfig(n_ants=20, max_cycles=40, seed=0, policy=pol,
                                              track_provenance=False)).run()
        rows.append({"policy": name, "best": r.best_length, "consensus": r.history["consensus"][-1]})
        print(f"{name:20s} best={r.best_length:.1f}  consensus={r.history['consensus'][-1]:.3f}")
    save_csv("example_custom_policy.csv", rows)
