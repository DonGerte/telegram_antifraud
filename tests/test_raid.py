import time

from engine import raid


def test_record_and_detect():
    raid.recent_joins.clear()
    chat=100
    now=time.time()
    # add 5 joins within window
    for i in range(5):
        raid.record_join(chat, i, ts=now - 10)
    assert raid.detect_raid(chat, threshold=5, window=60)
    assert not raid.detect_raid(chat, threshold=6, window=60)


def test_window_expiration():
    raid.recent_joins.clear()
    chat=200
    now=time.time()
    raid.record_join(chat, 1, ts=now - 1000)
    assert not raid.detect_raid(chat, threshold=1, window=60)
