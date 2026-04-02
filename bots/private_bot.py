from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import time
import json
import sys
import os
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import redis
except ImportError:
    redis = None

import config
from engine import raid, shadow_mod
from engine.logger import get_logger, log_event
from services import memory, strike_manager, ban_manager, db
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

# Ensure DB schema is applied
try:
    db.init_db()
    log.info("Database initialization/migration checked")
except Exception as e:
    log.warning(f"Database init failed: {e}")

# Validate configuration for private bot
if not config.PRIVATE_BOT_TOKEN:
    log.error("PRIVATE_BOT_TOKEN is not configured. Set it in .env")
    raise RuntimeError("PRIVATE_BOT_TOKEN is required")

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SESSION_DIR = ROOT_DIR / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SESSION_NAME = "private_bot"

priv_bot = Client(
    SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.PRIVATE_BOT_TOKEN,
    in_memory=True,
    workdir=str(SESSION_DIR)
)

ACTION_QUEUE = "action_bus"


def _cleanup_stale_session():
    """Remove stale session lock files for Pyrogram if present."""
    for suffix in ['.session', '.session-journal', '.session-wal', '.session-shm']:
        conn_path = SESSION_DIR / f"{SESSION_NAME}{suffix}"
        if conn_path.exists():
            try:
                conn_path.unlink()
                log.info(f"Stale session file removed: {conn_path}")
            except Exception as e:
                log.warning(f"No se pudo eliminar session stale {conn_path}: {e}")


def _safe_run_client(client: Client, max_retries=3, sleep_s=2):
    """Run client with retries on database lock (Pyrogram session file)."""
    _cleanup_stale_session()
    for attempt in range(1, max_retries + 1):
        try:
            client.run()
            return
        except Exception as e:
            msg = str(e).lower()
            if client and getattr(client, 'is_connected', False):
                try:
                    client.stop()
                except Exception:
                    pass

            if ("database is locked" in msg or "unable to open database file" in msg) and attempt < max_retries:
                log.warning(f"Database lock/error en session (intento {attempt}/{max_retries}). Reintentando en {sleep_s} segundos...")
                time.sleep(sleep_s)
                sleep_s *= 2
                continue
            log.error(f"Failed to run private bot: {e}")
            raise



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
def _is_admin(user_id: int) -> bool:
    admin = user_id in config.ADMIN_IDS
    log.debug(f"admin check: user_id={user_id}, admin={admin}, configured={config.ADMIN_IDS}")
    return admin


def admin_required(func):
    async def wrapper(client, message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else 0
        if not _is_admin(user_id):
            await message.reply_text("❌ Access denied: admin only")
            return
        return await func(client, message, *args, **kwargs)

    return wrapper


@priv_bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    """Handle /start command"""
    user_id = message.from_user.id if message.from_user else 0
    log.info(f"/start from {user_id}, config admins={config.ADMIN_IDS}")
    if not _is_admin(user_id):
        await message.reply_text(
            f"❌ Acceso denegado: administrador sólo.\n"
            f"Tu ID: {user_id}\n"
            f"Admin IDs configurados: {config.ADMIN_IDS}\n"
            "Si tú eres admin, actualiza ADMIN_IDS en .env y reinicia el bot."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Who am I", callback_data="private_whoami")],
        [InlineKeyboardButton("🔨 Ban user", callback_data="private_ban")],
        [InlineKeyboardButton("✅ Unban user", callback_data="private_unban")],
        [InlineKeyboardButton("📋 List banned", callback_data="private_list_bans")],
        [InlineKeyboardButton("📊 Stats", callback_data="private_stats")]
    ])

    await message.reply_text(
        "🤖 **Telegram Antifraud Admin Bot**\n\n"
        "Usa los botones para gestionar usuarios.\n"
        "Para ejecutar con texto: /ban <id|@username> <reason>, /unban <id|@username>\n",
        reply_markup=keyboard
    )


@priv_bot.on_callback_query()
async def private_callback_query(client, callback_query):
    user_id = callback_query.from_user.id if callback_query.from_user else 0
    is_admin = _is_admin(user_id)
    log.info(f"callback_query from {user_id}: is_admin={is_admin}, ADMIN_IDS={config.ADMIN_IDS}")

    if not is_admin:
        await callback_query.answer(
            f"❌ Acceso denegado (solo admin). ID actual: {user_id}. ADMIN_IDS: {config.ADMIN_IDS}",
            show_alert=True
        )
        return

    data = callback_query.data
    if data == "private_whoami":
        await callback_query.message.reply_text(f"Tu ID: {user_id}")
    elif data == "private_ban":
        await callback_query.message.reply_text("Envia /ban <id|@username> <motivo>")
    elif data == "private_unban":
        await callback_query.message.reply_text("Envia /unban <id|@username>")
    elif data == "private_list_bans":
        await list_bans_command(client, callback_query.message)
    elif data == "private_stats":
        await stats_command(client, callback_query.message)
    else:
        await callback_query.answer("❌ Acción desconocida")
        return

    await callback_query.answer("✅ Acción ejecutada")


@priv_bot.on_message(filters.command("stats") & filters.private)
@admin_required
async def stats_command(client, message: Message):
    """Show system statistics"""
    try:
        from services.db import SessionLocal, UserProfile, Ban, Message
        with SessionLocal() as db:
            total_users = db.query(UserProfile).count()
            banned_users = db.query(UserProfile).filter(UserProfile.banned == 1).count()
            total_strikes = db.query(UserProfile).with_entities(UserProfile.strikes).all()
            strikes_given = sum(s[0] for s in total_strikes)
            total_messages = db.query(Message).count()

        stats_text = (
            "📊 **System Statistics**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"🚫 Banned Users: {banned_users}\n"
            f"⚡ Total Strikes: {strikes_given}\n"
            f"💬 Total Messages: {total_messages}\n"
            f"🕒 Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        await message.reply_text(stats_text)
    except Exception as e:
        await message.reply_text(f"❌ Error getting stats: {e}")


@priv_bot.on_message(filters.command("user") & filters.private)
@admin_required
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
            f"🎯 Risk Level: {risk['level']}\n"
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
@admin_required
async def ban_command(client, message: Message):
    """Ban a user"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /ban <user_id|@username> [reason]")
            return

        target = args[0]
        reason = " ".join(args[1:]) if len(args) > 1 else "Manual ban"

        user_id = None
        username = None

        if target.startswith("@"):
            username = target
            try:
                user_obj = await client.get_users(target)
                user_id = user_obj.id
            except Exception as e:
                await message.reply_text(f"❌ No se pudo resolver el usuario {target}: {e}")
                return
        else:
            try:
                user_id = int(target)
            except ValueError:
                await message.reply_text("❌ Invalid user ID or username")
                return

        admin_user = message.from_user
        admin_id = admin_user.id if admin_user else None
        admin_username = admin_user.username if admin_user else None

        ban_manager.ban_user(user_id, reason, banned_by_id=admin_id, banned_by_username=admin_username)
        await message.reply_text(
            f"🚫 Banned user: {user_id} {username or ''}\nMotivo: {reason}\n"
            f"Ban hecho por: @{admin_username or 'unknown'} ({admin_id})\n"
            f"Uso: /unban {user_id} para desbanear"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("unban") & filters.private)
@admin_required
async def unban_command(client, message: Message):
    """Unban a user"""
    try:
        args = message.text.split()[1:]
        if not args:
            await message.reply_text("Usage: /unban <user_id|@username>")
            return

        target = args[0]

        if target.startswith("@"):
            try:
                user = await client.get_users(target)
                user_id = user.id
            except Exception as e:
                await message.reply_text(f"❌ No se pudo resolver el usuario {target}: {e}")
                return
        else:
            try:
                user_id = int(target)
            except ValueError:
                await message.reply_text("❌ Invalid user ID or username")
                return

        ban_manager.unban_user(user_id)
        await message.reply_text(f"✅ User {user_id} unbanned")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("listbans") & filters.private)
@admin_required
async def list_bans_command(client, message: Message):
    """List banned users"""
    try:
        from services.db import SessionLocal, Ban
        with SessionLocal() as db:
            bans = db.query(Ban).order_by(Ban.banned_at.desc()).all()
            if not bans:
                await message.reply_text("✅ No hay usuarios baneados actualmente.")
                return

            lines = []
            for ban in bans:
                by = f"@(unknown)" if not ban.banned_by else f"ID {ban.banned_by}"
                lines.append(
                    f"ID {ban.user_id} (razón: {ban.reason or 'sin motivo'}, baneado por: {by})"
                )

            response = "📛 Usuarios baneados:\n" + "\n".join(lines)
            await message.reply_text(response)
    except Exception:
        banned = memory.get_banned_users()
        if not banned:
            await message.reply_text("✅ No hay usuarios baneados actualmente.")
            return

        lines = []
        for uid, u in banned.items():
            by = u.get("ban_by") or u.get("ban_by_username") or u.get("ban_by_id") or "unknown"
            lines.append(
                f"ID {uid} (razón: {u.get('ban_reason', 'sin motivo')}, baneado por: {by})"
            )

        response = "📛 Usuarios baneados:\n" + "\n".join(lines)
        await message.reply_text(response)


@priv_bot.on_message(filters.command("strike") & filters.private)
@admin_required
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
@admin_required
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
@admin_required
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
            f"📊 Risk Level: {risk['level']}\n"
            f"🔢 Risk Score: {risk['score']:.2f}\n"
            f"📝 Reasons: {', '.join(risk.get('reasons', [])) or 'None'}\n"
        )

        await message.reply_text(risk_text)
    except ValueError:
        await message.reply_text("❌ Invalid user ID")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")


@priv_bot.on_message(filters.command("containment") & filters.private)
@admin_required
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
@admin_required
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
@admin_required
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


@priv_bot.on_message(filters.command("ping") & filters.private)
async def ping_command(client, message: Message):
    """Ping admin bot"""
    user_id = message.from_user.id if message.from_user else 0
    log.info(f"/ping from {user_id}")
    await message.reply_text(f"🏓 pong (user: {user_id})")


@priv_bot.on_message(filters.command("whoami") & filters.private)
async def whoami_command(client, message: Message):
    user_id = message.from_user.id if message.from_user else 0
    is_admin = _is_admin(user_id)
    bot_name = None
    try:
        bot_name = priv_bot.get_me().username if priv_bot.is_connected else 'disconnected'
    except Exception:
        bot_name = 'unknown'

    await message.reply_text(
        f"Tu ID: {user_id}\n"
        f"ADMIN_IDS configurados: {config.ADMIN_IDS}\n"
        f"¿Es admin?: {is_admin}\n"
        f"Bot username: {bot_name}"
    )


@priv_bot.on_message(filters.command("health") & filters.private)
@admin_required
async def health_command(client, message: Message):
    """Health check for admin bot"""
    try:
        store = memory.load_store()
        users = store.get("users", {})
        health_text = (
            "🩺 **Admin Bot Health**\n\n"
            f"Redis: {'Conectado' if _redis else 'No disponible'}\n"
            f"Usuarios almacenados: {len(users)}\n"
            f"Admin IDs: {config.ADMIN_IDS}\n"
        )
        await message.reply_text(health_text)
    except Exception as e:
        await message.reply_text(f"❌ Health check failed: {e}")


@priv_bot.on_message(filters.command("test") & filters.private)
@admin_required
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
        log.warning("Redis no configurado: la cola de acciones estará deshabilitada, el bot seguirá respondiendo comandos.")
        while True:
            time.sleep(5)

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

    # Run bot in blocking mode so it stays online and answers commands
    log.info("Attempting to start private bot...")
    try:
        _safe_run_client(priv_bot)
        log.info("Private bot stopped")
    except Exception as e:
        import traceback
        log.error(f"Failed to run private bot: {e}", exc_info=True)
        traceback.print_exc()
        raise
