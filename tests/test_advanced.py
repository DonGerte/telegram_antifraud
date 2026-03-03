"""Tests for advanced features: rules engine, honeypot similarity, raid containment."""
import pytest
from engine.rules import RuleEngine
from engine.honeypot import similarity, register_template, check_honeypot
from engine import raid, shadow_mod


def test_rule_engine_score_condition():
    rules_data = [
        {
            "name": "high_score",
            "condition": {"score_gt": 50},
            "action": "kick",
            "reason": "score>50"
        }
    ]
    engine = RuleEngine(rules_data)
    ctx = {"score": 60}
    actions = engine.evaluate(ctx)
    assert len(actions) == 1
    assert actions[0]["action"] == "kick"


def test_rule_engine_cluster_and_score():
    rules_data = [
        {
            "name": "cluster_high_score",
            "condition": {
                "cluster_gt": 2,
                "score_gt": 30,
                "cluster_and_score": True
            },
            "action": "kick",
            "reason": "network"
        }
    ]
    engine = RuleEngine(rules_data)
    # Both conditions met
    ctx1 = {"cluster_size": 3, "score": 40}
    actions1 = engine.evaluate(ctx1)
    assert len(actions1) == 1
    
    # Only one condition met
    ctx2 = {"cluster_size": 5, "score": 20}
    actions2 = engine.evaluate(ctx2)
    assert len(actions2) == 0


def test_honeypot_similarity():
    # Test Levenshtein distance
    assert similarity("hello", "hello", threshold=0.8)
    assert similarity("hello", "helo", threshold=0.8)  # 1 deletion
    assert not similarity("hello", "world", threshold=0.8)


def test_honeypot_with_templates():
    # Register a template
    register_template("test", "click here to buy now")
    # Similar text should be detected
    assert check_honeypot("click here to buy now")
    assert check_honeypot("click here to buy")  # similar


def test_raid_containment():
    chat = 999
    raid.recent_joins.clear()
    
    # No containment initially
    assert raid.get_containment_mode(chat) == "normal"
    
    # Enter slow mode
    raid.enter_containment(chat, "slow")
    assert raid.is_in_slow(chat)
    
    # Switch to bunker
    raid.enter_containment(chat, "bunker")
    assert raid.is_in_bunker(chat)
    
    # Exit
    raid.exit_containment(chat)
    assert raid.get_containment_mode(chat) == "normal"


def test_shadow_mod_throttle():
    uid = 123
    shadow_mod.throttled_users.clear()
    
    shadow_mod.throttle_user(uid, msgs_per_minute=1)
    assert shadow_mod.is_throttled(uid)
    assert shadow_mod.should_suppress_message(uid)


def test_shadow_mod_mute():
    uid = 456
    shadow_mod.shadow_muted.clear()
    
    shadow_mod.shadow_mute(uid, duration=1)
    assert shadow_mod.is_shadow_muted(uid)
    
    # After "expiry" (simulated)
    import time
    time.sleep(1.1)
    assert not shadow_mod.is_shadow_muted(uid)
