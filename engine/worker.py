import json
import logging
import time

try:
    import redis
except ImportError:
    redis = None

import config
from engine import scoring, clusters, raid, shadow_mod
from engine.rules import RuleEngine
from engine.logger import get_logger, log_event, log_action, log_score_update

# Setup structured logging
log = get_logger("worker")

redis_client = None
if redis and config.REDIS_URL:
    try:
        redis_client = redis.from_url(config.REDIS_URL)
    except Exception:
        redis_client = None
IN_QUEUE = "data_bus"
OUT_QUEUE = "action_bus"

# load decision rules if available
rule_engine = None
try:
    rule_engine = RuleEngine.load_file(config.RULES_FILE)
except Exception as e:
    if log:
        log.warning(f"could not load rule engine: {e}")
    rule_engine = None



def process_message(event: dict):
    uid = event.get("uid")
    chat = event.get("chat")
    sig_type = event.get("signal_type")
    value = event.get("value", 0.0)
    ts = event.get("ts", time.time())

    # store raw signal in scoring engine
    scoring.add_signal(uid, sig_type, value, chat, ts=ts)

    # correlate accounts mentioned together
    for other in event.get("correlated_uids", []):
        clusters.add_edge(uid, other)

    # compute score and apply rules
    score = scoring.compute_score(uid)
    cluster_sz = len(clusters.get_cluster(uid))
    
    log_score_update(log, uid, score, chat, sig_type)
    
    # prepare context for rule engine
    if rule_engine:
        ctx = {
            "score": score,
            "cluster_size": cluster_sz,
            "signals": [sig_type],
            "raid_detected": raid.detect_raid(chat)
        }
        actions = rule_engine.evaluate(ctx)
        for act in actions:
            action_name = act.get("action")
            reason = act.get("reason")
            log_action(log, action_name, user_id=uid, chat_id=chat, reason=reason)
            if action_name != "none":
                enqueue_action(action_name, {
                    "uid": uid, "chat": chat, "reason": reason, "rule": act.get("rule")
                })
    else:
        # fallback: simple threshold
        if score > 50:
            log_action(log, "kick", user_id=uid, chat_id=chat, reason="score>50")
            enqueue_action("kick", {"uid": uid, "chat": chat, "reason": "score>50"})


def process_join(event: dict):
    chat = event.get("chat")
    uid = event.get("uid")
    ts = event.get("ts", time.time())
    raid.record_join(chat, uid, ts=ts)
    
    # Check for raid
    if raid.detect_raid(chat, threshold=config.RAID_THRESHOLD, window=config.RAID_WINDOW):
        stats = raid.get_raid_stats(chat)
        log_event(log, "raid_detected", chat_id=chat, stats=stats)
        raid.enter_containment(chat, "slow")
        enqueue_action("raid_alert", {"chat": chat})

def enqueue_action(action: str, payload: dict):
    e = {"action": action, **payload}
    if not redis_client:
        log.warning(f"would enqueue action {e} (redis not configured)")
        return
    try:
        redis_client.rpush(OUT_QUEUE, json.dumps(e))
    except Exception as ex:
        log.error(f"failed to enqueue action {e}: {ex}")


def main():
    log.info("worker started, waiting for events")
    while True:
        try:
            if not redis_client:
                log.error("redis not available, sleeping...")
                time.sleep(5)
                continue
            _, raw = redis_client.blpop(IN_QUEUE, timeout=5)
            if not raw:
                continue
            event = json.loads(raw)
            et = event.get("type")
            if et == "message":
                process_message(event)
            elif et == "join":
                process_join(event)
                # Auto-cycle containment if needed
                raid.auto_cycle_containment(event.get("chat"))
            else:
                log.debug(f"unhandled event type {et}")
        except Exception as e:
            log.error(f"error processing event: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
