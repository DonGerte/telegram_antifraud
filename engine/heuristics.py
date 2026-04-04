import hashlib
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

from engine import honeypot

# in-memory tracking for velocity and repetition (per runtime)
user_message_times = defaultdict(list)
user_message_hashes = defaultdict(list)


def compute_signal(message: Dict) -> Tuple[str, float]:
    """Return signal type and a numeric value for suspicious message."""
    sig_type = "none"
    value = 0.0

    uid = None
    if message.get("from"):
        uid = message["from"].get("id")

    text = message.get("text") or message.get("caption") or ""

    # 1. link detection
    if text and ("http" in text or honeypot.LINK_PATTERN.search(text)):
        sig_type = "link"
        value += 5

    # 2. honeypot strategy
    if text and honeypot.check_honeypot(text):
        sig_type = "honeypot"
        value += 10

    # 3. velocity
    if uid:
        now = time.time()
        user_message_times[uid] = [t for t in user_message_times[uid] if now - t < 3600]
        user_message_times[uid].append(now)
        msg_count = len(user_message_times[uid])
        if msg_count > 50:
            value += 3
            if sig_type == "none":
                sig_type = "velocity"
        elif msg_count > 20:
            value += 1

    # 4. repetition
    if uid and text:
        text_hash = hashlib.md5(text.lower().strip().encode()).hexdigest()
        user_message_hashes[uid].append(text_hash)
        user_message_hashes[uid] = user_message_hashes[uid][-100:]
        repeat_count = sum(1 for h in user_message_hashes[uid] if h == text_hash)
        if repeat_count > 3:
            value += 4
            if sig_type == "none":
                sig_type = "repetition"

    return sig_type, value
