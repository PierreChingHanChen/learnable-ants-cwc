"""
螞蟻–TSP 的 Action／Datapath（純函式，無隱藏 global state）
==========================================================

每個函式對應一個 IDEF0 原子模組，都有明確的 Input／Output 契約，可獨立測試。
公式編號對應原論文《仿螞蟻行為的群體解題系統》。

注意：原論文 .doc 中的方程式物件已無法擷取，以下依論文文字描述與其引用之
Dorigo, Maniezzo & Colorni (1996) Ant System（ant-cycle）重建：

  (1) p_ij^k(t) = [τ_ij(t)]^α [η_ij]^β / Σ_{l∈allowed_k} [τ_il(t)]^α [η_il]^β ,  j ∈ allowed_k
  (2) η_ij = 1 / d_ij
  (3) τ_ij(t+n) = ρ · τ_ij(t) + Δτ_ij          （ρ：殘留係數）
  (4) Δτ_ij = Σ_k Δτ_ij^k
  (5) Δτ_ij^k = Q / L_k  若 ant k 的巡迴經過 (i,j)，否則 0
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------- A11 / A12
def distance_matrix(coords: np.ndarray) -> np.ndarray:
    """A11 計算城市距離。Input: (n,2) 座標；Output: (n,n) 歐氏距離，對角為 0。"""
    diff = coords[:, None, :] - coords[None, :, :]
    return np.sqrt((diff ** 2).sum(-1))


def visibility(D: np.ndarray) -> np.ndarray:
    """A12 能見度矩陣，式(2) η_ij = 1/d_ij。對角設 0。"""
    with np.errstate(divide="ignore"):
        eta = np.where(D > 0, 1.0 / D, 0.0)
    np.fill_diagonal(eta, 0.0)
    return eta


# ---------------------------------------------------------------- A21
def place_ants(n_ants: int, n_cities: int, rng: np.random.Generator) -> np.ndarray:
    """A21 將 m 隻螞蟻隨機放在 n 個城市上（步驟一）。Output: (m,) 起始城市。"""
    return rng.integers(0, n_cities, size=n_ants)


# ---------------------------------------------------------------- A22
def transition_probabilities(tau_row: np.ndarray, eta_row: np.ndarray,
                             allowed: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """式(1)：回傳長度 n 的機率向量；不允許的城市（tabu）機率為 0。"""
    w = np.where(allowed, (tau_row ** alpha) * (eta_row ** beta), 0.0)
    s = w.sum()
    if s <= 0 or not np.isfinite(s):          # 數值退化時退回均勻分布
        w = allowed.astype(float)
        s = w.sum()
    return w / s


def choose_next(cur: int, visited: np.ndarray, tau: np.ndarray, eta: np.ndarray,
                alpha: float, beta: float, rng: np.random.Generator) -> int:
    """A22 依式(1) 與限制表(tabu list) 擇一下一城市。"""
    allowed = ~visited
    p = transition_probabilities(tau[cur], eta[cur], allowed, alpha, beta)
    return int(rng.choice(len(p), p=p))


# ---------------------------------------------------------------- A3
def tour_length(tour: Sequence[int], D: np.ndarray) -> float:
    """A31 巡迴總長（含回到起點）。"""
    t = np.asarray(tour)
    return float(D[t, np.roll(t, -1)].sum())


def tour_edge_list(tour: Sequence[int]) -> List[Tuple[int, int]]:
    t = list(tour)
    return [(t[k], t[(k + 1) % len(t)]) for k in range(len(t))]


def is_valid_tour(tour: Sequence[int], n: int) -> bool:
    return len(tour) == n and set(tour) == set(range(n))


# ---------------------------------------------------------------- A4
def deposit_amount(Q: float, L: float) -> float:
    """式(5)：Δτ^k = Q / L_k。"""
    return Q / L


# ---------------------------------------------------------------- 研究用輔助
def greedy_medium_tour(tau: np.ndarray, start: int = 0) -> List[int]:
    """「介質中的集體記憶」所指向的巡迴：從 start 出發，每步走費洛蒙最強的未訪邊。
    用來觀察群體（而非任何個體或存檔）目前「相信」的路徑。"""
    n = tau.shape[0]
    visited = np.zeros(n, dtype=bool)
    tour = [start]
    visited[start] = True
    for _ in range(n - 1):
        row = np.where(visited, -np.inf, tau[tour[-1]])
        j = int(np.argmax(row))
        tour.append(j)
        visited[j] = True
    return tour


def two_opt(tour: Sequence[int], D: np.ndarray, max_rounds: int = 1000) -> List[int]:
    """2-opt 局部搜尋（first-improvement），用來取得強參考解。"""
    t = list(tour)
    n = len(t)
    for _ in range(max_rounds):
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = t[i - 1], t[i]
                c, d = t[j], t[(j + 1) % n]
                if D[a, c] + D[b, d] < D[a, b] + D[c, d] - 1e-12:
                    t[i:j + 1] = t[i:j + 1][::-1]
                    improved = True
        if not improved:
            break
    return t
