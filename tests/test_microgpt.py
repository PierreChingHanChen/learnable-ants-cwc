"""microGPT Datapath 單元測試（F-02～F-06）。"""
import numpy as np
import pytest

from miat_ants.microgpt import MicroGPT, GPTConfig


def _rand_model(A=2, seed=1):
    cfg = GPTConfig(vocab_size=7, block_size=6, n_embd=8, n_head=2)
    m = MicroGPT(cfg, n_agents=A, seed=seed)
    rng = np.random.default_rng(0)
    for k in m.p:
        m.p[k] = rng.normal(0, 0.3, m.p[k].shape)
    return m


def test_gradcheck():
    m = _rand_model()
    rng = np.random.default_rng(0)
    idx = rng.integers(0, 7, (2, 3, 5)); tg = rng.integers(0, 7, (2, 3, 5)); mask = rng.random((2, 3, 5)) < 0.6

    def L():
        lg = m.forward(idx, cache=True)
        l, d = m.loss_and_grad_logits(lg, tg, mask)
        return l.sum(), d
    _, d = L()
    g = m.backward(d)
    worst = 0.0
    for k in m.p:
        for _ in range(5):
            i = tuple(rng.integers(0, s) for s in m.p[k].shape)
            old = m.p[k][i]
            m.p[k][i] = old + 1e-5; lp, _ = L()
            m.p[k][i] = old - 1e-5; lm, _ = L()
            m.p[k][i] = old
            num, an = (lp - lm) / 2e-5, g[k][i]
            if abs(num) + abs(an) > 1e-7:
                worst = max(worst, abs(num - an) / (abs(num) + abs(an)))
    assert worst < 1e-5


def test_masked_loss_ignores_unmasked_positions():
    m = _rand_model(A=1)
    rng = np.random.default_rng(1)
    idx = rng.integers(0, 7, (1, 2, 5)); tg = rng.integers(0, 7, (1, 2, 5))
    mask = np.zeros((1, 2, 5), bool); mask[0, :, 2] = True
    lg = m.forward(idx)
    l1, _ = m.loss_and_grad_logits(lg, tg, mask)
    tg2 = tg.copy(); tg2[0, :, 0] = (tg2[0, :, 0] + 1) % 7      # 改變未遮罩位置的目標
    l2, _ = m.loss_and_grad_logits(lg, tg2, mask)
    assert l1 == pytest.approx(l2)


def test_overfit_fixed_sequence():
    cfg = GPTConfig(vocab_size=5, block_size=8, n_embd=16, n_head=4)
    m = MicroGPT(cfg, 1, seed=0)
    seq = np.array([0, 1, 2, 3, 4, 1, 2, 3, 4])
    idx, tg = seq[None, None, :-1], seq[None, None, 1:]
    mask = np.ones_like(tg, bool)
    for _ in range(400):
        loss = m.train_step(idx, tg, mask, lr=2e-2)
    assert loss[0] < 0.05


def test_param_count_microgpt_scale():
    n = MicroGPT(GPTConfig(vocab_size=24)).n_params()
    assert 3000 <= n <= 6000


def test_batched_equals_single_and_isolated_update():
    m = _rand_model(A=3)
    rng = np.random.default_rng(2)
    idx = rng.integers(0, 7, (3, 2, 4))
    full = m.forward(idx)
    one = m.forward(idx[1:2], np.array([1]))
    assert np.allclose(full[1], one[0])
    before = {k: v.copy() for k, v in m.p.items()}
    tg = rng.integers(0, 7, (1, 2, 4)); mask = np.ones((1, 2, 4), bool)
    m.train_step(idx[1:2], tg, mask, ids=np.array([1]), lr=1e-2)
    for k in m.p:
        assert np.array_equal(m.p[k][0], before[k][0]) and np.array_equal(m.p[k][2], before[k][2])
    assert any(not np.array_equal(m.p[k][1], before[k][1]) for k in m.p)


def test_save_load_roundtrip(tmp_path):
    m = _rand_model(A=1)
    p = tmp_path / "w.npz"
    m.save(str(p))
    m2 = MicroGPT.load(str(p))
    idx = np.zeros((1, 1, 3), int)
    assert np.allclose(m.forward(idx), m2.forward(idx))
