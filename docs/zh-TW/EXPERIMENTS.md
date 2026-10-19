[English](../en/EXPERIMENTS.md) | 中文

# 重現實驗

本文件列出產生〈Coordination without convergence: Three decouplings in learnable ant collectives〉結果與圖表的每個步驟、其設定與輸出，並對照論文中每張圖、每個表背後的腳本與資料。結果本身整理在 [RESULTS.md](RESULTS.md)；檔案格式說明見 [DATA_DICTIONARY.md](DATA_DICTIONARY.md)。

## 慣例

- **配對設計。** 所有比較都以隨機種子配對：同一個種子下，各條件在開始不同之前共享全部隨機性。反事實分支的做法是暫停蟻群並複製其完整狀態（`ForagingSystem.run_until` 與 `fork`）。
- **統計方法。** 95% 百分位 bootstrap 信賴區間（10,000 次重抽）、雙尾配對 Wilcoxon 符號秩檢定並附 Cohen's d_z、同一族比較以 Holm 法校正、配對二元結果用精確 McNemar 檢定、等價性用兩個單尾檢定（TOST）。工具函式在 `experiments/common.py`。
- **預設值就是論文設定。** 不加任何環境變數執行腳本，即重現論文的樣本數。
- **快速模式。** `QUICK=1` 會把每個實驗縮成少數種子與短回合，只用於檢查流程。它寫入同一個 `results/` 與 `figures/`，因此會覆寫論文資料；請在另一份副本中執行，或以 `git checkout -- results figures` 還原。
- **自動產生的紀錄。** 每支腳本也會把文字摘要寫到 `results/summary_<名稱>.md`（繁體中文）。這些檔案屬於執行紀錄，不納入 git；整理過的雙語版本是 [RESULTS.md](RESULTS.md)。
- **執行步驟會覆寫已存的結果。** 每支腳本都寫入 `results/` 與 `figures/`，取代儲存庫附帶的檔案；必要時以 `git checkout -- results figures` 還原。
- **基礎模型。** 行為複製的基礎模型已附在 `miat_ants/foraging/weights/`。`base_bc.npz` 可用 `python -m miat_ants.foraging.pretrain` 重新訓練（約 2 分鐘；會覆寫附帶的檔案）；`base_bc_mark05.npz`（教師以 0.5 機率標記）若不存在，`exp11_d1_controls.py` 會自動重新訓練。

## 執行方式

```bash
python run_all.py                 # 依序執行下表全部步驟
python run_all.py exp10b exp12    # 只執行指定的步驟（exp1 只執行 exp1，不含 exp10–exp13）
python experiments/exp12_learnable_return.py   # 直接執行單一腳本
```

直接執行腳本時使用相同的預設值。在 Windows PowerShell 中，請先以 `$env:QUICK="1"` 設定環境變數，再執行指令，不要用 `VAR=value 指令` 的寫法。驗證性重做 exp10b 就是以三個環境變數執行 exp10 腳本：

```bash
EXP10_SEED0=1000 EXP10_SHAPLEY=12 EXP10_TAG=b python experiments/exp10_topic2_learnable.py
```

完整流程在雙核心 CPU 上需要數小時，其中完整的 exp10 約 50 分鐘。快速模式下，每個旅行推銷員與分揀實驗（exp1–exp8）各約 20 到 100 秒。

## 步驟

| 步驟（`run_all.py`） | 腳本 | 論文位置 | 預設樣本 | `results/` 中的主要輸出 |
|---|---|---|---|---|
| exp1_tsp_params | `exp1_tsp_params.py` | 驗證：text S2、fig. S1 | 每個參數值 5 次、100 週期；5×5 網格與 30 城市實例 | `exp1_tsp_params.csv` |
| exp2_tsp_compare | `exp2_tsp_compare.py` | 驗證：table S14 | 每種方法 10 次、42 城市 | `exp2_tsp_compare.csv` |
| exp3_sorting | `exp3_sorting.py` | 驗證：fig. S2、table S15 | 每種設定 3 次、1000 迭代 | `exp3_entropy_curve.csv`、`exp3_fig8_ants.csv`、`exp3_table2_k1k2.csv` |
| exp4_topic1_we_sense | `exp4_topic1_we_sense.py`（`EXP4_SEEDS`） | D1：Fig. 2F、table S3B | 20 個種子 | `exp4a_private_vs_shared.csv`、`exp4b_perceptual_consistency.csv`、`exp4c_sorting_sensing.csv` |
| exp5_topic2_responsibility | `exp5_topic2_responsibility.py` | D2 早期版本（已由 exp7 取代） | 8 個種子 | `exp5a_provenance.csv`、`exp5b_counterfactual.csv`、`exp5c_sorting_authorship.csv`、`exp5_tsp_event_log.csv`、`exp5_sorting_event_log.csv` |
| exp6_topic3_reversibility | `exp6_topic3_reversibility.py` | D3：Fig. 4C、table S11 | 每個 ρ 4 個種子 | `exp6a_block_unblock.csv`、`exp6b_cut_remove.csv`、`exp6c_sorting_scramble.csv` |
| exp7_topic2_stats | `exp7_topic2_stats.py` | D2：text S4、fig. S5、table S9 | 32 個種子；Shapley 值 10 個 | `exp7_counterfactual_stats.csv`、`exp7_top_vs_random.csv`、`exp7_dispersion.csv`、`exp7_group_shapley.csv` |
| exp8_topic3_controls | `exp8_topic3_controls.py`（`EXP8_SEEDS`） | D3：Fig. 4A–B；table S10、S12 | ρ = 0.3、0.5、0.9 各 50 對 | `exp8_topic3_controls.csv`、`exp8_topic3_stats.csv`、`exp8_trajectories.npz` |
| exp9_microgpt_ants | `exp9_microgpt_ants.py`（`EXP9_SEEDS`、`EXP9_SKIP_D`） | D1：Fig. 1E、Fig. 2A–C；Table 1；table S2–S4 | 20 個種子、30 隻螞蟻、3000 步 | `exp9a_parity.csv`、`exp9b_stigmergy.csv`、`exp9c_dialect.csv` |
| exp10_topic2_learnable | `exp10_topic2_learnable.py`（`EXP10_SEEDS`、`EXP10_SHAPLEY`） | D2：Fig. 3、Table 2、table S6–S7 | 20 個種子（0–19）；Shapley 值 8 個 | `exp10_per_seed.csv`、`exp10_counterfactual_stats.csv`、`exp10_top_vs_random.csv`、`exp10_shapley_gpt.csv`、`exp10_shapley_rule.csv` |
| exp10b_confirmatory | `exp10_topic2_learnable.py`，加 `EXP10_SEED0=1000 EXP10_SHAPLEY=12 EXP10_TAG=b` | D2：Table 2、text S3、fig. S4、table S8 | 20 個種子（1000–1019）；Shapley 值 12 個 | `exp10b_*.csv`（與 exp10 相同的檔案，另加 `exp10b_noise.csv`） |
| exp11_d1_controls | `exp11_d1_controls.py`（`EXP11_SEEDS`） | D1：Fig. 2B（社會學習）、fig. S3、table S4 | 每個條件 20 個種子 | `exp11_per_seed.csv` |
| exp12_learnable_return | `exp12_learnable_return.py`（`EXP12_SEEDS`） | D3：Fig. 4D–F、fig. S6、table S13 | 20 個種子 | `exp12.npy`、`exp12_stats.csv` |
| exp13_grammar_adherence | `exp13_grammar_adherence.py`（`EXP13_SEEDS`） | D1：Fig. 2D–E、table S5 | 20 個種子 | `exp13_grammar.csv`、`exp13_per_seed.csv` |
| fig_data | `fig_data.py`（`FIG_SEEDS_CURVE`、`FIG_SEEDS_BLOCK`） | Fig. 1C–D | 每類螞蟻 20 個種子 | `fig_data.npy` |
| analysis_revision | `analysis_revision.py` | 配對檢定、TOST 與 exp10b 的事前指定檢定 | 讀取 exp9、exp11、exp13、exp10b | `summary_revision.md`（執行紀錄） |
| make_figures | `make_figures.py` | Fig. 1–5 | 讀取 `results/` | `figures/paper/Fig1`–`Fig5`（.pdf、.png） |
| make_supp_figures | `make_supp_figures.py` | figs. S1–S6 | 讀取 `results/` | `figures/paper/FigS1`–`FigS6`（.pdf、.png） |

括號中的環境變數可覆寫該腳本的預設樣本數。exp9 的 (d) 部分（未配對的封鎖再解封）預設略過（`EXP9_SKIP_D=1`），因為 exp12 已以配對分岔取代它。

## 論文各圖表的來源

### 主文

| 項目 | 內容 | 資料 | 腳本 |
|---|---|---|---|
| Fig. 1A–B | 螞蟻與回合的示意圖 | 無 | `make_figures.py` |
| Fig. 1C–D | 費洛蒙場；累積送達量 | `fig_data.npy` | `fig_data.py`、`make_figures.py` |
| Fig. 1E | 相對規則螞蟻的產量 | `exp9a_parity.csv` | `exp9_microgpt_ants.py` |
| Fig. 2A | 不同介質下的送達量 | `exp9b_stigmergy.csv` | `exp9_microgpt_ants.py` |
| Fig. 2B–C | 分散度；等價檢定 | `exp13_per_seed.csv`、`exp11_per_seed.csv` | `exp13_grammar_adherence.py`、`exp11_d1_controls.py` |
| Fig. 2D–E | 合法質量；文法內分散度 | `exp13_per_seed.csv` | `exp13_grammar_adherence.py` |
| Fig. 2F | 旅行推銷員問題中的集體增益 | `exp4a_private_vs_shared.csv` | `exp4_topic1_we_sense.py` |
| Fig. 3 | 痕跡與原因 | `exp10_shapley_gpt.csv`、`exp10_shapley_rule.csv`、`exp10_counterfactual_stats.csv` | `exp10_topic2_learnable.py` |
| Fig. 4A–B | 當下表現、介質、存檔 | `exp8_topic3_stats.csv` | `exp8_topic3_controls.py` |
| Fig. 4C | 費洛蒙半衰期 | `exp6a_block_unblock.csv` | `exp6_topic3_reversibility.py` |
| Fig. 4D–F | 配對回歸分岔 | `exp12.npy` | `exp12_learnable_return.py` |
| Fig. 5 | 總結示意圖 | 無 | `make_figures.py` |
| Table 1 | 規則與可學習蟻群的產量 | `exp9a_parity.csv` | `exp9_microgpt_ants.py` |
| Table 2 | 痕跡占比與 Shapley 占比 | `exp10_shapley_*.csv`、`exp10b_shapley_*.csv` | `exp10_topic2_learnable.py` |

### Supplementary Materials

| 項目 | 資料 | 腳本 |
|---|---|---|
| fig. S1 | `exp1_tsp_params.csv` | `exp1_tsp_params.py` |
| fig. S2 | `exp3_entropy_curve.csv`、`exp3_fig8_ants.csv` | `exp3_sorting.py` |
| fig. S3 | `exp11_per_seed.csv` | `exp11_d1_controls.py` |
| fig. S4 | `exp10b_shapley_gpt.csv`、`exp10b_shapley_rule.csv` | exp10b |
| fig. S5 | `exp7_group_shapley.csv`、`exp7_counterfactual_stats.csv` | `exp7_topic2_stats.py` |
| fig. S6 | `exp12.npy` | `exp12_learnable_return.py` |
| table S1 | 文獻比較 | 無 |
| table S2 | `exp9a_parity.csv` | `exp9_microgpt_ants.py` |
| table S3 | `exp9b_stigmergy.csv`、`exp4a_private_vs_shared.csv` | exp9、exp4 |
| table S4 | `exp9c_dialect.csv`、`exp13_per_seed.csv`、`exp11_per_seed.csv` | exp9、exp13、exp11；`analysis_revision.py` |
| table S5 | `exp13_grammar.csv`、`exp13_per_seed.csv` | `exp13_grammar_adherence.py` |
| table S6 | `exp10_counterfactual_stats.csv`、`exp10_top_vs_random.csv` | exp10 |
| table S7 | `exp10_shapley_gpt.csv`、`exp10_shapley_rule.csv` | exp10 |
| table S8 | `exp10b_*.csv` | exp10b；`analysis_revision.py` |
| table S9 | `exp7_counterfactual_stats.csv`、`exp7_top_vs_random.csv`、`exp7_group_shapley.csv` | exp7 |
| table S10 | `exp8_topic3_stats.csv`（`control1` 部分） | exp8 |
| table S11 | `exp6a_block_unblock.csv`、`exp6b_cut_remove.csv` | exp6 |
| table S12 | `exp8_topic3_stats.csv`（`control2` 部分）、`exp8_topic3_controls.csv` | exp8 |
| table S13 | `exp12_stats.csv`、`exp12.npy` | exp12 |
| table S14 | `exp2_tsp_compare.csv` | exp2 |
| table S15 | `exp3_table2_k1k2.csv` | exp3 |

## 舊版檔案

以下檔案為完整起見保留，但最終圖表沒有使用：

- `fig_data_5seeds.npy`：`fig_data.npy` 較早的 5 種子版本。
- `fig_data_null.npy`：Fig. 4F 較早的 10 種子零假設資料，只有在 `exp12.npy` 不存在時才會被 `make_figures.py` 使用（由 `fig_data_null.py` 產生）。
- `exp9d_block_unblock.csv`：exp9 早期未配對的封鎖再解封結果，已由 exp12 取代。
- exp5 的輸出：旅行推銷員責任分析的早期 8 種子版本，已由 exp7 取代；其事件紀錄可作為事件契約的範例。
- `example_custom_policy.csv`：自訂策略範例的輸出，論文未使用。
