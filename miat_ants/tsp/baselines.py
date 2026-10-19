"""
比較基準：模擬退火（SA）與遺傳演算法（GA）
==========================================
原論文表 1 比較 ACO / SA / GA。原始實作已不可得，此處為重新實作的標準版本，
參數取常見預設值，並讓三者使用相近的評估次數預算（見 experiments/exp_tsp_compare.py）。
"""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from .actions import distance_matrix, tour_length


def simulated_annealing(coords: np.ndarray, n_evals: int = 250_000, T0: float = None,
                        T_end: float = 1e-3, seed: int = None) -> Tuple[List[int], float]:
    """2-opt 反轉鄰域 + 幾何降溫。"""
    rng = np.random.default_rng(seed)
    D = distance_matrix(coords)
    n = len(coords)
    tour = list(rng.permutation(n))
    L = tour_length(tour, D)
    if T0 is None:
        T0 = D.mean()
    alpha = (T_end / T0) ** (1.0 / n_evals)
    T = T0
    best, bestL = tour[:], L
    for _ in range(n_evals):
        i, j = sorted(rng.choice(n, 2, replace=False))
        if j - i < 1 or (i == 0 and j == n - 1):
            T *= alpha
            continue
        a, b = tour[i - 1], tour[i]
        c, d = tour[j], tour[(j + 1) % n]
        delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]
        if delta < 0 or rng.random() < math.exp(-delta / T):
            tour[i:j + 1] = tour[i:j + 1][::-1]
            L += delta
            if L < bestL:
                best, bestL = tour[:], L
        T *= alpha
    return [int(x) for x in best], float(tour_length(best, D))


def _ox(p1: np.ndarray, p2: np.ndarray, rng) -> np.ndarray:
    """Order crossover (OX)。"""
    n = len(p1)
    i, j = sorted(rng.choice(n, 2, replace=False))
    child = -np.ones(n, dtype=int)
    child[i:j + 1] = p1[i:j + 1]
    used = set(child[i:j + 1].tolist())
    fill = [g for g in p2 if g not in used]
    idx = [k for k in range(n) if child[k] < 0]
    child[idx] = fill
    return child


def genetic_algorithm(coords: np.ndarray, pop: int = 100, generations: int = 2500,
                      p_mut: float = 0.2, elite: int = 2, tour_k: int = 3,
                      seed: int = None) -> Tuple[List[int], float]:
    """錦標賽選擇 + OX 交配 + 反轉突變 + 菁英保留。"""
    rng = np.random.default_rng(seed)
    D = distance_matrix(coords)
    n = len(coords)
    P = np.array([rng.permutation(n) for _ in range(pop)])
    fit = np.array([tour_length(t, D) for t in P])
    for _ in range(generations):
        order = np.argsort(fit)
        newP = [P[k].copy() for k in order[:elite]]
        while len(newP) < pop:
            par = []
            for _ in range(2):
                cand = rng.choice(pop, tour_k, replace=False)
                par.append(P[cand[np.argmin(fit[cand])]])
            child = _ox(par[0], par[1], rng)
            if rng.random() < p_mut:
                i, j = sorted(rng.choice(n, 2, replace=False))
                child[i:j + 1] = child[i:j + 1][::-1]
            newP.append(child)
        P = np.array(newP)
        fit = np.array([tour_length(t, D) for t in P])
    k = int(np.argmin(fit))
    return [int(x) for x in P[k]], float(fit[k])
