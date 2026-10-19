"""
螞蟻–自動分揀 的 Action／Datapath（純函式）
==========================================

原論文式(6)(7)(8) 的方程式物件已無法自 .doc 擷取，依論文文字與其引用之
Deneubourg et al. (1991) 及 Lumer & Faieta (1994) 重建：

  (6) p_pick(o_i)    = ( k1 / (k1 + f(o_i)) )²
  (7) p_deposit(o_i) = ( f(o_i) / (k2 + f(o_i)) )²
  (8) f(o_i) = max( 0, (1/s²) · Σ_{o_j ∈ Neigh(x)} [ 1 − d(o_i, o_j) / a ] )

  s² 為鄰域格數（不含中心），d 為差異度（同類 0、異類 1），a 為差異尺度。
  a = 1 時 f 即「鄰域中同類物資所占比率」，與論文文字「與周圍物資的同質性
  成正比」一致。a < 1 時異類鄰居會扣分（Lumer–Faieta 形式）。
"""
from __future__ import annotations

from typing import Tuple

import numpy as np

# 8 個方向：E, W, S, N, EN, WN, ES, WS（論文虛擬碼）
DIRS = np.array([(0, 1), (0, -1), (1, 0), (-1, 0), (-1, 1), (-1, -1), (1, 1), (1, -1)])


def place_objects(H: int, W: int, n_types: int, n_per_type: int,
                  rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
    """A11 隨機把物資放在網格上（一格最多一個）。
    Output: type_grid (H,W) int, -1 為空；id_grid (H,W) int, -1 為空。"""
    total = n_types * n_per_type
    if total > H * W:
        raise ValueError("物資數超過格子數")
    cells = rng.choice(H * W, size=total, replace=False)
    type_grid = -np.ones(H * W, dtype=int)
    id_grid = -np.ones(H * W, dtype=int)
    type_grid[cells] = np.repeat(np.arange(n_types), n_per_type)
    id_grid[cells] = np.arange(total)
    return type_grid.reshape(H, W), id_grid.reshape(H, W)


def place_ants(H: int, W: int, n_ants: int, rng: np.random.Generator) -> np.ndarray:
    """A12 隨機放置螞蟻。Output: (n_ants, 2) int 座標。"""
    return np.stack([rng.integers(0, H, n_ants), rng.integers(0, W, n_ants)], axis=1)


def neighbor_type_counts(type_grid: np.ndarray, n_types: int, radius: int = 1) -> np.ndarray:
    """回傳 (n_types, H, W)：每一格鄰域（不含自身，環面邊界）內各類物資數。"""
    H, W = type_grid.shape
    out = np.zeros((n_types, H, W), dtype=float)
    onehot = np.stack([(type_grid == t).astype(float) for t in range(n_types)])
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if dr == 0 and dc == 0:
                continue
            out += np.roll(np.roll(onehot, dr, axis=1), dc, axis=2)
    return out


def local_density(obj_type: np.ndarray, pos: np.ndarray, counts: np.ndarray,
                  radius: int = 1, a: float = 1.0) -> np.ndarray:
    """式(8)：對每隻螞蟻在 pos 處、針對物資類別 obj_type 計算 f。
    Input: obj_type (m,), pos (m,2), counts (n_types,H,W)；Output: f (m,) ∈ [0,1]。"""
    s2 = (2 * radius + 1) ** 2 - 1
    r, c = pos[:, 0], pos[:, 1]
    same = counts[obj_type, r, c]
    total = counts[:, r, c].sum(axis=0)
    diff = total - same
    f = (same * 1.0 + diff * (1.0 - 1.0 / a)) / s2     # d=0 → 1；d=1 → 1-1/a
    return np.clip(f, 0.0, 1.0)


def p_pick(f: np.ndarray, k1: float) -> np.ndarray:
    """式(6)。"""
    return (k1 / (k1 + f)) ** 2


def p_deposit(f: np.ndarray, k2: float) -> np.ndarray:
    """式(7)。"""
    return (f / (k2 + f)) ** 2


def random_moves(pos: np.ndarray, speed: np.ndarray, H: int, W: int,
                 rng: np.random.Generator) -> np.ndarray:
    """A21 隨機往 8 方向之一移動 speed 格（環面邊界）。"""
    d = DIRS[rng.integers(0, 8, size=len(pos))] * speed[:, None]
    new = pos + d
    new[:, 0] %= H
    new[:, 1] %= W
    return new


def arbitrate(cells: np.ndarray, want: np.ndarray) -> Tuple[np.ndarray, int]:
    """同一格的多隻螞蟻同時想拿起／放下：以 ant index 最小者優先（明確仲裁規則）。
    Input: cells (m,2)，want (m,) bool；Output: granted (m,) bool, 衝突次數。"""
    granted = np.zeros_like(want)
    seen = set()
    conflicts = 0
    for k in np.flatnonzero(want):
        key = (int(cells[k, 0]), int(cells[k, 1]))
        if key in seen:
            conflicts += 1
            continue
        seen.add(key)
        granted[k] = True
    return granted, conflicts
