# GRAFCET 模型（自動產生，請勿手改）

[English](../en/GRAFCET_MODELS.md) | 中文

由 `docs/gen_model_docs.py` 從程式中的模型定義產生。修改行為時請改模型定義，再重新產生本檔。

## 螞蟻–TSP 最佳化系統

### 主控制器（G0，IDEF0 A0，n=1）

Gate 2 模型審查：通過

| Step | IDEF0 | Action (mode) | 轉移 | 條件 | 下一狀態 |
|---|---|---|---|---|---|
| X0 (init) | A1 | a1_initialize (P1) | T0 | init_done | X1 |
| X1 | A2 | — (N) | T1 | G2.X24（巡迴建構完成） | X2 |
| X2 | A3 | a3_evaluate (P1) | T2 | eval_done | X3 |
| X3 | A4 | a4_update_pheromone (P1) | T3 | update_done | X4 |
| X4 | A5 | a5_record_and_events (P1) | T4a | record_done ∧ ¬finished | X1 |
| X4 | A5 | a5_record_and_events (P1) | T4b | record_done ∧ finished | X5 |
| X5 | A5 | a6_report (P1) | — | (terminal) | — |

```mermaid
flowchart TD
    X0[["X0<br/>初始化"]]
    X1["X1<br/>建構巡迴（啟動 G2）"]
    X2["X2<br/>評估巡迴"]
    X3["X3<br/>更新費洛蒙"]
    X4["X4<br/>紀錄／事件／終止判斷"]
    X5["X5<br/>輸出結果"]
    T0{{"T0: init_done"}}
    X0 --> T0
    T0 --> X1
    T1{{"T1: G2.X24（巡迴建構完成）"}}
    X1 --> T1
    T1 --> X2
    T2{{"T2: eval_done"}}
    X2 --> T2
    T2 --> X3
    T3{{"T3: update_done"}}
    X3 --> T3
    T3 --> X4
    T4a{{"T4a: record_done ∧ ¬finished"}}
    X4 --> T4a
    T4a --> X1
    T4b{{"T4b: record_done ∧ finished"}}
    X4 --> T4b
    T4b --> X5
```

### 巡迴建構子控制器（G2，IDEF0 A2，n=1）

Gate 2 模型審查：通過

| Step | IDEF0 | Action (mode) | 轉移 | 條件 | 下一狀態 |
|---|---|---|---|---|---|
| X20 (init) | A2 | — (N) | T20 | G0.X1 | X21 |
| X21 | A21 | a21_place_ants (P1) | T21 | placed | X22 |
| X22 | A22 | a22_step_all_ants (N) | T22 | tours_complete（tabu 已滿） | X23 |
| X23 | A23 | a23_close_tours (P1) | T23 | closed | X24 |
| X24 | A2 | — (N) | T24 | ¬G0.X1 | X20 |

```mermaid
flowchart TD
    X20[["X20<br/>等待啟動"]]
    X21["X21<br/>放置螞蟻"]
    X22["X22<br/>全體前進一步"]
    X23["X23<br/>閉合巡迴"]
    X24["X24<br/>完成（回報 G0）"]
    T20{{"T20: G0.X1"}}
    X20 --> T20
    T20 --> X21
    T21{{"T21: placed"}}
    X21 --> T21
    T21 --> X22
    T22{{"T22: tours_complete（tabu 已滿）"}}
    X22 --> T22
    T22 --> X23
    T23{{"T23: closed"}}
    X23 --> T23
    T23 --> X24
    T24{{"T24: ¬G0.X1"}}
    X24 --> T24
    T24 --> X20
```

## 螞蟻–自動分揀系統

### 主控制器（G0，IDEF0 A0，n=1）

Gate 2 模型審查：通過

| Step | IDEF0 | Action (mode) | 轉移 | 條件 | 下一狀態 |
|---|---|---|---|---|---|
| X0 (init) | A1 | a1_initialize (P1) | T0 | init_done | X1 |
| X1 | A2 | a_iteration_clock (N) | T1 | iteration_done | X2 |
| X2 | A3 | a3_measure (P1) | T2 | measure_done | X3 |
| X3 | A4 | a4_record_and_events (P1) | T3a | record_done ∧ ¬finished | X1 |
| X3 | A4 | a4_record_and_events (P1) | T3b | record_done ∧ finished | X4 |
| X4 | A4 | a5_report (P1) | — | (terminal) | — |

```mermaid
flowchart TD
    X0[["X0<br/>初始化"]]
    X1["X1<br/>運行一回合"]
    X2["X2<br/>量測空間熵"]
    X3["X3<br/>紀錄／事件／終止判斷"]
    X4["X4<br/>輸出結果"]
    T0{{"T0: init_done"}}
    X0 --> T0
    T0 --> X1
    T1{{"T1: iteration_done"}}
    X1 --> T1
    T1 --> X2
    T2{{"T2: measure_done"}}
    X2 --> T2
    T2 --> X3
    T3a{{"T3a: record_done ∧ ¬finished"}}
    X3 --> T3a
    T3a --> X1
    T3b{{"T3b: record_done ∧ finished"}}
    X3 --> T3b
    T3b --> X4
```

### 族群控制器（每隻螞蟻一個同構控制器）（G2，IDEF0 A2，n=40）

Gate 2 模型審查：通過

| Step | IDEF0 | Action (mode) | 轉移 | 條件 | 下一狀態 |
|---|---|---|---|---|---|
| X20 (init) | A21 | a21_move (N) | T20 | G0.X1 ∧ on_object | X21 |
| X21 | A22 | a22_eval_pick (P1) | T21a | pick_eval_done ∧ picked | X22 |
| X21 | A22 | a22_eval_pick (P1) | T21b | pick_eval_done ∧ ¬picked | X20 |
| X22 | A21 | a21_move (N) | T22 | G0.X1 ∧ on_empty_cell | X23 |
| X23 | A23 | a23_eval_drop (P1) | T23a | drop_eval_done ∧ dropped | X20 |
| X23 | A23 | a23_eval_drop (P1) | T23b | drop_eval_done ∧ ¬dropped | X22 |

```mermaid
flowchart TD
    X20[["X20<br/>空手漫遊"]]
    X21["X21<br/>評估拿起"]
    X22["X22<br/>搬運漫遊"]
    X23["X23<br/>評估放下"]
    T20{{"T20: G0.X1 ∧ on_object"}}
    X20 --> T20
    T20 --> X21
    T21a{{"T21a: pick_eval_done ∧ picked"}}
    X21 --> T21a
    T21a --> X22
    T21b{{"T21b: pick_eval_done ∧ ¬picked"}}
    X21 --> T21b
    T21b --> X20
    T22{{"T22: G0.X1 ∧ on_empty_cell"}}
    X22 --> T22
    T22 --> X23
    T23a{{"T23a: drop_eval_done ∧ dropped"}}
    X23 --> T23a
    T23a --> X20
    T23b{{"T23b: drop_eval_done ∧ ¬dropped"}}
    X23 --> T23b
    T23b --> X22
```

## microGPT 螞蟻覓食系統

### 感覺運動時脈（G0，IDEF0 A0，n=1）

Gate 2 模型審查：通過

| Step | IDEF0 | Action (mode) | 轉移 | 條件 | 下一狀態 |
|---|---|---|---|---|---|
| X0 (init) | A1 | a1_initialize (P1) | T0 | init_done | X1 |
| X1 | A21 | a21_perceive (P1) | T1 | obs_ready | X2 |
| X2 | A22 | a22_decide (P1) | T2 | actions_ready | X3 |
| X3 | A23 | a23_act (P1) | T3 | act_done | X4 |
| X4 | A3 | a3_medium (P1) | T4a | step_done ∧ ¬epoch_end | X1 |
| X4 | A3 | a3_medium (P1) | T4b | step_done ∧ epoch_end | X5 |
| X5 | A4 | a4_learn (P1) | T5 | learn_done | X6 |
| X6 | A5 | a5_record (P1) | T6a | record_done ∧ ¬finished | X1 |
| X6 | A5 | a5_record (P1) | T6b | record_done ∧ finished | X7 |
| X7 | A5 | a6_report (P1) | — | (terminal) | — |

```mermaid
flowchart TD
    X0[["X0<br/>初始化"]]
    X1["X1<br/>感知編碼"]
    X2["X2<br/>決策（核心）"]
    X3["X3<br/>行動執行"]
    X4["X4<br/>介質更新"]
    X5["X5<br/>線上學習"]
    X6["X6<br/>量測／事件"]
    X7["X7<br/>輸出結果"]
    T0{{"T0: init_done"}}
    X0 --> T0
    T0 --> X1
    T1{{"T1: obs_ready"}}
    X1 --> T1
    T1 --> X2
    T2{{"T2: actions_ready"}}
    X2 --> T2
    T2 --> X3
    T3{{"T3: act_done"}}
    X3 --> T3
    T3 --> X4
    T4a{{"T4a: step_done ∧ ¬epoch_end"}}
    X4 --> T4a
    T4a --> X1
    T4b{{"T4b: step_done ∧ epoch_end"}}
    X4 --> T4b
    T4b --> X5
    T5{{"T5: learn_done"}}
    X5 --> T5
    T5 --> X6
    T6a{{"T6a: record_done ∧ ¬finished"}}
    X6 --> T6a
    T6a --> X1
    T6b{{"T6b: record_done ∧ finished"}}
    X6 --> T6b
    T6b --> X7
```

### 任務意向（族群控制器）（G2，IDEF0 A2，n=30）

Gate 2 模型審查：通過

| Step | IDEF0 | Action (mode) | 轉移 | 條件 | 下一狀態 |
|---|---|---|---|---|---|
| X20 (init) | A2 | — (N) | T20t | ep_len ≥ max_ep（例外） | X23 |
| X20 (init) | A2 | — (N) | T20 | took | X21 |
| X21 | A2 | — (N) | T21t | ep_len ≥ max_ep（例外） | X23 |
| X21 | A2 | — (N) | T21 | delivered | X22 |
| X22 | A4 | a24_record_success (P1) | T22 | recorded | X20 |
| X23 | A2 | a25_reset_timeout (P1) | T23 | reset_done | X20 |

```mermaid
flowchart TD
    X20[["X20<br/>搜尋"]]
    X21["X21<br/>攜帶返巢"]
    X22["X22<br/>成功回合：寫入緩衝"]
    X23["X23<br/>逾時：捨棄回合"]
    T20t{{"T20t: ep_len ≥ max_ep（例外）"}}
    X20 --> T20t
    T20t --> X23
    T20{{"T20: took"}}
    X20 --> T20
    T20 --> X21
    T21t{{"T21t: ep_len ≥ max_ep（例外）"}}
    X21 --> T21t
    T21t --> X23
    T21{{"T21: delivered"}}
    X21 --> T21
    T21 --> X22
    T22{{"T22: recorded"}}
    X22 --> T22
    T22 --> X20
    T23{{"T23: reset_done"}}
    X23 --> T23
    T23 --> X20
```
