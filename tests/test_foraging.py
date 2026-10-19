"""覓食子系統：序列契約、感知、行動、守恆、事件一致、Token 走查（F-01、F-07～F-15）。"""
import numpy as np
import pytest

from miat_ants.core.field_medium import FieldMedium
from miat_ants.foraging import vocab as V
from miat_ants.foraging import ForagingSystem, ForagingConfig, run_foraging
from miat_ants.foraging.cores import GPTCore, RuleCore
from miat_ants.foraging.world import World, open_field, double_bridge


def test_vocab_and_sequence_contract():
    assert V.V == 24 and V.ACTION_MASK.sum() == 8 and V.OBS_MASK.sum() == 15
    V.check_sequence(V.encode(".NFAFXT1f0D"))
    with pytest.raises(ValueError):
        V.check_sequence(V.encode(".FN"))          # 行動詞出現在感知位置
    with pytest.raises(ValueError):
        V.check_sequence(V.encode(".NA"))          # 感知詞出現在行動位置


def test_training_windows_mask_only_actions():
    seqs = [V.encode(".NFNFAFXT1f1f0D")]
    idx, tgt, msk = V.training_windows(seqs, 4, 16, np.random.default_rng(0))
    assert np.all(V.ACTION_MASK[tgt[msk]])
    assert not np.any(V.ACTION_MASK[tgt[~msk & (tgt != V.BOS_ID)]])


def _world(spec=None, A=1):
    spec = spec or open_field()
    med = FieldMedium(*spec.shape, A, rho=0.9)
    return World(spec, A, med, np.random.default_rng(0)), med


def test_perception_cases():
    w, med = _world()
    k = np.array([0])
    w.pos[0] = (10, 10); w.heading[0] = 0          # 朝東
    assert V.ITOS[w.perceive(k)[0]] == "N"
    w.food[10, 11] = 1
    assert V.ITOS[w.perceive(k)[0]] == "A"
    w.food[10, 11] = 0; w.food[9, 11] = 1          # 左前（NE）
    assert V.ITOS[w.perceive(k)[0]] == "B"
    w.food[9, 11] = 0
    med.tau[11, 11] = 1.0                          # 右前（SE）有費洛蒙
    assert V.ITOS[w.perceive(k)[0]] == "S"
    med.cut()
    assert V.ITOS[w.perceive(k)[0]] == "N"         # 介質被切斷 → 無線索
    w.pos[0] = (1, 10); w.heading[0] = 6           # 朝北，前方是牆
    assert V.ITOS[w.perceive(k)[0]] == "W"
    w.carrying[0] = True
    w.pos[0] = (16, 5); w.heading[0] = 0           # 巢在 (16,16)：正前
    assert V.ITOS[w.perceive(k)[0]] == "1"
    w.heading[0] = 4                               # 朝西：巢在後
    assert V.ITOS[w.perceive(k)[0]] == "3"
    w.heading[0] = 6                               # 朝北：巢在右
    assert V.ITOS[w.perceive(k)[0]] == "2"
    w.pos[0] = (16, 16)
    assert V.ITOS[w.perceive(k)[0]] == "0"


def test_actions_take_deliver_mark_and_noop():
    w, med = _world()
    k = np.array([0])
    w.pos[0] = (5, 5); w.heading[0] = 0
    f0 = w.food_total()
    r = w.apply(k, np.array([V.STOI["D"]]))        # 無效：沒攜帶 → no-op
    assert not r.delivered.any()
    r = w.apply(k, np.array([V.STOI["T"]]))
    assert r.took[0] and w.carrying[0] and w.heading[0] == 4
    r = w.apply(k, np.array([V.STOI["f"]]))
    assert r.marked[0] and r.moved[0]
    med.commit()
    assert med.tau[5, 4] == pytest.approx(1.0)
    w.pos[0] = (16, 16)
    r = w.apply(k, np.array([V.STOI["D"]]))
    assert r.delivered[0] and w.delivered_total == 1
    assert w.food_total() == f0
    with pytest.raises(ValueError):
        w.apply(k, np.array([V.STOI["N"]]))        # 感知詞不可作為行動


def test_field_medium_modes():
    m = FieldMedium(4, 4, 2, rho=0.5, mode="private")
    m.deposit(np.array([0]), np.array([[1, 1]]), 2.0)
    m.commit()
    cells = np.array([[[1, 1]], [[1, 1]]])
    v = m.sense(np.array([0, 1]), cells)
    assert v[0, 0] == 2.0 and v[1, 0] == 0.0       # private：只讀得到自己的
    m.commit()
    assert m.sense(np.array([0]), cells[:1])[0, 0] == 1.0


def test_rule_core_contract_and_gpt_decide_only_actions():
    rng = np.random.default_rng(0)
    rc = RuleCore(2, rng)
    out = rc.decide([0, 1], [V.encode(".X"), V.encode(".N")])
    assert V.ITOS[out[0]] == "T" and V.ACTION_MASK[out].all()
    with pytest.raises(ValueError):
        rc.decide([0], [V.encode(".NF")])       # 最後一個不是感知詞
    gc = GPTCore(3, rng, base=None)
    ctxs = [V.encode(".N"), V.encode(".NFN"), V.encode(".NFNFA")]
    acts = gc.decide([0, 1, 2], ctxs)
    assert V.ACTION_MASK[acts].all()


def test_food_conservation_events_and_token_walk():
    sysm = ForagingSystem(ForagingConfig(core="rule", seed=3, max_steps=300, max_ep_steps=60,
                                         record_trace=True))
    r = sysm.run()
    w = r.world
    assert w.food_total() == w.food0
    assert len(r.events.filter("deliver")) == w.delivered_total
    # 正常路徑：X0→X1→X2→X3→X4→X1 …，最後 X7
    seq = []
    for _, act, _ in sysm.g0.trace:
        if not seq or seq[-1] != act:
            seq.append(act)
    flat = [a[0] for a in seq]
    assert flat[:6] == ["X0", "X1", "X2", "X3", "X4", "X1"] and flat[-1] == "X7"
    assert "X5" in flat and "X6" in flat
    # 例外路徑：回合逾時（max_ep_steps=60）必定發生並被處理
    eps = r.events.filter("episode_end")
    assert any(not e.payload["success"] for e in eps)
    assert all(e.payload["length"] <= 60 for e in eps if not e.payload["success"])


def test_individual_learning_isolated_and_reproducible():
    cfg = dict(core="gpt", base_weights=None, seed=4, max_steps=100, steps_per_epoch=50, n_ants=6)
    s = ForagingSystem(ForagingConfig(**cfg))
    r = s.run()
    p = r.core.model.p
    learned = [k for k, b in s.buffers.items() if b]
    untouched = [k for k, b in s.buffers.items() if not b]
    base = ForagingSystem(ForagingConfig(**{**cfg, "learn": False})).run().core.model.p
    for k in untouched:
        assert np.array_equal(p["lm"][k], base["lm"][k])
    for k in learned:
        assert not np.array_equal(p["lm"][k], base["lm"][k])
    r2 = ForagingSystem(ForagingConfig(**cfg)).run()
    assert r2.delivered == r.delivered
    assert np.array_equal(r2.core.model.p["lm"], p["lm"])


def test_double_bridge_gates_counted():
    r = run_foraging(map_name="double_bridge", core="rule", seed=1, max_steps=400)
    assert r.history["gate_short"][-1] + r.history["gate_long"][-1] > 0


def test_dialect_metrics():
    from miat_ants.foraging.analysis import dispersion, drift
    p = np.full((3, 4, 8), 1 / 8)
    assert dispersion(p) == pytest.approx(0) and drift(p, p[0]) == pytest.approx(0)
    q = p.copy(); q[1, :, :] = 0; q[1, :, 0] = 1
    assert dispersion(q) > 0 and drift(q, p[0]) > 0


# ---------------------------------------------------------------- exp10 支援：來源追蹤、分岔、指定移除、重設亂數
def _fg(**kw):
    base = dict(map_name="double_bridge", core="gpt", learn=True, n_ants=8, max_steps=300,
                seed=3, track_provenance=True)
    base.update(kw)
    return ForagingSystem(ForagingConfig(**base))


def test_fork_replays_identically():
    """分岔後不加任何事件 → 與原系統繼續執行的結果逐步相同（配對設計的前提）。"""
    s = _fg().run_until(150)
    a = s.fork().resume()
    b = s.resume()
    assert a.history["delivered"] == b.history["delivered"]
    assert np.array_equal(a.world.pos, b.world.pos)
    for k in a.core.model.p:
        assert np.array_equal(a.core.model.p[k], b.core.model.p[k])


def test_fork_matches_uninterrupted_run():
    full = _fg().run()
    part = _fg().run_until(150).fork().resume()
    assert full.history["delivered"] == part.history["delivered"]


def test_provenance_conservation_in_foraging():
    r = _fg().run()
    m = r.world.medium
    assert np.allclose(m.contrib.sum(0), m.tau)
    assert len(r.history["contrib_trail"]) == len(r.history["step"])


def test_remove_ids_and_reseed():
    from miat_ants.core.events import Event, PRIORITY_ENV
    s = _fg().run_until(150)
    rm = s.fork(events_now=[Event("remove_ants", 150, "experiment", {"ids": [0, 1, 2]}, PRIORITY_ENV)])
    assert not rm.alive[[0, 1, 2]].any() and rm.alive[3:].all()
    before = rm.world.delivered_by[[0, 1, 2]].copy()
    r = rm.resume()
    assert np.array_equal(r.world.delivered_by[[0, 1, 2]], before)     # 被移除者不再有任何產出
    ev = lambda sd: [Event("reseed", 150, "experiment", {"seed": sd}, PRIORITY_ENV)]
    x = s.fork(events_now=ev(7)).resume().history["delivered"]
    y = s.fork(events_now=ev(7)).resume().history["delivered"]
    assert x == y                                                       # 同一重設種子 → 可重現


def test_run_until_pauses_after_recording_that_epoch():
    s = _fg(core="rule").run_until(200)
    assert s.steps == 200 and s.hist["step"][-1] == 200
