"""實驗統計工具的單元測試。"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "experiments"))
from common import bootstrap_ci, holm, paired_stats  # noqa: E402


def test_holm():
    adj = holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.06, 0.06])


def test_paired_stats_and_ci():
    d = np.random.default_rng(0).normal(1.0, 0.5, 40)
    st = paired_stats(d)
    assert st["ci_lo"] < 1.0 < st["ci_hi"] or st["ci_lo"] < st["mean"] < st["ci_hi"]
    assert st["p"] < 1e-4 and st["d_z"] > 1
    assert paired_stats(np.zeros(10))["p"] == 1.0
    lo, hi = bootstrap_ci([1, 1, 1, 1])
    assert lo == hi == 1
