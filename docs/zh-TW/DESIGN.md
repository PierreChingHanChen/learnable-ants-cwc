[English](../en/DESIGN.md) | 中文

# 仿螞蟻行為的群體解題系統：MIAT 2.0 設計文件

> 第三個子系統「microGPT 螞蟻語言模型」（`miat_ants/foraging`）的完整設計，見 [`DESIGN_microgpt_ants.md`](DESIGN_microgpt_ants.md)。

原論文：陳慶瀚（2000），〈仿螞蟻行為的群體解題系統〉（Java Applet 實作）
重寫目標：以 MIAT 2.0 方法論（需求 → IDEF0 → GRAFCET → 高階合成 → 分層驗證）重建兩個系統，作為後續三個研究主題的實驗平台：

1. Stigmergy 與 We-sense
2. 分散式責任
3. 交織的可逆性

論文中，主題一對應第一個脫鉤（D1，協調而不趨同），主題二對應 D2（痕跡與責任），主題三對應 D3（恢復而不回歸）。

---

## Phase 0｜需求形式化

| ID | 需求 | 量測方法 | 驗收條件 | 測試／證據 |
|---|---|---|---|---|
| R-01 | 螞蟻–TSP 系統依 Ant System（ant-cycle，式1–5）求解對稱 TSP | 5×5 網格已知最佳解 24+√2 | 40 週期內誤差 ≤ 3% | `test_grid_optimum_found_and_token_walk` |
| R-02 | 每隻螞蟻的巡迴必須合法：每城市恰好一次，最後回到起點 | `is_valid_tour` | 100% 合法 | A23 assert、`test_baselines_valid` |
| R-03 | 費洛蒙更新符合式(3)：τ ← ρτ + Δτ | 數值比對 | 誤差 < 1e-9 | `test_medium_eq3_and_provenance_invariant` |
| R-04 | 重現原論文表1：ACO、SA、GA 在 42 城市問題上各跑 10 次的比較 | 最佳解／平均／標準差 | 輸出表格與 CSV | `exp2_tsp_compare` |
| R-05 | 重現原論文圖3：螞蟻數、ρ、α、β、Q 的參數實驗 | 與參考最佳解的差距 % | 輸出圖與 CSV | `exp1_tsp_params` |
| R-06 | 自動分揀系統依式(6)(7)(8) 執行拿起與放下 | 單調性、邊界值 | p_pick 隨 f 遞減，p_drop 隨 f 遞增 | `test_density_bounds_and_probabilities` |
| R-07 | 物資守恆：網格上與攜帶中的物資總數恆為 N，且 id 不重複 | 每次執行後檢查 | 200/200 | `test_object_conservation_and_clustering` |
| R-08 | 空間熵（式9–10）可量測聚類程度 | 完全分離為 0，隨機分布 > 0.9 | 通過 | `test_entropy_extremes` |
| R-09 | 重現原論文圖7、圖8、表2 | E_S 曲線與表格 | 輸出圖與 CSV | `exp3_sorting` |
| R-10 | 同一個隨機種子必須得到完全相同的結果 | 執行兩次後比對 | 完全一致 | `test_seed_reproducibility` |
| R-11 | 介質可在共享與私有之間切換，並支援讀取延遲、雜訊與切斷（主題一） | 介面測試與實驗 | delay 讀到舊狀態；cut 後讀到均勻矩陣 | `test_medium_delay_and_cut`、`exp4` |
| R-12 | 每份費洛蒙都可追溯到留下它的 agent，且守恆：τ = base + Σ contrib（主題二） | 不變量檢查 | 誤差 < 1e-6 | `check_invariant`、`exp5` |
| R-13 | 所有拿起與放下事件都寫入事件契約；事件數必須與狀態一致：picks − drops = 攜帶數（主題二） | 事件與狀態比對 | 完全一致 | `test_object_conservation_and_clustering` |
| R-14 | 外部擾動以高優先權事件在週期邊界處理，包括封路／解封、移除／恢復螞蟻、切斷／恢復介質、打亂網格（主題三） | 例外路徑 Token 走查 | 封路後最佳巡迴不含被封邊 | `test_exception_path_block_edge`、`exp6` |
| R-15 | 所有 GRAFCET 都必須通過 Gate 2 審查：可達、有離開條件、條件不得為 True | `Grafcet.validate()` | 建構時自動檢查，未通過即拋出例外 | `test_validate_*`、[`GRAFCET_MODELS.md`](GRAFCET_MODELS.md) |
| R-16 | 以配對統計量化責任：bootstrap 信賴區間、附效果量的 Wilcoxon 檢定、Holm 校正與群組 Shapley 值（主題二） | 統計工具的單元測試 | 通過 | `test_holm`、`test_paired_stats_and_ci`、`exp7`、`exp10` |
| R-17 | 蟻群可由已知巡迴暖啟動：介質寫入該巡迴的穩態費洛蒙，存檔保存該巡迴（主題三） | 介面測試 | 介質與存檔都能取回寫入的巡迴 | `test_warm_start_imprint_and_reference_helpers`、`exp8` |

**非功能需求**

- 一般筆電上單次 25 城市、100 週期的執行時間少於 3 秒。
- 純 Python 實作，只依賴 numpy 與 matplotlib。
- 所有隨機性只來自每個系統各自的 `np.random.Generator`，不使用 global state。

---

## Phase 1｜系統架構

### 實體架構（部署視圖）

| 元件 | 位置 | 說明 |
|---|---|---|
| 核心框架 | `miat_ants/core/` | GRAFCET 引擎、事件契約、共享介質、量測指標 |
| 螞蟻–TSP | `miat_ants/tsp/` | `problem.py`（A1 問題實例）、`actions.py`（Datapath）、`system.py`（Controller ＋ 組裝）、`baselines.py`（SA/GA） |
| 螞蟻–分揀 | `miat_ants/sorting/` | `actions.py`（Datapath）、`system.py`（Controller ＋ 組裝） |
| 實驗 | `experiments/` | 原論文重現（exp1–3）、三個研究主題（exp4–8）、可學習螞蟻（exp9–13，含 exp10b；見 [`DESIGN_microgpt_ants.md`](DESIGN_microgpt_ants.md)） |
| 驗證 | `tests/` | 模型、Controller、Action、整合四層測試 |

### 功能架構（IDEF0）：螞蟻–TSP

| 模組 | 功能（動詞片語） | Input | Control | Output | Mechanism |
|---|---|---|---|---|---|
| A0 | 以蟻群集體搜尋 TSP 最短巡迴 | 城市座標 | AntTSPConfig、擾動事件 | 最佳巡迴、歷史紀錄、事件紀錄 | Python/numpy |
| A1 | 初始化問題 | 座標 | τ0、ρ、介質模式 | D、η、介質 | `a1_initialize`、`distance_matrix`、`visibility` |
| A21 | 放置螞蟻 | m、n | 存活螞蟻遮罩 | 起始城市、tabu list | `place_ants` |
| A22 | 依機率選擇下一城市 | 介質讀值 τ、η、tabu | α_k、β_k（式1） | 下一城市 | `choose_next`、`GraphMedium.sense` |
| A23 | 閉合巡迴 | n−1 步後的路徑 | 合法性規則 | 完整巡迴 | `a23_close_tours` |
| A3 | 評估巡迴 | 巡迴、D | 目前成本（可能已被擾動） | L_k、本週期最佳、全域最佳 | `tour_length` |
| A4 | 更新費洛蒙 | 巡迴、L_k | Q、ρ（式3–5） | 新的 τ、provenance | `GraphMedium.deposit/commit` |
| A5 | 紀錄、處理事件、判斷終止 | 量測值 | max_cycles、事件佇列 | history、finished | `EventQueue`、`metrics` |

### 功能架構（IDEF0）：螞蟻–分揀

| 模組 | 功能 | Input | Control | Output | Mechanism |
|---|---|---|---|---|---|
| A0 | 將異質物資分揀成同質聚落 | 物資、網格 | AntSortConfig、擾動事件 | 網格、熵曲線、事件紀錄 | Python/numpy |
| A11 | 放置物資 | H、W、類別數、數量 | 一格最多一個物資 | type_grid、id_grid | `place_objects` |
| A12 | 放置螞蟻 | H、W、m | — | 位置 | `place_ants` |
| A21 | 隨機移動 | 位置、速度 | 8 方向、環面邊界、只在 G0.X1 時移動 | 新位置 | `random_moves` |
| A22 | 評估是否拿起 | 腳下物資、鄰域 | k1（式6、8）、仲裁規則 | 拿起成功遮罩、pick 事件 | `local_density`、`p_pick`、`arbitrate` |
| A23 | 評估是否放下 | 攜帶物資、鄰域 | k2（式7、8）、仲裁規則 | 放下成功遮罩、drop 事件 | `p_deposit`、`arbitrate` |
| A3 | 量測聚類程度 | type_grid | 區塊大小 s（式9–10） | E_S | `spatial_entropy` |
| A4 | 紀錄、處理事件、判斷終止 | history | max_iterations、事件佇列 | finished | `EventQueue` |

### 共享介質的介面契約（主題一）

| 方法 | 契約 |
|---|---|
| `deposit(agent, edges, amount)` | 只寫入 delta buffer，不會立即生效 |
| `commit()` | 同步套用式(3)；各 agent 之間沒有寫入順序依賴，所以不存在 race condition |
| `sense(agent)` | 回傳 (n, n) 矩陣：可能延遲 d 週期、加上雜訊、或在切斷時回傳均勻矩陣 |
| `snapshot()` | 研究者視角的真實狀態，agent 不可呼叫 |
| `provenance_share(edges)` | 回傳 [環境初始量, agent0, …] 的占比，總和為 1 |

**擴充方式：** 把螞蟻換成 LLM 代理人時，只要讓代理人遵守 deposit/sense 介面，A2 與 A4 的契約就不變。

### Gate 1 審查紀錄

- **共享狀態**
  - TSP 的介質採 deposit → commit 兩段式，沒有隱藏的共享寫入。
  - 分揀的網格是唯一共享物；同一格的衝突由 `arbitrate` 明確仲裁，規則是 ant index 小者優先，衝突次數也會被記錄。
- **效能熱點**
  - A22 每個 clock 對 m 隻螞蟻各做一次 O(n) 機率計算，單次執行約 m·n²·cycles。
  - 分揀的鄰域計數以 numpy roll 向量化，每個 clock 約 O(H·W)。

---

## Phase 2｜行為建模（GRAFCET）

完整的狀態表與 Mermaid 圖見 **[`GRAFCET_MODELS.md`](GRAFCET_MODELS.md)**。該檔由程式中的模型自動產生，是 single source of truth。

| 控制器 | 啟動條件 | 完成條件 | 說明 |
|---|---|---|---|
| TSP G0 | 上電（X0） | X5 | A1→A2→A3→A4→A5 循環 |
| TSP G2 | G0.X1 | X24 | 巡迴建構；X22 以 `tours_complete` 完成事件離開，不是 True |
| Sort G0 | 上電（X0） | X4 | 一個迭代包含 `steps_per_iteration` 個 clock |
| Sort G2 | G0.X1 ∧ 腳下條件 | — | 族群 GRAFCET，n = 螞蟻數，每隻螞蟻各自持有一組狀態變數 |

### 並行的四種失敗模式檢查

| 失敗模式 | 本系統的處理 |
|---|---|
| Stale data | TSP 介質只在 commit 時更新。`sense_delay` 則是**刻意**引入的 stale data，作為主題一的實驗變因。 |
| Deadlock | 等待鏈只有 G0.X1 ⇄ G2.X24，不會成環。`SuperLoop.run` 設有 max_ticks 保護。 |
| Race condition | 分揀時同一格的拿起或放下競爭，由 `arbitrate` 處理。Divergence OR 若同時致能，`Grafcet.conflicts` 會計數。 |
| Starvation | 被移除的螞蟻（alive=False）不執行 Action，也不參與轉移條件。 |

### 事件契約（Event）

欄位：`event_type, timestamp, source_module, payload, priority, policy`

| event_type | 來源 | 優先權 | 用途 |
|---|---|---|---|
| `deposit` | `ant:k` | LOG | 主題二：每次費洛蒙沉積 |
| `pick` / `drop` | `ant:k` | LOG | 主題二：分揀的每個動作，payload 含 f、p、cell |
| `block_edge` / `unblock_edge` / `move_city` | environment | ENV | 主題三：環境改變 |
| `remove_ants` / `restore_ants` | environment | ENV | 主題三：個體失效 |
| `cut_medium` / `restore_medium` / `cut_sensing` / `restore_sensing` | environment | ENV | 原論文 4.2.3：溶解並重組集體智能 |
| `scramble_region` / `scramble_all` | environment | ENV | 主題三：分揀的大擾動 |
| `perturbation_applied` / `report` | 系統 | 同原事件 | 追溯證據 |

---

## Phase 3｜高階合成

`miat_ants/core/grafcet.py` 以 MIAT 方法論的 GRAFCET 合成規則實作 Controller，並把 Controller 與 Action 分開。

| GRAFCET 元素 | 實作 |
|---|---|
| State Xi | `Grafcet.X[sid]`：長度 n 的布林陣列 |
| Transition Ri | `add_transition(..., cond)`：條件函式。建構時拒絕 True。 |
| Fundamental／AND／OR | `controller()` 採同步快照語意；宣告順序即 OR 分支的優先序 |
| Action | `add_step(..., action, mode)`。mode 為 `N`（持續）或 `P1`（進入時一次）。完成時以 `mark_done()` 產生事件。 |
| Sub-GRAFCET | 獨立的 Grafcet 物件，由 `SuperLoop` 在同一個 clock 內「先全部 controller，再全部 action」。採用狀態協調，不是 call-return。 |
| Reset | `Grafcet.reset()` |

所有 Action 都是 `actions.py` 中的純函式。每個函式都有 Input／Output 說明，可以用固定輸入獨立測試（3b、3c 白箱驗收）。

---

## Phase 4｜分層驗證

| 層次 | 檔案 |
|---|---|
| 模型檢查 | `Grafcet.validate()`（建構時自動執行）、[`GRAFCET_MODELS.md`](GRAFCET_MODELS.md) |
| Controller 模擬 | `tests/test_grafcet.py`：基本塊、AND、OR、P1/N、族群、子控制器協調 |
| Action 單元測試 | `tests/test_tsp.py`、`tests/test_sorting.py` 中的公式與函式測試 |
| 整合測試 | 系統完整執行、Token 走查（正常路徑與例外路徑）、守恆與一致性 |
| 系統驗收 | `experiments/` 的 exp1–exp13（含 exp10b），由 `run_all.py` 依序執行，輸出 `results/summary_*.md` |

### Traceability

| 需求 | IDEF0 | GRAFCET 狀態 | 函式 | 測試 |
|---|---|---|---|---|
| R-01 | A0–A5 | G0.X0–X5、G2.X20–X24 | `AntTSPSystem.run` | test_grid_optimum… |
| R-02 | A21–A23 | G2.X21–X23 | `place_ants`、`choose_next`、`is_valid_tour` | test_tour_length_closed |
| R-03 | A4 | G0.X3 | `GraphMedium.commit` | test_medium_eq3… |
| R-06 | A22、A23 | Sort G2.X21、X23 | `p_pick`、`p_deposit`、`local_density` | test_density… |
| R-07、R-13 | A22、A23 | Sort G2.X21–X23 | `a22_eval_pick`、`a23_eval_drop` | test_object_conservation… |
| R-08 | A3 | Sort G0.X2 | `spatial_entropy` | test_entropy_extremes |
| R-11 | A22（Mechanism） | TSP G2.X22 | `GraphMedium.sense` | test_medium_delay_and_cut |
| R-12 | A4 | TSP G0.X3 | `provenance_share`、`check_invariant` | test_medium_eq3… |
| R-14 | A5、A4 | TSP G0.X4、Sort G0.X3 | `_apply_perturbation` | test_exception_path_block_edge |
| R-16 | A4、A5 | TSP G0.X3–X4 | `provenance_share`；`experiments/common.py` 的統計工具 | test_stats |
| R-17 | A1、A5 | TSP G0.X0、X4 | `GraphMedium.imprint`、`init_best`、`greedy_medium_tour`、`two_opt` | test_warm_start_imprint… |
| R-15 | 全部 | 全部 | `Grafcet.validate` | test_validate… |

---

## 與原論文的差異與重建說明

1. **方程式重建。** 原 .doc 中的方程式物件無法擷取。式(1)–(5) 依 Dorigo, Maniezzo & Colorni（1996）的 Ant System（ant-cycle）重建；式(6)–(8) 依 Deneubourg et al.（1991）與 Lumer & Faieta（1994）重建；式(9)–(10) 依文字描述重建（區塊熵，以 log(類別數) 正規化後取平均）。由於是重建，細節可能與原論文的方程式不同。
2. **42 城市實例。** 原座標已無法取得，改用固定種子的 42 個隨機城市。可用 `load_tsplib()` 換成 dantzig42 等標準實例。
3. **SA／GA 為重新實作。** 參數取常見值，並設定相近的評估預算。
4. **「迭代」的定義。** 原論文沒有載明分揀系統的一個迭代包含幾步。本版以 `steps_per_iteration`（預設 20 個 clock）定義，依表2數值的量級校準。
5. **新增的研究旋鈕**（預設關閉，所以預設行為與原演算法相同）：
   - 介質模式、延遲、雜訊、切斷
   - provenance 追蹤
   - 個體異質性
   - 事件紀錄
   - 擾動事件
