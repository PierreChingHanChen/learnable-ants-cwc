[English](../en/DATA_DICTIONARY.md) | 中文

# 資料字典

本文件說明 `results/` 中每個檔案由哪個實驗產生，以及各欄位的意義。每個檔案用於論文的哪張圖或哪個表，請見 [EXPERIMENTS.md](EXPERIMENTS.md)。

## 共同慣例

- `seed` 是一次執行的隨機種子；不同條件中種子相同的列彼此配對。
- `core` 為 `rule`（規則螞蟻）或 `gpt`（可學習螞蟻：行為複製的 transformer 加上線上自我模仿）。
- `delivered` 是送回巢穴的食物數；`short_frac` 是雙橋上通過短橋的穿越次數比例（開闊地圖為 0）。
- 統計摘要檔共用以下欄位：`mean`、`ci_lo`、`ci_hi`（95% bootstrap 信賴區間）、`d_z`（配對效果量）、`p`（雙尾配對 Wilcoxon 檢定）、`n`（種子數），部分檔案另有 `p_holm`（Holm 校正）。
- 策略差異（`dispersion`、`drift`、`disp`、`js_*`）都是以 nats 為單位的 Jensen-Shannon 散度，在 96 個固定的探針上下文上讀取。
- 旅行推銷員的差距（`gap_pct`、`*_gap`）是高於參考最佳解的百分比（30 城市實例為 456.637）。
- `.npy` 檔是以 `np.save(..., allow_pickle=True)` 存的 Python 物件。字典檔 `exp12.npy`、`fig_data.npy` 與 `fig_data_5seeds.npy` 請用 `np.load(path, allow_pickle=True).item()` 讀取；`fig_data_null.npy` 是字典組成的陣列（`np.load(path, allow_pickle=True)`）。
- 少數標籤欄位保留腳本寫入的中文值：`exp10*_shapley_*.csv` 的 `group`（`Q1(痕跡最多)`、`Q4(痕跡最少)`）、`exp7_group_shapley.csv` 的 `group`（`Q1(最高)`、`Q4(最低)`）、`exp6b_cut_remove.csv` 的 `condition`（`切斷介質後恢復`、`移除半數螞蟻後恢復`），以及 `example_custom_policy.csv` 的 `policy`（`Ant System 式(1)`）。

## 平台驗證（exp1–exp3）

| 檔案 | 欄位 |
|---|---|
| `exp1_tsp_params.csv` | `instance`（`grid5x5` 或 `random30`）、`param`（`n_ants`、`rho`、`alpha`、`beta`、`Q`）、`value`、`seed`、`best`（100 週期後的最佳巡迴長度）、`gap_pct` |
| `exp2_tsp_compare.csv` | `method`（`ACO`、`SA`、`GA`）、`run`、`best`（42 城市的最佳巡迴長度）、`sec`（執行秒數） |
| `exp3_entropy_curve.csv` | `iteration`、`entropy`（分揀網格的空間熵 E_S，介於 0 與 1） |
| `exp3_fig8_ants.csv` | `n_ants`、`seed`、`entropy_100`（100 迭代後的 E_S） |
| `exp3_table2_k1k2.csv` | `k1`（拿起常數）、`k2`（放下常數）、`ES(100)`、`ES(500)`、`ES(1000)`（該迭代數後的平均 E_S） |

## 旅行推銷員與分揀實驗（exp4–exp8）

| 檔案 | 欄位 |
|---|---|
| `exp4a_private_vs_shared.csv` | `beta`（啟發權重）、`mode`（`shared` 共享或 `private` 私有介質）、`seed`、`best`（最佳巡迴長度）、`final_consensus`（路徑共識指數 C：1 減去各城市外連費洛蒙正規化熵的平均；0 表示沒有偏好，1 表示形成單一共同路徑） |
| `exp4b_perceptual_consistency.csv` | `factor`（讀取介質時的 `delay` 延遲週期或 `noise` 雜訊標準差）、`level`、`seed`、`best`、`consensus` |
| `exp4c_sorting_sensing.csv` | `condition`（`local` 鄰域感知、高斯感知雜訊，或 `blind` 不感知）、`seed`、`final_entropy` |
| `exp5a_provenance.csv` | `ant`、`share`（最終最佳巡迴上的費洛蒙中，由該螞蟻留下的比例） |
| `exp5b_counterfactual.csv` | `condition`、`removed`（被移除螞蟻的編號）、`best_mean`、`best_sd`（跨種子的最佳巡迴長度） |
| `exp5c_sorting_authorship.csv` | `ant`、`author_share`（最終聚落中最後由該螞蟻放下的物資比例） |
| `exp5_tsp_event_log.csv`、`exp5_sorting_event_log.csv` | 事件契約紀錄：`event_type`（`deposit`、`report` 等）、`timestamp`、`source_module`、`payload`（JSON）、`priority`、`policy` |
| `exp6a_block_unblock.csv` | `rho`、`seed`、`pre_len`（封路時的最佳巡迴）、`recovery_cycles`（封路後，本週期最佳巡迴回到封路期間最佳巡迴 2% 以內所需的週期數）、`blocked_edge_half_life`（實測半衰期，週期）、`theory_half_life`（ln ½ / ln ρ）、`jaccard_final_vs_pre`（最終最佳巡迴與封路時巡迴的邊重疊）、`edge_readopted`（被封的邊是否出現在最終最佳巡迴中）、`final_len` |
| `exp6b_cut_remove.csv` | `condition`（切斷介質，或移除半數螞蟻）、`seed`、`during_ratio` 與 `after_ratio`（擾動期間與恢復後 10 週期的平均巡迴長度，相對於擾動前）、`consensus_before`、`consensus_during` |
| `exp6c_sorting_scramble.csv` | `seed`、`pre_entropy`、`post_scramble`（打亂後的 E_S）、`recovery_iterations`（回到打亂前 E_S 3% 以內所需迭代數；未恢復為 −1）、`first_descent_iterations`（初次形成所需迭代數） |
| `exp7_counterfactual_stats.csv` | `condition`（`top-1`、`bottom-1`、`random-1`、`top-25%`、`random-25%`、`top-50%`、`random-50%`）與統計摘要欄位，對象是移除後最佳巡迴長度的變化（正值表示變差） |
| `exp7_top_vs_random.csv` | `k`（1、25%、50%）與統計摘要欄位，對象是「依貢獻移除」減「隨機移除」的差 |
| `exp7_dispersion.csv` | `seed`、`gini`（來源占比的 Gini 係數）、`n_eff`（有效貢獻者數）、`max_share` |
| `exp7_group_shapley.csv` | `seed`、`group`（來源占比四分位，Q1 最高）、`provenance_share`、`shapley_share`、`v_single`（該群組單獨的價值 L_random − L）、`v_all`（完整蟻群的價值）、`synergy`（(v_all − Σ v_single) / v_all） |
| `exp8_topic3_controls.csv` | 每次執行一列：`start`（`cold` 冷啟動或 `warm` 從最佳解暖啟動）、`rho`、`seed`、`blocked_edge`、`T1_archive_gap`（封路時的存檔差距）；未擾動對照（`ctrl_`）與擾動組（`pert_`）各有：`perf_gap`（最後 20 週期本週期最佳的平均差距）、`archive_gap`、`J_medium`（費洛蒙場所指向的巡迴與封路時巡迴的邊 Jaccard）、`J_best`（存檔巡迴的同一指標）；`fresh_hit_<x>`（冷啟動：存檔首次進入最佳解 x% 以內的週期，未達到為 −1）與 `rehit_<x>`（暖啟動：解封後再次進入 x% 以內所需的週期，未達到為 −1），x = 0.0、0.5、1.0 |
| `exp8_topic3_stats.csv` | `part`（`control1`：配對擾動；`control2`：重新找回）、`rho`、`metric`、`ctrl`、`pert`（各條件的平均或比例）與統計摘要欄位。`control1` 的 `mean`、`ci_lo`、`ci_hi` 是配對差 pert − ctrl。`control2` 的 `ctrl` 與 `pert` 分別是冷啟動蟻群找到、暖啟動蟻群重新找回最佳解的比例，`ci_lo` 與 `ci_hi` 是 `pert` 的 Clopper–Pearson 區間，`p` 為精確 McNemar 檢定 |
| `exp8_trajectories.npz` | `keys`（每列的 `start|rho|seed`）、`ctrl` 與 `pert`（形狀為 執行數 × 220 的陣列：每週期本週期最佳巡迴的差距 %） |

## 可學習螞蟻（exp9–exp13）

| 檔案 | 欄位 |
|---|---|
| `exp9a_parity.csv` | `tag`（`rule`、`gpt_bc` = 不學習的基礎模型、`gpt_learn` = 可學習螞蟻）、`map`（`open_field` 或 `double_bridge`）、`core`、`seed`、`delivered`、`short_frac`、`timeouts`（400 步內未送達而放棄的回合數） |
| `exp9b_stigmergy.csv` | `tag`（`<core>_<medium>`，介質為 `shared`、`private` 或 `cut`）、`map`、`core`、`seed`、`delivered`、`short_frac`、`timeouts` |
| `exp9c_dialect.csv` | `medium`、`seed`、`dispersion`（螞蟻兩兩之間的平均散度）、`drift`（每隻螞蟻相對基礎模型的平均散度） |
| `exp9d_block_unblock.csv` | 舊版未配對的封鎖再解封結果：`core`、`pre`、`during`、`post`（封鎖前、中、後的短橋比例）、`delivered` |
| `exp10_per_seed.csv`、`exp10b_per_seed.csv` | `core`、`seed`、`condition`（同 exp7）、`d_total`（1000 步測試窗內蟻群送達量的變化）、`d_indirect`（每隻倖存螞蟻送達量的變化）、`additive_expect`（被移除螞蟻在未擾動未來中自己的送達量，取負值）、`removed_trace`（被移除者的痕跡占比）、`removed_direct`（被移除者的送達占比）、`d_short`（短橋比例的變化） |
| `exp10_counterfactual_stats.csv`、`exp10b_counterfactual_stats.csv` | `core`、`outcome`（`d_total` 或 `d_indirect`）、`condition`、統計摘要欄位、`p_holm`、`removed_trace`、`additive_expect` |
| `exp10_top_vs_random.csv`、`exp10b_top_vs_random.csv` | `core`、`k`、`outcome`，以及「依痕跡移除」減「隨機移除」的統計摘要欄位 |
| `exp10_shapley_gpt.csv`、`exp10_shapley_rule.csv`、`exp10b_shapley_*.csv` | `seed`、`group`（痕跡占比四分位，Q1 痕跡最多）、`trace_share`、`direct_share`（送達占比）、`phi`（Shapley 值，單位為食物數）、`superadd`（v(N) / Σ v({g})，同一種子的每列重複） |
| `exp10b_noise.csv` | `core`、`seed`，以及另一個以不同重設種子執行的未擾動分支的 exp10 效果欄位（自然變異） |
| `exp11_per_seed.csv` | `tag`（`social` = 共享介質上的社會學習；`mark05_<core>_<medium>` = 教師以 0.5 機率標記）、`seed`、`delivered`、`short_frac`、`mark_carry_start` 與 `mark_carry_end`（執行開始與結束時，攜帶移動中留下費洛蒙的比例）、`dispersion`、`dispersion_start` |
| `exp12.npy` | 字典，含 `T1`（1000，分岔步）、`T2`（2000，解封步）與 `blocks`：每個核心與種子一個字典，包含 `core`、`seed`、`step`；封鎖分支 B（`blocked_`）、同亂數流雙生分支 C1（`control_`）與不同亂數流雙生分支 C2（`control2_`）在每個紀錄步的 `frac`（短橋比例）、`n`（穿越次數）與 `delivered`（累積送達量）；可學習螞蟻另有 `js_bc`、`js_cc`、`js_bc2`（結束時每隻螞蟻在 B 與 C1、C1 與 C2、B 與 C2 之間的散度；長度 30 的陣列） |
| `exp12_stats.csv` | `core`、`metric`（`short_frac_diff`、`delivered_diff`、`js_excess` = JS(B, C1) − JS(C1, C2)、`js_excess_alt` = JS(B, C2) − JS(C1, C2)）與統計摘要欄位 |
| `exp13_per_seed.csv` | `core`、`medium`、`seed`、`delivered`、`deploy_legal`（依教師文法屬合法的行動比例）、`legal_mass`（探針上策略放在合法行動的機率）、`disp`（分散度）、`disp_within`（文法內分散度） |
| `exp13_grammar.csv` | `core`、`medium`，以及 `deploy_legal`、`legal_mass`、`disp`、`disp_within` 的平均，與 `min_ant_mass`（最不守文法的那隻螞蟻的合法質量） |

## 繪圖資料

| 檔案 | 內容 |
|---|---|
| `fig_data.npy` | 字典，含 `curves`：每類螞蟻（`tag`）與種子一個字典，記錄雙橋上的 `step` 與累積 `delivered`；其中一筆另含 Fig. 1C 用的 `tau`（結束時的費洛蒙場）與 `walls`。最終版本中 `blocks` 為空（配對分岔改存於 `exp12.npy`）；`T1`、`T2` 為 1000 與 2000。 |
| `fig_data_5seeds.npy` | `fig_data.npy` 的舊版 5 種子版本。 |
| `fig_data_null.npy` | Fig. 4F 的舊版零假設分岔資料，為 10 個字典組成的陣列（只有在 `exp12.npy` 不存在時才使用）。 |
| `example_custom_policy.csv` | `example_custom_policy.py` 的輸出：`policy`、`best`、`consensus`。 |

## 模型權重

`miat_ants/foraging/weights/base_bc.npz` 與 `base_bc_mark05.npz` 是行為複製基礎模型的參數（標準教師；以 0.5 機率標記的教師）。旁邊的 `.json` 檔記錄訓練設定與保留集指標（負對數概似，以及與教師的 top-1 一致率）。
