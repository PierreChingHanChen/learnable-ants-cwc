[English](README.md) | 中文

# 可學習螞蟻：協調而不趨同

本儲存庫收錄〈**Coordination without convergence: Three decouplings in learnable ant collectives**〉（陳慶瀚，國立中央大學）研究的程式碼、資料與圖表。

AI 代理人系統愈來愈常透過「留在共享記憶中的東西」彼此協調，而不是直接互傳訊息。本研究以「可學習螞蟻」檢驗這類系統治理背後的三個假設。每隻可學習螞蟻的決策核心是一個 4096 參數的 transformer：它把感知與行動寫成同一條交錯的詞元序列，持續從自己成功的回合中學習，並且只透過費洛蒙介質與其他螞蟻互動。

| 脫鉤 | 受檢驗的假設 | 結果 |
|---|---|---|
| D1 協調而不趨同 | 協調需要代理人彼此趨同 | 共享介質讓蟻群產量提高為 1.57 倍，個體間策略分散度卻沒有下降；社會學習讓螞蟻幾乎一模一樣，產量卻沒有提高。大部分分化仍落在螞蟻所學的控制文法之內。 |
| D2 痕跡誇大了責任的集中程度 | 「誰寫了什麼」的紀錄能定位責任 | 留下最多痕跡的四分之一螞蟻占痕跡的 40%，Shapley 值卻只占 31%；沒有任何單一螞蟻是必要的；蟻群產出比各部分單獨產出的總和多 30%。這些結果已在新種子上以事前指定的檢定重現。 |
| D3 恢復而不回歸 | 恢復就是回到原本狀態 | 擾動後群體表現恢復了，存檔的解與個體策略卻沒有回到原狀。 |

論文目前審稿中。正式發表後，會在此補上引用資訊與存檔版本的 DOI。

## 內容

```
miat_ants/            模擬平台（Python + numpy）
  core/               GRAFCET 引擎、事件契約、具來源追蹤的共享介質、指標
  tsp/                旅行推銷員問題的 Ant System（含 SA／GA 基準）
  sorting/            螞蟻物資分揀
  microgpt/           numpy 版 transformer（約 4 千參數、多代理人批次、手寫梯度、Adam）
  foraging/           可學習螞蟻覓食：詞彙、世界、規則／GPT 核心、系統、預訓練
    weights/          行為複製的基礎模型（base_bc、base_bc_mark05）
experiments/          每個實驗一支腳本（exp1–exp13），以及分析與繪圖腳本
results/              論文使用的逐種子結果（CSV／NPY／NPZ）
figures/              實驗腳本輸出的探索性圖表
figures/paper/       論文圖：Fig1–Fig5 與 FigS1–FigS6（PDF + PNG）
tests/                51 項自動化測試（模型、Controller、Action、整合）
docs/en/、docs/zh-TW/ 英文與繁體中文文件
run_all.py            依序執行全部實驗與繪圖腳本
```

## 安裝

需要 Python 3.10 以上（已在 Python 3.13 測試）。

```bash
pip install -r requirements.txt
python -m pytest -q          # 51 項測試，約 15 秒
```

## 快速開始

由已存的結果重新繪製所有論文圖（約一分鐘）：

```bash
python experiments/make_figures.py        # Fig. 1–5  → figures/paper/
python experiments/make_supp_figures.py   # figs. S1–S6 → figures/paper/
```

以論文設定執行單一實驗，例如配對分岔的回歸實驗（這會以你自己的執行結果取代已存的 `results/exp12*` 檔）：

```bash
python run_all.py exp12
```

以極小樣本快速檢查整條流程。這會用低樣本數的結果**覆寫 `results/` 與 `figures/`**，請在另一份副本中執行，或事後以 `git checkout -- results figures` 還原：

```bash
QUICK=1 python run_all.py
```

完整執行（`python run_all.py`）在雙核心 CPU 上需要數小時。每個步驟的設定、輸出，以及它產生論文中的哪張圖或哪個表，請見 [docs/zh-TW/EXPERIMENTS.md](docs/zh-TW/EXPERIMENTS.md)。

## 文件

| 文件 | 內容 |
|---|---|
| [EXPERIMENTS.md](docs/zh-TW/EXPERIMENTS.md) | 如何重現每個結果；論文圖表與腳本、資料的對照 |
| [RESULTS.md](docs/zh-TW/RESULTS.md) | 各實驗結果整理 |
| [DATA_DICTIONARY.md](docs/zh-TW/DATA_DICTIONARY.md) | `results/` 中每個檔案的欄位與意義 |
| [DESIGN.md](docs/zh-TW/DESIGN.md) | 平台的 MIAT 2.0 設計：需求、IDEF0、事件契約、Traceability |
| [DESIGN_microgpt_ants.md](docs/zh-TW/DESIGN_microgpt_ants.md) | 可學習螞蟻（microGPT）子系統的設計 |
| [GRAFCET_MODELS.md](docs/zh-TW/GRAFCET_MODELS.md) | 所有 GRAFCET 控制器的狀態表與圖 |

每份文件都有英文版，位於 [docs/en/](docs/en/)。程式註解、docstring，以及腳本寫入 `results/summary_*.md` 的文字摘要都是繁體中文。

## 使用平台

### 分岔蟻群以做配對反事實

`ForagingSystem` 可以在 epoch 邊界暫停，並複製完整狀態（位置、攜帶狀態、費洛蒙場、每隻螞蟻的權重與最佳化器狀態、控制器狀態、亂數產生器），讓不同的未來共享同一段歷史（這個範例約需一分鐘）：

```python
from miat_ants.core.events import Event
from miat_ants.foraging import ForagingSystem, ForagingConfig

s = ForagingSystem(ForagingConfig(core="gpt", track_provenance=True, max_steps=3000, seed=0)).run_until(2000)
full = s.fork(events_now=[Event("reseed", 2000, "experiment", {"seed": 1})]).resume()
cut = s.fork(events_now=[Event("reseed", 2000, "experiment", {"seed": 1}),
                         Event("remove_ants", 2000, "experiment", {"ids": [3, 7]})]).resume()
```

- `run_until(step)` 在 epoch 邊界暫停；`fork()` 複製全部 Datapath 狀態與 GRAFCET 標記。
- `remove_ants` 移除指定的螞蟻；`reseed` 重設共用亂數流，讓各分支在分岔後面對同一串隨機性。
- `track_provenance=True` 時，history 會記錄 `contrib_trail`（每隻螞蟻在可感知路徑上的費洛蒙量）、`contrib_total` 與 `delivered_by`。

### 含擾動與事件紀錄的 Ant System

```python
from miat_ants.tsp import AntTSPSystem, AntTSPConfig, random_cities
from miat_ants.core.events import Event, PRIORITY_ENV

coords = random_cities(30, seed=30)
ev = [Event("cut_medium", 50, "environment", {}, PRIORITY_ENV),
      Event("restore_medium", 100, "environment", {}, PRIORITY_ENV)]
r = AntTSPSystem(coords, AntTSPConfig(n_ants=30, max_cycles=150, seed=0, medium_mode="shared",
                                      perturbations=ev, log_deposits=True)).run()
print(r.best_length, r.history["consensus"][-1])
r.events.to_csv("my_events.csv")
```

### 接上自己的代理人

在 `AntTSPConfig(policy=...)` 傳入任意函式：

```
f(agent_id, cur, allowed_mask, tau_row, eta_row, rng) -> next_city
```

代理人只能讀到經介質感知後的 `tau_row`；違反 tabu 契約時，系統會拋出例外。`experiments/example_custom_policy.py` 提供了語言模型代理人「觀察 → 提示 → 解析回覆」流程的範本（`llm_stub`），範本不會呼叫任何 API。

### 修改行為

先修改相關 `system.py` 中的模型定義（`add_step`／`add_transition`），再以 `python docs/gen_model_docs.py` 重新產生模型文件（這會改寫中文檔；英文翻譯 `docs/en/GRAFCET_MODELS.md` 需手動更新）。不要繞過模型、直接改 Action 內的流程控制。新指標以純函式寫在 `miat_ants/core/metrics.py`；新擾動需要在 `_apply_perturbation` 加一個分支、在 [DESIGN.md](docs/zh-TW/DESIGN.md) 的事件契約表登錄，並補一項測試。

## 與原論文的關係

本平台以 Python 重寫陳慶瀚 2000 年論文〈仿螞蟻行為的群體解題系統〉中的 Java Applet，並加入可學習螞蟻。exp1–exp3 重現了該論文的結果。差異如下：原稿的方程式物件無法擷取，因此方程式是重建的；原 42 城市座標已無法取得，改用固定種子的隨機實例；模擬退火與遺傳演算法是重新實作的；分揀系統一個「迭代」包含的步數原論文沒有載明，因此另行校準。詳見 [DESIGN.md](docs/zh-TW/DESIGN.md) 最後一節。

## 授權

- 程式碼（`miat_ants/`、`experiments/`、`tests/`、`docs/gen_model_docs.py`、`run_all.py`）：[MIT 授權](LICENSE)。
- 資料、圖表、模型權重與文件（`results/`、`figures/`、`miat_ants/foraging/weights/`、`docs/`、README 檔）：[創用 CC 姓名標示 4.0 國際（CC BY 4.0）](LICENSE-DATA)。

## 引用

使用本程式碼或資料時，請引用本儲存庫（見 [CITATION.cff](CITATION.cff)）；論文正式發表後會補上期刊引用資訊。

## 聯絡

問題回報與建議：請開 issue。
