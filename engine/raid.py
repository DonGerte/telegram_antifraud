"""Advanced raid detection and containment modes."""
import time
from collections import deque, defaultdict

# buffer de joins recientes por chat
recent_joins = defaultdict(lambda: deque(maxlen=1000))

# raid containment state: chat_id -> mode
MODES = {"normal": 0, "slow": 1, "bunker": 2}  # escalating severity
containment_mode = defaultdict(lambda: "normal")
mode_start_time = {}


def record_join(chat_id: int, user_id: int, ts=None):
    """Record a user joining a chat."""
    ts = ts or time.time()
    recent_joins[chat_id].append((user_id, ts))


def detect_raid(chat_id: int, threshold=20, window=300):
    """Detect if a raid is happening (joins spike in window)."""
    now = time.time()
    joins = [t for (_, t) in recent_joins[chat_id] if now - t < window]
    return len(joins) >= threshold


def get_raid_stats(chat_id: int, window=300):
    """Get detailed raid statistics for a chat."""
    now = time.time()
    all_joins = [(uid, t) for (uid, t) in recent_joins[chat_id] if now - t < window]
    return {
        "join_count": len(all_joins),
        "unique_users": len(set(uid for uid, _ in all_joins)),
        "window_seconds": window,
        "avg_joins_per_min": len(all_joins) / (window / 60) if window > 0 else 0
    }


def enter_containment(chat_id: int, mode: str = "slow"):
    """Activate containment mode (slow/bunker)."""
    if mode not in MODES:
        return False
    containment_mode[chat_id] = mode
    mode_start_time[chat_id] = time.time()
    return True


def exit_containment(chat_id: int):
    """Deactivate containment mode."""
    containment_mode[chat_id] = "normal"
    if chat_id in mode_start_time:
        del mode_start_time[chat_id]


def get_containment_mode(chat_id: int):
    """Get current containment mode for a chat."""
    return containment_mode.get(chat_id, "normal")


def is_in_bunker(chat_id: int):
    """Check if chat is in bunker mode (lock down)."""
    return get_containment_mode(chat_id) == "bunker"


def is_in_slow(chat_id: int):
    """Check if chat is in slow mode."""
    return get_containment_mode(chat_id) == "slow"


def get_containment_duration(chat_id: int):
    """Get how long containment has been active."""
    if chat_id not in mode_start_time:
        return 0
    return time.time() - mode_start_time[chat_id]


def should_auto_exit_containment(chat_id: int, timeout_seconds=1800):
    """Check if containment should expire (default 30 min)."""
    if get_containment_mode(chat_id) == "normal":
        return False
    return get_containment_duration(chat_id) >= timeout_seconds


def auto_cycle_containment(chat_id: int):
    """Auto-exit containment if duration exceeded."""
    if should_auto_exit_containment(chat_id):
        exit_containment(chat_id)
        return True
    return False
