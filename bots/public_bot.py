from pyrogram import Client, filters
import logging
import os
import json
import time
import hashlib
from collections import defaultdict
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import redis
except ImportError:
    redis = None

from engine import honeypot
from engine import scoring as scoring_engine
from engine import text_normalization
from engine.heuristics import compute_signal
from engine.risk_assessment import assess_user_risk, should_action_on_message
from services import memory, strike_manager, ban_manager, user_history, db
import config
from pathlib import Path

# Ensure sessions directory is consistent across bot execution contexts
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SESSION_DIR = ROOT_DIR / "sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# Lock file to prevent multiple instances
LOCK_FILE = ROOT_DIR / ".public_bot.lock"


def _acquire_lock():
    """Acquire exclusive lock to prevent multiple instances."""
    import platform
    
    if platform.system() == "Windows":
        # Windows doesn't support fcntl, use simple file check
        if LOCK_FILE.exists():
            try:
                age = time.time() - LOCK_FILE.stat().st_mtime
                if age < 300:  # 5 minutes
                    raise RuntimeError("Another instance of public_bot is already running")
            except OSError:
                pass
        LOCK_FILE.write_text(str(os.getpid()))
    else:
        # Unix: use fcntl for proper locking
        import fcntl
        lock_fd = open(LOCK_FILE, 'w')
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_fd.write(str(os.getpid()))
            lock_fd.flush()
            return lock_fd
        except IOError:
            raise RuntimeError("Another instance of public_bot is already running")
    
    return None


def _release_lock(lock_fd=None):
    """Release lock file."""
    try:
        if lock_fd:
            import fcntl
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass

# Redis queue names
IN_QUEUE = "data_bus"
OUT_QUEUE = "action_bus"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("public_bot")

# connect to Redis broker
redis_client = None
if redis and config.REDIS_URL:
    try:
        redis_client = redis.from_url(config.REDIS_URL)
        logger.info("Redis conectado")
    except Exception as e:
        logger.warning(f"Redis no disponible: {e}")
        redis_client = None

# Ensure DB schema is applied
try:
    db.init_db()
    logger.info("Database initialization/migration checked")
except Exception as e:
    logger.warning(f"Database init failed: {e}")

# Validate configuration before starting
if not config.PUBLIC_BOT_TOKEN:
    logger.error("PUBLIC_BOT_TOKEN is not configured. Set it in .env")
    raise RuntimeError("PUBLIC_BOT_TOKEN is required")

bot = Client(
    "public_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.PUBLIC_BOT_TOKEN,
    in_memory=True,
    workdir=str(SESSION_DIR)
)

def enqueue_action(action, payload):
    event = {"action": action, **payload}
    logger.info(f"enqueue {event}")
    if not redis_client:
        logger.warning("redis not configured, cannot enqueue")
        return
    try:
        redis_client.rpush(OUT_QUEUE, json.dumps(event))
    except Exception as e:
        logger.error(f"failed to enqueue action: {e}")


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@bot.on_message(filters.command("start"))
async def start_command(client, message):
    """Handle /start command in chats"""
    logger.info(f"/start received in chat {message.chat.id} by user {message.from_user.id if message.from_user else 'unknown'}")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="public_status")],
        [InlineKeyboardButton("🩺 Health", callback_data="public_health")],
        [InlineKeyboardButton("❓ Help", callback_data="public_help")]
    ])

    await message.reply_text(
        "🤖 **Telegram Antifraud Bot**\n\n"
        "Bot de monitoreo para grupos. Usa los botones para ver estado y salud.\n",
        reply_markup=keyboard
    )


@bot.on_message(filters.command("help"))
async def help_command(client, message):
    """Handle /help command"""
    logger.info(f"/help received in chat {message.chat.id} by user {message.from_user.id if message.from_user else 'unknown'}")
    await start_command(client, message)


@bot.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data
    if data == "public_status":
        await callback_query.message.reply_text("Ejecutando /status...")
        await status_command(client, callback_query.message)
    elif data == "public_health":
        await callback_query.message.reply_text("Ejecutando /health...")
        await health_command(client, callback_query.message)
    elif data == "public_help":
        await callback_query.message.reply_text("Ejecutando /help...")
        await help_command(client, callback_query.message)
    await callback_query.answer()


@bot.on_message(filters.command("status"))
async def status_command(client, message):
    """Handle /status command"""
    try:
        store = memory.load_store()
        users = store.get("users", {})
        total_users = len(users)
        banned_users = sum(1 for u in users.values() if u.get("banned", False))

        status_text = (
            "📊 **Bot Status**\n\n"
            f"👥 Usuarios registrados: {total_users}\n"
            f"🚫 Usuarios baneados: {banned_users}\n"
            f"🔄 Estado: {'Activo' if redis_client else 'Sin Redis'}\n"
            f"⚙️ Modo: {'Producción' if config.PUBLIC_BOT_TOKEN else 'Desarrollo'}\n"
        )

        await message.reply_text(status_text)
    except Exception as e:
        await message.reply_text(f"❌ Error obteniendo status: {e}")


@bot.on_message(filters.command("ping"))
async def ping_command(client, message):
    logger.info(f"/ping received from {message.chat.id}")
    await message.reply_text("🏓 pong")


@bot.on_message(filters.command("health"))
async def health_check(client, message):
    try:
        store = memory.load_store()
        users = store.get("users", {})

        health_text = (
            "🩺 **Health Check**\n\n"
            f"Redis: {'Conectado' if redis_client else 'No disponible'}\n"
            f"Usuarios almacenados: {len(users)}\n"
            f"Admin config: {config.ADMIN_IDS}\n"
            f"Modo: {'Producción' if config.PUBLIC_BOT_TOKEN else 'Desarrollo'}\n"
        )
        await message.reply_text(health_text)
    except Exception as e:
        await message.reply_text(f"❌ Health check failed: {e}")


@bot.on_message(filters.group)
async def ingest(client, message):
    """Process incoming messages in group chats."""
    uid = message.from_user.id if message.from_user else None
    if not uid:
        return

    text = message.text or message.caption or ""
    
    # Deduplication: Skip if we've seen this exact message in the last 2 seconds
    msg_hash = hashlib.md5(f"{uid}:{message.chat.id}:{text}:{message.date}".encode()).hexdigest()
    cache_key = f"msg_dedup:{msg_hash}"
    if redis_client:
        try:
            if redis_client.get(cache_key):
                logger.debug(f"Duplicate message detected: {msg_hash}, skipping")
                return
            redis_client.setex(cache_key, 2, "1")
        except Exception as e:
            logger.debug(f"Dedup check failed: {e}")
    
    text_normalized = text_normalization.normalize_text(text)
    signals = text_normalization.extract_signals(text)

    # Record message in memory cache
    memory.record_message(uid, text, message.chat.id)

    # Get signal from heuristics
    sig_type, sig_value = compute_signal(message)

    # Store event in persistent history
    user_history.record_event(
        user_id=uid,
        chat_id=message.chat.id,
        signal=sig_type,
        value=sig_value,
        ts=message.date,
    )

    # Add scoring signal to in-memory score flow
    scoring_engine.add_signal(
        uid,
        signal_type=sig_type,
        value=sig_value,
        chat=message.chat.id,
        ts=message.date.timestamp(),
    )

    # Assess overall risk
    risk_result = assess_user_risk(uid, message.chat.id, text)
    
    logger.info(
        f"[{message.chat.id}] User {uid} | Signal: {sig_type} ({sig_value}) | "
        f"Risk: {risk_result['level']} ({risk_result['score']:.0f})"
    )
    
    # Determine if action needed
    should_act, action = should_action_on_message(risk_result)
    
    if should_act:
        if action == "STRIKE":
            strike_result = strike_manager.process_strike(uid, reason=sig_type)
            logger.warning(f"User {uid}: Strike processed - {strike_result}")
        elif action == "DELETE":
            logger.error(f"User {uid} banned - deleting message")
    
    # Send to queue for worker processing (existing system)
    event = {
        "type": "message",
        "uid": uid,
        "chat": message.chat.id,
        "ts": message.date.timestamp(),
        "signal_type": sig_type,
        "value": sig_value,
        "raw": text,
        "risk_level": risk_result["level"],
        "risk_score": risk_result["score"]
    }
    
    if redis_client:
        try:
            redis_client.rpush(IN_QUEUE, json.dumps(event))
        except Exception as e:
            logger.error(f"failed to send event to queue: {e}")


@bot.on_chat_member_updated()
async def member_change(client, event):
    """Track joins and leaves for raid detection."""
    if event.new_chat_member and event.new_chat_member.status == "member":
        uid = event.new_chat_member.user.id
        chat_id = event.chat.id
        ts = event.date.timestamp() if hasattr(event, "date") else time.time()

        # Deduplication: Skip if we've seen this join in the last 3 seconds
        join_hash = hashlib.md5(f"{uid}:{chat_id}:join:{event.date}".encode()).hexdigest()
        cache_key = f"join_dedup:{join_hash}"
        if redis_client:
            try:
                if redis_client.get(cache_key):
                    logger.debug(f"Duplicate join detected: {join_hash}, skipping")
                    return
                redis_client.setex(cache_key, 3, "1")
            except Exception as e:
                logger.debug(f"Join dedup check failed: {e}")

        # Check if user is banned
        if ban_manager.is_user_banned(uid):
            logger.warning(f"Banned user {uid} joined {chat_id} - should restrict")

        join_event = {"type": "join", "chat": chat_id, "uid": uid, "ts": ts}
        try:
            if redis_client:
                redis_client.rpush(IN_QUEUE, json.dumps(join_event))
        except Exception as e:
            logger.error(f"failed to enqueue join: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Antifraud Bot")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode (no Telegram connection)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.test_mode:
        # Test mode: validate imports and basic functionality
        logger.info("Running in test mode...")
        
        # Test imports
        try:
            from engine import honeypot, scoring
            from services import memory, strike_manager, ban_manager
            from engine.risk_assessment import assess_user_risk
            logger.info("✓ All imports successful")
        except ImportError as e:
            logger.error(f"✗ Import error: {e}")
            sys.exit(1)
        
        # Test memory service
        try:
            memory.record_message(12345, "test message", -100123)
            profile = memory.get_user_profile(12345)
            assert profile is not None
            assert profile["message_count"] == 1
            logger.info("✓ Memory service working")
        except Exception as e:
            logger.error(f"✗ Memory service error: {e}")
            sys.exit(1)
        
        # Test strike system
        try:
            strike_manager.process_strike(12345, "test")
            strikes = memory.get_strikes(12345)
            assert strikes == 1
            logger.info("✓ Strike system working")
        except Exception as e:
            logger.error(f"✗ Strike system error: {e}")
            sys.exit(1)
        
        # Test risk assessment
        try:
            risk = assess_user_risk(12345, -100123, "test")
            assert "level" in risk
            assert "score" in risk
            logger.info("✓ Risk assessment working")
        except Exception as e:
            logger.error(f"✗ Risk assessment error: {e}")
            sys.exit(1)
        
        logger.info("🎉 All tests passed! Bot is ready.")
        sys.exit(0)
    
    # Acquire exclusive lock to prevent multiple instances
    lock_fd = None
    try:
        lock_fd = _acquire_lock()
        logger.info("✓ Acquired exclusive lock for public_bot")
    except RuntimeError as e:
        logger.error(f"✗ {e}")
        sys.exit(1)
    
    # Normal mode: start the bot
    try:
        logger.info("Starting public bot...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        _release_lock(lock_fd)
        logger.info("Public bot shutdown complete")
