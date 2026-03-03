import time
import pytest

from engine import scoring


def test_add_and_compute_score_empty():
    # ensure score of unknown user is zero
    assert scoring.compute_score(9999) == 0.0


def test_add_signal_and_score():
    uid = 1
    scoring.user_signals.clear()
    scoring.add_signal(uid, "test", 10, -100, ts=time.time() - 3600)
    # after one hour decayed by decay^1 = 0.99
    score = scoring.compute_score(uid)
    # allow small floating precision error
    assert 9.89 < score < 10.1


def test_decay_accumulates():
    uid = 2
    scoring.user_signals.clear()
    now = time.time()
    scoring.add_signal(uid, "a", 1, -1, ts=now - 0)
    scoring.add_signal(uid, "b", 1, -1, ts=now - 3600)
    # second signal should be slightly lower weight
    score = scoring.compute_score(uid)
    assert score < 2 and score > 1.9
