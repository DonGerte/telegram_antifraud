"""Strike management system - warning / mute / ban."""
import logging
from services.memory import add_strike, get_strikes, ban_user, get_user_profile

logger = logging.getLogger("strike_manager")


class StrikeAction:
    """Result of a strike action."""
    
    NONE = "none"
    WARNING = "warning"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"


def process_strike(user_id: int, reason: str = "") -> StrikeAction:
    """
    Process a strike for a user.
    
    1 strike -> warning
    2 strikes -> mute/restrict
    3 strikes -> ban
    
    Returns action type.
    """
    strikes = add_strike(user_id)
    profile = get_user_profile(user_id)
    
    logger.info(f"User {user_id} received strike {strikes}. Reason: {reason}")
    
    if strikes == 1:
        return StrikeAction.WARNING
    elif strikes == 2:
        return StrikeAction.MUTE
    elif strikes >= 3:
        ban_user(user_id, reason=f"Reached 3 strikes. Last reason: {reason}")
        return StrikeAction.BAN
    
    return StrikeAction.NONE


def format_strike_reason(reason: str, strikes: int) -> str:
    """Format a message explaining the strike."""
    strike_msgs = {
        1: f"⚠️ Warning: {reason}. (1/3 strikes)",
        2: f"⛔ Final warning (2/3 strikes): {reason}. Next violation = ban.",
        3: f"🔴 BANNED: {reason}. (3/3 strikes)"
    }
    return strike_msgs.get(strikes, f"Strike received: {reason}")
