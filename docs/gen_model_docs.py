"""由程式中的 GRAFCET 模型自動產生狀態表與 Mermaid 圖（模型為 single source of truth）。

用法：python docs/gen_model_docs.py  → 產生 docs/zh-TW/GRAFCET_MODELS.md
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from miat_ants.tsp import AntTSPSystem, AntTSPConfig, grid_cities
from miat_ants.sorting import AntSortSystem, AntSortConfig
from miat_ants.foraging import ForagingSystem, ForagingConfig


def section(title, g):
    issues = g.validate()
    return "\n".join([
        f"### {title}（{g.name}，IDEF0 {g.idef0}，n={g.n}）", "",
        f"Gate 2 模型審查：{'通過' if not issues else '未通過 ' + str(issues)}", "",
        g.state_table(), "",
        "```mermaid", g.to_mermaid(), "```", ""])


def main():
    tsp = AntTSPSystem(grid_cities(), AntTSPConfig())
    srt = AntSortSystem(AntSortConfig())
    fg = ForagingSystem(ForagingConfig())
    out = ["# GRAFCET 模型（自動產生，請勿手改）", "",
           "[English](../en/GRAFCET_MODELS.md) | 中文", "",
           "由 `docs/gen_model_docs.py` 從程式中的模型定義產生。修改行為時請改模型定義，再重新產生本檔。", "",
           "## 螞蟻–TSP 最佳化系統", "",
           section("主控制器", tsp.g0), section("巡迴建構子控制器", tsp.g2),
           "## 螞蟻–自動分揀系統", "",
           section("主控制器", srt.g0), section("族群控制器（每隻螞蟻一個同構控制器）", srt.g2),
           "## microGPT 螞蟻覓食系統", "",
           section("感覺運動時脈", fg.g0), section("任務意向（族群控制器）", fg.g2)]
    path = os.path.join(HERE, "zh-TW", "GRAFCET_MODELS.md")  # English version: docs/en/GRAFCET_MODELS.md (translated)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote", path)


if __name__ == "__main__":
    main()
