"""Quick-start demo: how to use the antifraud system end-to-end.

This script simulates a typical workflow: ingest messages, track scores,
apply rules, and log actions.
"""
import json
import time
import sys

# Ensure we can import from engine
sys.path.insert(0, '.')

from engine import scoring, clusters, raid, honeypot
from engine.rules import RuleEngine
from engine.logger import log_event, get_logger

log = get_logger("demo")


def demo_signal_ingestion():
    """Demo 1: Ingest messages and compute scores."""
    print("\n=== DEMO 1: Signal Ingestion ===")
    
    # Simulate 3 users sending suspicious messages
    uid1, uid2, uid3 = 111, 222, 333
    chat = -100
    
    # User 111: sends link
    scoring.add_signal(uid1, "link", 5, chat)
    score1 = scoring.compute_score(uid1)
    print(f"User {uid1} sent link: score = {score1}")
    
    # User 222: sends honeypot
    scoring.add_signal(uid2, "honeypot", 10, chat)
    score2 = scoring.compute_score(uid2)
    print(f"User {uid2} sent honeypot: score = {score2}")
    
    # User 333: correlates with 222
    scoring.add_signal(uid3, "velocity", 3, chat)
    clusters.add_edge(uid2, uid3)
    score3 = scoring.compute_score(uid3)
    cluster = clusters.get_cluster(uid3)
    print(f"User {uid3} has velocity signal: score = {score3}, cluster = {cluster}")


def demo_rules_engine():
    """Demo 2: Apply rule engine to decide actions."""
    print("\n=== DEMO 2: Rule Engine Decisions ===")
    
    # Load rules
    try:
        engine = RuleEngine.load_file("rules.json")
    except Exception as e:
        print(f"Error loading rules: {e}")
        return
    
    # User contexts
    contexts = [
        {"score": 25, "cluster_size": 1, "signals": ["link"]},
        {"score": 60, "cluster_size": 1, "signals": ["text"]},
        {"score": 35, "cluster_size": 3, "signals": ["velocity"]},
        {"score": 15, "cluster_size": 1, "signals": ["honeypot"]},
    ]
    
    for i, ctx in enumerate(contexts):
        actions = engine.evaluate(ctx)
        print(f"Context {i+1}: score={ctx['score']}, cluster={ctx['cluster_size']}, signals={ctx['signals']}")
        if actions:
            for act in actions:
                print(f"  -> Action: {act['action']} (rule: {act['rule']})")
        else:
            print(f"  -> No action")


def demo_raid_detection():
    """Demo 3: Raid detection and containment."""
    print("\n=== DEMO 3: Raid Detection ===")
    
    chat = -100
    raid.recent_joins.clear()
    raid.containment_mode.clear()
    
    # Simulate 25 joins in 300 seconds
    now = time.time()
    for i in range(25):
        raid.record_join(chat, 1000 + i, ts=now - (300 - i*12))
    
    is_raid = raid.detect_raid(chat, threshold=20, window=300)
    stats = raid.get_raid_stats(chat, window=300)
    print(f"Is raid? {is_raid}")
    print(f"Stats: {stats}")
    
    # Enter containment
    raid.enter_containment(chat, "slow")
    mode = raid.get_containment_mode(chat)
    print(f"Containment mode: {mode}")


def demo_honeypot():
    """Demo 4: Honeypot detection with similarity."""
    print("\n=== DEMO 4: Honeypot Detection ===")
    
    # Register a template
    honeypot.register_template("spam", "buy cheap products online now")
    
    # Test messages
    messages = [
        "http://example.com",  # link
        "buy cheap products online now",  # exact template
        "buy cheap products today",  # similar template
        "hello world",  # normal
        "click here to get free stuff",  # might match keywords
    ]
    
    for msg in messages:
        detected = honeypot.check_honeypot(msg)
        print(f"'{msg}' -> honeypot: {detected}")


def demo_logging():
    """Demo 5: Structured JSON logging."""
    print("\n=== DEMO 5: Structured Logging ===")
    
    # Log some events
    log_event(log, "message_processed", user_id=111, chat_id=-100, score=25)
    log_event(log, "user_kicked", user_id=222, chat_id=-100, reason="honeypot")
    log_event(log, "raid_detected", chat_id=-100, join_count=25)


if __name__ == "__main__":
    print("=== Anti-Fraud System Demo ===")
    print("Showcasing each subsystem...")
    
    demo_signal_ingestion()
    demo_rules_engine()
    demo_raid_detection()
    demo_honeypot()
    demo_logging()
    
    print("\n✓ Demo complete!")
    print("\nTo run the full system:")
    print("  docker compose up --build")
    print("\nOr manually:")
    print("  python bots/public_bot.py    &")
    print("  python engine/worker.py      &")
    print("  python bots/private_bot.py   &")
