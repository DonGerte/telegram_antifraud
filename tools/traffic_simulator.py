"""Traffic simulator for testing rule engine and scoring with synthetic malicious events.

Generates realistic attack patterns:
  - Spam/honeypot messages
  - User velocity attacks (flood)
  - Coordinated raids (multiple users joining)
  - Message repetition attacks
  - Link farming
"""
import json
import time
import random
import hashlib
import sys

try:
    import redis
except ImportError:
    redis = None

import config

IN_QUEUE = "data_bus"


class TrafficSimulator:
    def __init__(self, redis_url=None):
        self.redis = None
        if redis and redis_url:
            try:
                self.redis = redis.from_url(redis_url)
            except Exception as e:
                print(f"Warning: redis not available: {e}")
        
        # Message templates for spam simulation
        self.spam_templates = [
            "Click here for free money http://bit.ly/free123",
            "Buy cheap shoes now - limited offer! http://shop.ru",
            "Get WhatsApp Messenger free here http://download.com/whatsapp",
            "Contact me: telegram @spammer01",
            "🔥 OFERTA ESPECIAL 🔥 zapatos por solo $5",
            "Envío gratis a todo el país! Ordena ahora",
            "💰 Gana dinero rápido con nuestro sistema",
            "Compra ahora, paga después - sin intereses!",
        ]
        
        self.raid_usernames = [f"raid_bot_{i:04d}" for i in range(1000, 1100)]
    
    def push_event(self, event):
        if not self.redis:
            print(f"[OFFLINE] {event['type']} - {event}")
            return
        try:
            self.redis.rpush(IN_QUEUE, json.dumps(event))
            print(f"[SENT] {event['type']} - uid={event.get('uid')} sig={event.get('signal_type')}")
        except Exception as e:
            print(f"Error pushing event: {e}")
    
    def simulate_spam_messages(self, num_users=10, msgs_per_user=5, chat_id=-100):
        """Simulate spam messages from multiple users."""
        print(f"\n=== SPAM MESSAGE ATTACK: {num_users} users x {msgs_per_user} messages ===")
        base_uid = 50000
        now = time.time()
        
        for u in range(num_users):
            uid = base_uid + u
            for m in range(msgs_per_user):
                template = random.choice(self.spam_templates)
                event = {
                    "type": "message",
                    "uid": uid,
                    "chat": chat_id,
                    "ts": now + u * 10 + m,
                    "signal_type": "honeypot",
                    "value": 10.0,
                    "raw": template,
                }
                self.push_event(event)
                time.sleep(0.01)
    
    def simulate_velocity_attack(self, num_users=5, msgs_per_second=3, duration_seconds=30, chat_id=-100):
        """Simulate high-velocity message flooding."""
        print(f"\n=== VELOCITY ATTACK: {num_users} users sending {msgs_per_second} msgs/sec for {duration_seconds}s ===")
        base_uid = 60000
        start = time.time()
        
        while time.time() - start < duration_seconds:
            for u in range(num_users):
                uid = base_uid + u
                event = {
                    "type": "message",
                    "uid": uid,
                    "chat": chat_id,
                    "ts": time.time(),
                    "signal_type": "velocity",
                    "value": 3.0,
                    "raw": f"message #{random.randint(1, 1000000)}",
                }
                self.push_event(event)
            time.sleep(1.0 / msgs_per_second)
    
    def simulate_raid(self, num_users=50, join_interval=0.5, chat_id=-100):
        """Simulate a coordinated raid (many users joining)."""
        print(f"\n=== RAID ATTACK: {num_users} users joining chat {chat_id} ===")
        base_uid = 70000
        now = time.time()
        
        for u in range(num_users):
            uid = base_uid + u
            event = {
                "type": "join",
                "chat": chat_id,
                "uid": uid,
                "ts": now + u * join_interval,
            }
            self.push_event(event)
            time.sleep(join_interval / 10)  # small delay
    
    def simulate_repetition_attack(self, num_users=5, num_repetitions=10, chat_id=-100):
        """Simulate message repetition (same spam repeated)."""
        print(f"\n=== REPETITION ATTACK: {num_users} users x {num_repetitions} identical messages ===")
        base_uid = 80000
        spam_msg = "Buy cheap now http://spam.ru"
        now = time.time()
        
        for u in range(num_users):
            uid = base_uid + u
            for r in range(num_repetitions):
                event = {
                    "type": "message",
                    "uid": uid,
                    "chat": chat_id,
                    "ts": now + u * 5 + r * 0.5,
                    "signal_type": "repetition",
                    "value": 4.0,
                    "raw": spam_msg,
                }
                self.push_event(event)
    
    def simulate_link_farming(self, num_messages=20, chat_id=-100):
        """Simulate a user posting many links."""
        print(f"\n=== LINK FARMING: single user posting {num_messages} links ===")
        uid = 90000
        now = time.time()
        
        for i in range(num_messages):
            url = f"http://link-farm-{i}.ru/promo"
            event = {
                "type": "message",
                "uid": uid,
                "chat": chat_id,
                "ts": now + i * 0.3,
                "signal_type": "link",
                "value": 5.0,
                "raw": f"Check this out: {url}",
            }
            self.push_event(event)
    
    def simulate_mixed_attack(self, chat_id=-100):
        """Simulate a complex multi-vector attack."""
        print(f"\n=== MIXED ATTACK: combination of spam, velocity, raids ===")
        # 1. Small raid first
        self.simulate_raid(num_users=15, join_interval=0.3, chat_id=chat_id)
        time.sleep(2)
        
        # 2. Spam flood from raid members
        self.simulate_spam_messages(num_users=10, msgs_per_user=3, chat_id=chat_id)
        time.sleep(2)
        
        # 3. Velocity attack
        self.simulate_velocity_attack(num_users=3, msgs_per_second=2, duration_seconds=10, chat_id=chat_id)
    
    def run_test_suite(self):
        """Run all attack simulations in sequence."""
        print("=" * 60)
        print("TRAFFIC SIMULATOR - Test Suite")
        print("=" * 60)
        
        self.simulate_spam_messages(num_users=5, msgs_per_user=4)
        time.sleep(3)
        
        self.simulate_repetition_attack(num_users=3, num_repetitions=8)
        time.sleep(3)
        
        self.simulate_raid(num_users=30, join_interval=0.3)
        time.sleep(3)
        
        self.simulate_link_farming(num_messages=15)
        time.sleep(3)
        
        self.simulate_mixed_attack()
        
        print("\n" + "=" * 60)
        print("✓ Test suite complete!")
        print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Traffic simulator for antifraud testing")
    parser.add_argument("--attack", choices=["spam", "velocity", "raid", "repetition", "links", "mixed", "all"],
                        default="all", help="Attack type to simulate")
    parser.add_argument("--redis-url", default=None, help="Redis URL (default: from config)")
    parser.add_argument("--chat", type=int, default=-100, help="Chat ID to attack")
    
    args = parser.parse_args()
    
    redis_url = args.redis_url or config.REDIS_URL
    sim = TrafficSimulator(redis_url=redis_url)
    
    try:
        if args.attack == "all":
            sim.run_test_suite()
        elif args.attack == "spam":
            sim.simulate_spam_messages(chat_id=args.chat)
        elif args.attack == "velocity":
            sim.simulate_velocity_attack(chat_id=args.chat)
        elif args.attack == "raid":
            sim.simulate_raid(chat_id=args.chat)
        elif args.attack == "repetition":
            sim.simulate_repetition_attack(chat_id=args.chat)
        elif args.attack == "links":
            sim.simulate_link_farming(chat_id=args.chat)
        elif args.attack == "mixed":
            sim.simulate_mixed_attack(chat_id=args.chat)
    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user.")
