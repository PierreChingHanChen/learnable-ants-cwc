"""
A1 問題定義（TSP 實例）
======================
Input  : 城市座標（滑鼠輸入／檔案／產生器）
Output : coords (n,2) float 陣列
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np


def grid_cities(rows: int = 5, cols: int = 5, spacing: float = 1.0) -> np.ndarray:
    """原論文實驗用的 5×5 網格地圖。

    已知最佳解：rows*cols 為奇數時 = (rows*cols - 1)*spacing + √2*spacing
    （5×5、spacing=1 → 24 + √2 ≈ 25.414），可用來驗證演算法正確性。
    """
    return np.array([(c * spacing, r * spacing) for r in range(rows) for c in range(cols)], dtype=float)


def grid_optimum(rows: int = 5, cols: int = 5, spacing: float = 1.0) -> float:
    n = rows * cols
    return (n * spacing) if n % 2 == 0 else ((n - 1) * spacing + math.sqrt(2) * spacing)


def random_cities(n: int = 42, seed: int = 42, size: float = 100.0) -> np.ndarray:
    """可重現的隨機城市（原論文 42 城市座標已不可得，以固定亂數種子替代）。"""
    rng = np.random.default_rng(seed)
    return rng.uniform(0, size, size=(n, 2))


def load_tsplib(path: str) -> np.ndarray:
    """讀取 TSPLIB 格式（NODE_COORD_SECTION, EUC_2D）。可載入 dantzig42 等標準實例。"""
    coords = []
    with open(path, encoding="utf-8") as f:
        reading = False
        for line in f:
            s = line.strip()
            if s.startswith("NODE_COORD_SECTION"):
                reading = True
                continue
            if s in ("EOF", "") or not reading:
                continue
            parts = s.split()
            if len(parts) >= 3:
                coords.append((float(parts[1]), float(parts[2])))
    return np.array(coords, dtype=float)
