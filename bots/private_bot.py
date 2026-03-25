from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import time
import json
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import redis
except ImportError:
    redis = None

import config
from engine import raid, shadow_mod
from engine.logger import get_logger, log_event
from services import memory, strike_manager, ban_manager
from engine.risk_assessment import assess_user_risk, RiskLevel

log = get_logger("private_bot")

_redis = None
if redis and config.REDIS_URL:
    try:
        _redis = redis.from_url(config.REDIS_URL)
        log.info("Redis conectado para bot privado")
    except Exception as e:
        log.warning(f"Redis no disponible para bot privado: {e}")
        _redis = None

priv_bot = Client("private_bot",
               api_id=config.API_ID,
               api_hash=config.API_HASH,
               bot_token=config.PRIVATE_BOT_TOKEN)

ACTION_QUEUE = "action_bus"



def kick_user(chat_id: int, user_id: int, reason=None):
    """Kick a user from a chat."""
    try:
        priv_bot.kick_chat_member(chat_id, user_id)
        log_event(log, "user_kicked", chat_id=chat_id, user_id=user_id, reason=reason)
        return True
    except Exception as e:
        log.error(f"kick failed {user_id}@{chat_id}: {e}")
        return False


def mute_user(chat_id: int, user_id: int, duration: int = 3600):
    """Mute a user for duration seconds."""
    try:
        shadow_mod.shadow_mute(user_id, duration)
        log_event(log, "user_muted", chat_id=chat_id, user_id=user_id, duration=duration)
        return True
    except Exception as e:
        log.error(f"mute failed {user_id}@{chat_id}: {e}")
        return False


def restrict_user(chat_id: int, user_id: int, reason=None):
    """Restrict a user's permissions."""
    try:
        shadow_mod.throttle_user(user_id, msgs_per_minute=1)
        log_event(log, "user_restricted", chat_id=chat_id, user_id=user_id, reason=reason)
        return True
    except Exception as e:
        log.error(f"restrict failed {user_id}@{chat_id}: {e}")
        return False


def enable_slow_mode(chat_id: int):
    """Enable slow mode in a chat."""
    try:
        raid.enter_containment(chat_id, "slow")
        log_event(log, "slow_mode_enabled", chat_id=chat_id)
        return True
    except Exception as e:
        log.error(f"slow mode failed {chat_id}: {e}")
        return False


def enable_bunker_mode(chat_id: int):
    """Enable bunker (lockdown) mode in a chat."""
    try:
        raid.enter_containment(chat_id, "bunker")
        log_event(log, "bunker_mode_enabled", chat_id=chat_id)
        return True
    except Exception as e:
        log.error(f"bunker mode failed {chat_id}: {e}")
        return False


def disable_containment(chat_id: int):
    """Disable containment mode in a chat."""
    try:
        raid.exit_containment(chat_id)
        log_event(log, "containment_disabled", chat_id=chat_id)
        return True
    except Exception as e:
        log.error(f"disable containment failed {chat_id}: {e}")
        return False


def process_action(raw):
    """Process an action from the action_bus queue."""
    try:
        action = json.loads(raw)
    except Exception as e:
        log.error(f"malformed action: {raw}, error: {e}")
        return

    act = action.get("action")

    if act == "kick":
        kick_user(action.get("chat"), action.get("uid"), action.get("reason"))
    elif act == "mute":
        mute_user(action.get("chat"), action.get("uid"), action.get("duration", 3600))
    elif act == "restrict":
        restrict_user(action.get("chat"), action.get("uid"), action.get("reason"))
    elif act == "raid_alert":
        enable_slow_mode(action.get("chat"))
    elif act == "raid_bunker":
        enable_bunker_mode(action.get("chat"))
    elif act == "containment_off":
        disable_containment(action.get("chat"))
    else:
        log.info(f"unhandled action {act}")


# Admin command handlers
@priv_bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """Handle /start command"""
    await message.reply_text(
        "🤖 **Telegram Antifraud Admin Bot**\n\n"
        "Available commands:\n"
        "/stats - Show system statistics\n"
        "/user <id> - Get user information\n"
        "/ban <id> [reason] - Ban user\n"
        "/unban <id> - Unban user\n"
        "/strike <id> [reason] - Add strike to user\n"
        "/forgive <id> - Remove strike from user\n"
        "/risk <id> - Assess user risk\n"
        "/containment <chat_id> <mode> - Set containment mode\n"
        "/whitelist <id> - Add user to whitelist\n"
        "/blacklist <id> - Add user to blacklist\n"
        "/test - Run system tests"
    )


@priv_bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message: Message):
    """Show system statistics"""
    try:
        store = memory.load_store()
        users = store.get("users", {})
        metadata = store.get("metadata", {})

        total_users = len(users)
        banned_users = sum(1 for u in users.values() if u.get("banned", False))
        strikes_given = sum(u.get("strikes", 0) for u in users.values())
        total_messages = sum(u.get("message_count", 0) for u in users.values())

        stats_text = (
            "📊 **System Statistics**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"🚫 Banned Users: {banned_users}\n"
            f"⚡ Total Strikes: {strikes_given}\n"
            f"💬 Total Messages: {total_messages}\n"
            f"🕒 Last Updated: {metadata.get('last_updated', 'Never')}\n"
        )

        await message.reply_text(stats_text)
    except Exception as e:
        await message.reply_text(f"❌ Error getting stats: {e}")


@priv_bot.on_message(filters.command("user") & filters.private)
async def user_command(client, message: Message):
    """Get user information"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /user <user_id>")
            return

        user_id = int(args[0])
        profile = memory.get_user_profile(user_id)

        if not profile:
            await message.reply_text("❌ User not found")
            return

        risk = assess_user_risk(user_id, 0, "")  # Assess without chat context

        user_text = (
            f"👤 **User {user_id}**\n\n"
            f"📝 Messages: {profile.get('message_count', 0)}\n"
            f"⚡ Strikes: {profile.get('strikes', 0)}\n"
            f"🚫 Banned: {'Yes' if profile.get('banned', False) else 'No'}\n"
            f"🎯 Risk Level: {risk['level'].value}\n"
            f"📊 Risk Score: {risk['score']:.2f}\n"
            f"🏷️ Tags: {', '.join(profile.get('tags', []))}\n"
            f"🕒 First Seen: {profile.get('first_seen', 'Unknown')}\n"
            f"🕒 Last Seen: {profile.get('last_seen', 'Unknown')}\n"
        )

        await message.reply_text(user_text)
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("ban") & filters.private)
async def ban_command(client, message: Message):
    """Ban a user"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /ban <user_id> [reason]")
            return

        user_id = int(args[0])
        reason = " ".join(args[1:]) if len(args) > 1 else "Manual ban"

        success = ban_manager.ban_user(user_id, reason)
        if success:
            await message.reply_text(f"✅ User {user_id} banned: {reason}")
        else:
            await message.reply_text(f"❌ Failed to ban user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("unban") & filters.private)
async def unban_command(client, message: Message):
    """Unban a user"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /unban <user_id>")
            return

        user_id = int(args[0])
        success = ban_manager.unban_user(user_id)
        if success:
            await message.reply_text(f"✅ User {user_id} unbanned")
        else:
            await message.reply_text(f"❌ Failed to unban user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("strike") & filters.private)
async def strike_command(client, message: Message):
    """Add strike to user"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /strike <user_id> [reason]")
            return

        user_id = int(args[0])
        reason = " ".join(args[1:]) if len(args) > 1 else "Manual strike"

        action = strike_manager.process_strike(user_id, reason)
        if action == strike_manager.StrikeAction.STRIKE_ADDED:
            strikes = memory.get_strikes(user_id)
            await message.reply_text(f"⚡ Strike added to user {user_id}. Total strikes: {strikes}")
        elif action == strike_manager.StrikeAction.USER_BANNED:
            await message.reply_text(f"🚫 User {user_id} banned after 3 strikes")
        else:
            await message.reply_text(f"❌ Failed to add strike to user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("forgive") & filters.private)
async def forgive_command(client, message: Message):
    """Remove strike from user"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /forgive <user_id>")
            return

        user_id = int(args[0])
        success = strike_manager.remove_strike(user_id)
        if success:
            strikes = memory.get_strikes(user_id)
            await message.reply_text(f"✅ Strike removed from user {user_id}. Remaining strikes: {strikes}")
        else:
            await message.reply_text(f"❌ Failed to remove strike from user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("risk") & filters.private)
async def risk_command(client, message: Message):
    """Assess user risk"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /risk <user_id>")
            return

        user_id = int(args[0])
        risk = assess_user_risk(user_id, 0, "")

        risk_text = (
            f"🎯 **Risk Assessment for {user_id}**\n\n"
            f"📊 Risk Level: {risk['level'].value}\n"
            f"🔢 Risk Score: {risk['score']:.2f}\n"
            f"📝 Factors: {', '.join(risk.get('factors', []))}\n"
        )

        await message.reply_text(risk_text)
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("containment") & filters.private)
async def containment_command(client, message: Message):
    """Set containment mode for a chat"""
    try:
        args = message.text.split()[1:]
        if len(args) < 2:
            await message.reply_text("Usage: /containment <chat_id> <mode>\nModes: slow, bunker, off")
            return

        chat_id = int(args[0])
        mode = args[1].lower()

        if mode == "off":
            success = disable_containment(chat_id)
            msg = f"✅ Containment disabled for chat {chat_id}"
        elif mode == "slow":
            success = enable_slow_mode(chat_id)
            msg = f"✅ Slow mode enabled for chat {chat_id}"
        elif mode == "bunker":
            success = enable_bunker_mode(chat_id)
            msg = f"✅ Bunker mode enabled for chat {chat_id}"
        else:
            await message.reply_text("❌ Invalid mode. Use: slow, bunker, off")
            return

        if not success:
            msg = f"❌ Failed to set containment mode for chat {chat_id}"

        await message.reply_text(msg)
    except ValueError:
        await message.reply_text("❌ Invalid chat ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("whitelist") & filters.private)
async def whitelist_command(client, message: Message):
    """Add user to whitelist"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /whitelist <user_id>")
            return

        user_id = int(args[0])
        success = memory.add_to_whitelist(user_id)
        if success:
            await message.reply_text(f"✅ User {user_id} added to whitelist")
        else:
            await message.reply_text(f"❌ Failed to whitelist user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("blacklist") & filters.private)
async def blacklist_command(client, message: Message):
    """Add user to blacklist"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /blacklist <user_id>")
            return

        user_id = int(args[0])
        success = memory.add_to_blacklist(user_id)
        if success:
            await message.reply_text(f"🚫 User {user_id} added to blacklist")
        else:
            await message.reply_text(f"❌ Failed to blacklist user {user_id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("test") & filters.private)
async def test_command(client, message: Message):
    """Run system tests"""
    await message.reply_text("🧪 Running system tests...")

    try:
        # Test memory service
        test_user = 999999
        memory.record_message(test_user, "test", -100999)
        profile = memory.get_user_profile(test_user)
        assert profile is not None

        # Test strike system
        strike_manager.process_strike(test_user, "test")
        strikes = memory.get_strikes(test_user)
        assert strikes == 1

        # Test risk assessment
        risk = assess_user_risk(test_user, -100999, "test")
        assert "level" in risk

        # Clean up test data
        store = memory.load_store()
        if str(test_user) in store.get("users", {}):
            del store["users"][str(test_user)]
            memory.save_store(store)

        await message.reply_text("✅ All tests passed!")
    except Exception as e:
        await message.reply_text(f"❌ Test failed: {e}")


def main():
    if not _redis:
        log.error("redis not configured, cannot consume actions")
        return
    log.info("private bot listening for actions")
    while True:
        try:
            _, raw = _redis.blpop(ACTION_QUEUE, timeout=5)
            if raw:
                process_action(raw)
        except Exception as e:
            log.error(f"error processing action: {e}")
            time.sleep(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Antifraud Admin Bot")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode (no Telegram connection)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.test_mode:
        # Test mode: validate imports and basic functionality
        logger = logging.getLogger("private_bot_test")
        logger.info("Running private bot in test mode...")

        # Test imports
        try:
            from services import memory, strike_manager, ban_manager
            from engine.risk_assessment import assess_user_risk
            logger.info("✓ All imports successful")
        except ImportError as e:
            logger.error(f"✗ Import error: {e}")
            sys.exit(1)

        # Test admin functions
        try:
            # Test memory operations
            test_user = 999998
            memory.record_message(test_user, "test", -100999)
            profile = memory.get_user_profile(test_user)
            assert profile is not None

            # Test strike operations
            strike_manager.process_strike(test_user, "test")
            strikes = memory.get_strikes(test_user)
            assert strikes == 1

            # Test ban operations
            ban_manager.ban_user(test_user, "test ban")
            profile = memory.get_user_profile(test_user)
            assert profile.get("banned", False)

            # Clean up
            store = memory.load_store()
            if str(test_user) in store.get("users", {}):
                del store["users"][str(test_user)]
                memory.save_store(store)

            logger.info("✓ Admin functions working")
        except Exception as e:
            logger.error(f"✗ Admin function error: {e}")
            sys.exit(1)

        logger.info("🎉 All private bot tests passed!")
        sys.exit(0)

    # Start listening on a background thread while bot runs
    import threading
    action_thread = threading.Thread(target=main, daemon=True)
    action_thread.start()

    try:
        priv_bot.start()
    finally:
        priv_bot.stop()
