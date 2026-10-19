[English](../en/DESIGN_microgpt_ants.md) | 中文

# microGPT 螞蟻語言模型：MIAT 2.0 設計文件

本文件定義平台的第三個子系統 `miat_ants/foraging`：把螞蟻的感知與行動編碼成 token 序列，以微型自迴歸 Transformer（microGPT 級，約 4 千參數）作為螞蟻的決策核心，並保留規則螞蟻作為對照組。

**設計決策**

| 項目 | 決定 |
|---|---|
| 實驗環境 | 覓食，含開闊地圖與雙橋 |
| 模型權重 | 共享基礎模型＋各 agent 個別線上微調 |
| 學習方式 | 先做行為複製（BC），再做線上篩選式自我模仿 |
| 社會學習 | 預設關閉，以開關提供 |
| 序列格式 | 感知詞與行動詞交錯 |

---

## Phase 0｜需求形式化

| ID | 需求 | 量測方法 | 驗收條件 | 證據 |
|---|---|---|---|---|
| F-01 | 序列採交錯格式 `. o₁ a₁ o₂ a₂ …`。感知詞只能由世界寫入，行動詞只能由核心產生。 | 每個 token 依位置檢查類別 | 違反時拋出例外 | test_vocab_and_sequence_contract |
| F-02 | 模型只在行動位置計算損失與取樣。取樣時把非行動詞的機率遮為 0。 | 損失遮罩、取樣結果 | 100% 是行動詞 | test_masked_loss、test_rule_core_contract_and_gpt_decide_only_actions |
| F-03 | microGPT 的反向傳播正確 | 與有限差分做梯度檢查 | 相對誤差 < 1e-5 | test_gradcheck |
| F-04 | 模型能學習：可過擬合固定序列 | 訓練後的損失 | 降到 < 0.05 | test_overfit |
| F-05 | 參數量與 microgpt 同級 | 計數 | 3–6 千 | test_param_count |
| F-06 | 多 agent 批次推論：每個 agent 有自己的權重，一次前向完成全體決策 | 與逐一推論比對 | 數值一致 | test_batched_equals_single |
| F-07 | 世界守恆：食物總量 = 剩餘 + 攜帶中 + 已送達 | 每次執行後檢查 | 恆等 | test_food_conservation |
| F-08 | 感知編碼正確：食物、牆、費洛蒙、巢方向、在巢內 | 人造情境 | 全部符合預期 token | test_perception_cases |
| F-09 | 規則螞蟻（teacher）能完成覓食，並在雙橋偏好短路徑 | 送達率、短橋比例 | 送達 > 0；短橋比例 > 0.5 | exp9(a)(b) |
| F-10 | BC 後的 GPT 螞蟻功能對等 | 送達率比值 | ≥ 規則螞蟻的 80% | exp9(a) |
| F-11 | 線上學習只更新該 agent 自己的權重 | 權重差分 | 其他 agent 不變 | test_individual_learning_isolated |
| F-12 | 介質支援 shared／private／cut，延續主題一的對照設計 | 介面測試 | 通過 | test_field_medium |
| F-13 | 關鍵事件寫入事件契約：取食、送達、回合結束、學習、擾動 | 事件與狀態比對 | 送達事件數 = 送達計數 | test_food_conservation_events_and_token_walk |
| F-14 | 所有 GRAFCET 通過 Gate 2 審查；Token 走查包含正常與例外路徑（回合逾時） | `validate()`、trace | 通過 | test_food_conservation_events_and_token_walk |
| F-15 | 同一種子的結果完全一致 | 執行兩次比對 | 一致 | test_individual_learning_isolated_and_reproducible |

**非功能需求**

- 只依賴 numpy，不需要 GPU。
- 一般 CPU 上，30 隻螞蟻 × 3000 步的單次執行少於 60 秒。
- 預訓練權重隨專案提供：`miat_ants/foraging/weights/base_bc.npz`。

---

## Phase 1｜系統架構

### 詞彙表（24 個 token）

| 類別 | Token | 意義 | 寫入者 |
|---|---|---|---|
| 邊界 | `.` | 回合開始（BOS） | 系統 |
| 行動・移動 | `F` `L` `R` | 前進；左轉 45° 後前進；右轉 45° 後前進 | 核心 |
| 行動・移動並標記 | `f` `l` `r` | 同上，並在新位置沉積費洛蒙 | 核心 |
| 行動・操作 | `T` `D` | 拿取食物（之後轉向 180°）；在巢內放下食物（之後轉向 180°） | 核心 |
| 感知・搜尋中 | `X` `A` `B` `C` | 腳下有食物；正前方、左前方、右前方有食物 | 世界 |
| 感知・搜尋中 | `P` `Q` `S` `N` `W` | 費洛蒙最強在前、左前、右前；什麼都沒有；前方是牆 | 世界 |
| 感知・攜帶中 | `0` `1` `2` `3` `4` `w` | 在巢內；巢在前、右、後、左；前方是牆 | 世界 |

**感知優先序**

- 搜尋中：X > W > 食物方向（A/B/C）> 費洛蒙方向（P/Q/S，需超過閾值）> N
- 攜帶中：0 > w > 巢方向

感知會依當下任務選取最顯著的線索，這是梅洛龐蒂「意向弧」與 Gibson「可供性」的操作化。

### 實體架構

| 元件 | 位置 |
|---|---|
| 微型 Transformer | `miat_ants/microgpt/model.py`（純 numpy） |
| 場域介質 | `miat_ants/core/field_medium.py` |
| 覓食子系統 | `miat_ants/foraging/`：`vocab.py`、`world.py`、`cores.py`、`system.py`、`pretrain.py`、`analysis.py` |
| 預訓練權重 | `miat_ants/foraging/weights/` |
| 實驗 | `experiments/exp9_microgpt_ants.py`；另見 `exp10_topic2_learnable.py`（含 exp10b）、`exp11_d1_controls.py`、`exp12_learnable_return.py`、`exp13_grammar_adherence.py` |

### IDEF0 功能架構

| 模組 | 功能 | Input | Control | Output | Mechanism |
|---|---|---|---|---|---|
| A0 | 以 token 化螞蟻群體覓食並形成路徑 | 地圖、基礎權重 | ForagingConfig、擾動事件 | 送達紀錄、歷史、事件、各 agent 權重 | numpy |
| A1 | 初始化世界、介質與核心 | 地圖規格、權重檔 | 種子、核心類型、權重模式 | World、FieldMedium、AgentCore | `World`、`make_core` |
| A21 | 感知編碼：世界狀態 → 感知詞 | 位置、朝向、攜帶狀態、介質讀值 | 感知優先序、費洛蒙閾值 | 每隻螞蟻一個感知詞，附加到上下文 | `World.perceive` |
| A22 | 決策：上下文 → 行動詞 | 每隻螞蟻最近 16 個 token | 溫度、行動遮罩 | 每隻螞蟻一個行動詞 | `AgentCore.decide` |
| A23 | 行動執行：行動詞 → 世界改變 | 行動詞 | 牆、食物、巢的規則 | 新狀態、事件旗標（取食／送達／受阻）、介質沉積 | `World.apply`、`FieldMedium.deposit` |
| A3 | 介質更新 | delta buffer | ρ（殘留係數） | τ ← ρτ + Δτ | `FieldMedium.commit` |
| A4 | 線上學習 | 各 agent 的成功回合緩衝 | 學習率、batch 大小、更新次數、是否社會學習 | 更新後的權重、損失 | `AgentCore.learn` |
| A5 | 量測與事件處理 | 歷史、世界狀態 | 擾動事件佇列、epoch 數 | 指標、finished | `metrics`、`EventQueue` |
| A6 | 行為複製預訓練（離線） | 規則螞蟻的軌跡 | 步數、batch、學習率 | `base_bc.npz` | `pretrain.py` |

### 介面契約

**AgentCore**（規則核心與 GPT 核心都必須實作）

| 方法 | 契約 |
|---|---|
| `decide(ids, contexts) -> tokens` | contexts 是長度 ≤16 的 token id 序列，最後一個必須是感知詞。回傳值必須屬於行動詞集合。不得讀取世界或介質。 |
| `learn(ids, episodes) -> dict` | 只能更新 ids 中各 agent 自己的參數。規則核心不學習，回傳空 dict。 |
| `n_params() / policy_probe(contexts)` | 給研究者用的觀察介面：在固定的探針上下文下取得行動分布。 |

**World**

| 方法 | 契約 |
|---|---|
| `perceive(ids) -> obs_tokens` | 只回傳感知詞，不改變狀態 |
| `apply(ids, act_tokens) -> ActResult` | 無效行動視為無作用（no-op），不拋出例外；回傳 moved／took／delivered／blocked／marked 旗標 |
| `food_total()` | 守恆檢查用 |

**FieldMedium**（延續 GraphMedium 的契約）

| 方法 | 契約 |
|---|---|
| `deposit(ids, cells, amount)` | 只寫入 delta buffer |
| `commit()` | 套用 τ ← ρτ + Δτ |
| `sense(ids, cells)` | 回傳讀值；處於 cut 狀態時回傳 0；可加雜訊；private 模式下只讀得到自己的介質 |

**事件契約**

| 事件 | 來源 | 優先權 |
|---|---|---|
| `take`、`deliver` | `ant:k` | LOG |
| `episode_end`（payload：success、length、mark_rate） | `ant:k` | LOG |
| `learn`（payload：agent 數、平均損失） | A4 | MISSION |
| `cut_medium`、`restore_medium`、`block_gate`、`unblock_gate`、`remove_ants`、`restore_ants` | environment | ENV |

### Gate 1 審查

- **共享狀態**
  - 介質採 deposit→commit 兩段式。
  - 世界的位置與食物在 A23 依 ant index 順序處理：同一格食物只剩 1 個時，index 小的螞蟻先取，這是明確的仲裁規則。
- **效能熱點**
  - A22 每步一次批次前向，複雜度 O(A·T²·C)。
  - A4 每個 epoch 對 A 個 agent 各做 n 次 Adam 更新。

---

## Phase 2｜行為建模（GRAFCET）

### G0：感覺運動時脈（主控制器）

| Step | Action | 轉移條件 | 下一狀態 |
|---|---|---|---|
| X0（init） | A1 初始化（P1） | init_done | X1 |
| X1 | A21 感知（P1） | obs_ready | X2 |
| X2 | A22 決策（P1） | actions_ready | X3 |
| X3 | A23 行動（P1） | act_done | X4 |
| X4 | A3 介質更新、步數加 1（P1） | step_done ∧ ¬epoch_end | X1 |
| X4 | 同上 | step_done ∧ epoch_end | X5 |
| X5 | A4 線上學習（P1） | learn_done | X6 |
| X6 | A5 量測與事件（P1） | record_done ∧ ¬finished | X1 |
| X6 | 同上 | record_done ∧ finished | X7 |
| X7 | 輸出報告（terminal） | — | — |

### G2：任務狀態（族群控制器，n = 螞蟻數）

| Step | 意義 | 轉移條件 | 下一狀態 |
|---|---|---|---|
| X20（init） | 搜尋 | took | X21 |
| X20 | 搜尋 | ep_len ≥ max_ep | X23 |
| X21 | 攜帶返巢 | delivered | X22 |
| X21 | 攜帶返巢 | ep_len ≥ max_ep | X23 |
| X22 | 成功回合：寫入成功緩衝、重設上下文（P1） | recorded | X20 |
| X23 | 逾時（例外路徑）：捨棄回合、重設上下文（P1） | reset_done | X20 |

G0 是整個群體共用的感知—行動時脈；G2 是每隻螞蟻的任務意向（搜尋／返巢）。兩者以 A23 產生的完成事件（took、delivered）協調：G2 在 A23 之後的下一個 clock 讀取這些旗標，A21 會在下一輪感知開始時清除它們。

### 並行失敗模式

| 模式 | 處理 |
|---|---|
| Stale data | A21 在 A23 與 A3 之後執行，一定讀到最新的世界與介質 |
| Race | 同格取食依 index 優先；介質採 delta buffer |
| Deadlock | G0 是線性循環；G2 的每個狀態都有逾時出口 |
| Starvation | 被移除的螞蟻不參與 A21–A23 |

---

## Phase 3｜合成

- **Controller**：沿用 `core/grafcet.py`。G0 的 n = 1；G2 的 n = A，是族群向量化版本。
- **Action／Datapath**：都是純函式或物件方法，對應上表的 IDEF0 編號。
- **AgentCore 實作**：`RuleCore`（規則螞蟻）與 `GPTCore`（microGPT）。實驗時兩者在同一個世界中互換，確保比較公平。

## Phase 4｜驗證

| 層次 | 測試 |
|---|---|
| 模型檢查 | Gate 2 審查；GRAFCET 自動文件 |
| Datapath 單元 | 梯度檢查、過擬合、遮罩、批次一致性、感知情境、行動效果、介質 |
| 整合 | 食物守恆、事件一致、Token 走查（含逾時例外路徑）、可重現性 |
| 系統驗收 | exp9：(a) 功能對等；(b) 雙橋；(c) 方言與慣例；(d) 切斷介質 |

## Traceability

| 需求 | IDEF0 | GRAFCET | 函式 | 測試 |
|---|---|---|---|---|
| F-01、F-02 | A21、A22 | G0.X1–X2 | `vocab`、`GPTCore.decide`、`MicroGPT.loss` | test_vocab_and_sequence_contract、test_masked_loss |
| F-03～F-06 | A22、A4 | G0.X2、X5 | `MicroGPT.forward/backward/step` | test_gradcheck、test_overfit、test_batched… |
| F-07、F-08 | A21、A23 | G0.X1、X3 | `World.perceive/apply` | test_food_conservation、test_perception_cases |
| F-11 | A4 | G0.X5、G2.X22 | `GPTCore.learn` | test_individual_learning_isolated |
| F-12 | A23、A3 | G0.X3–X4 | `FieldMedium` | test_field_medium |
| F-13、F-14 | A5、全部 | G0、G2 | `ForagingSystem` | test_food_conservation_events_and_token_walk |

---

## 驗證證據（Phase 4 結果）

| 需求 | 證據 | 結果 |
|---|---|---|
| F-03 | test_gradcheck | 最大相對誤差約 1.6e-8 |
| F-04、F-05 | test_overfit、test_param_count | 損失 < 0.05；參數 4,096（microgpt 原版為 4,192） |
| F-06、F-11 | test_batched_equals_single…、test_individual_learning_isolated… | 通過 |
| F-07、F-13、F-14 | test_food_conservation_events_and_token_walk | 守恆；送達事件數 = 送達計數；正常路徑與逾時例外路徑都走完 |
| A6 預訓練 | `miat_ants/foraging/weights/base_bc.json` | 9,984 個 teacher 回合、約 104 萬 token；保留集 NLL 0.284；最可能行動與 teacher 一致率 91.2% |
| F-09、F-10 | exp9(a) | 見 [RESULTS.md](RESULTS.md)（exp9）：BC 後的 GPT 螞蟻送達量為規則螞蟻的 1.07–1.15 倍，達到對等要求 |

### 設計備註

- **行為複製的結果略優於 teacher，這是合理的。** teacher 在可確定的情境中仍保留約 10% 的雜訊行為。模型以有限容量近似 teacher 的分布時，會稍微「去噪」。
- **方言分散度的定義。** 以 agent 兩兩之間 JS 的平均計算，與漂移使用同一個 JS 定義，所以兩者的數值可以直接比較。
