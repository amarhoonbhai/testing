"""
Telegram channel logger — sends all activity logs to the logs channel.

All user actions, broadcast events, and system events are sent to
the configured LOGS_CHANNEL_ID for centralized monitoring.
"""

import logging
from datetime import datetime

import pytz

from app.config import LOGS_CHANNEL_ID, TIMEZONE, BOT_USERNAME

logger = logging.getLogger(__name__)

_bot = None
_tz = pytz.timezone(TIMEZONE)


def set_bot(bot):
    """Set the bot instance for sending logs. Called during startup."""
    global _bot
    _bot = bot


async def log_to_channel(text: str, silent: bool = True):
    """Send a log message to the logs channel."""
    if not _bot or not LOGS_CHANNEL_ID:
        return
    try:
        await _bot.send_message(
            chat_id=LOGS_CHANNEL_ID,
            text=text,
            parse_mode="HTML",
            disable_notification=silent,
        )
    except Exception as e:
        logger.warning(f"Failed to send log to channel: {type(e).__name__}")


def _now_str() -> str:
    return datetime.now(_tz).strftime("%H:%M:%S")


# ═══════════════════════════════════════════════════════════════════════════════
#  USER EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_user_start(user_id: int, username: str, first_name: str):
    await log_to_channel(
        f"🟢 <b>USER START</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Name: {first_name}\n"
        f"├ Username: @{username}\n"
        f"└ Time: {_now_str()}"
    )


async def log_account_added(user_id: int, phone_masked: str):
    await log_to_channel(
        f"📱 <b>ACCOUNT ADDED</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Account: <code>{phone_masked}</code>\n"
        f"└ Time: {_now_str()}"
    )


async def log_account_deleted(user_id: int, phone_masked: str):
    await log_to_channel(
        f"🗑️ <b>ACCOUNT DELETED</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Account: <code>{phone_masked}</code>\n"
        f"└ Time: {_now_str()}"
    )


async def log_ads_started(user_id: int, accounts: int, groups: int, interval: int):
    await log_to_channel(
        f"▶️ <b>ADS STARTED</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Accounts: {accounts}\n"
        f"├ Groups: {groups}\n"
        f"├ Interval: {interval}s\n"
        f"└ Time: {_now_str()}"
    )


async def log_ads_stopped(user_id: int):
    await log_to_channel(
        f"⏸️ <b>ADS STOPPED</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"└ Time: {_now_str()}"
    )


async def log_broadcast_cycle(user_id: int, sent: int, failed: int):
    await log_to_channel(
        f"📊 <b>CYCLE REPORT</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Sent: {sent}\n"
        f"├ Failed: {failed}\n"
        f"└ Time: {_now_str()}"
    )


async def log_night_mode(user_id: int, action: str):
    emoji = "🌙" if action == "start" else "☀️"
    await log_to_channel(
        f"{emoji} <b>NIGHT MODE {'ACTIVATED' if action == 'start' else 'ENDED'}</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"└ Time: {_now_str()}"
    )


async def log_error(user_id: int, error_type: str, details: str = ""):
    await log_to_channel(
        f"❌ <b>ERROR</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Type: {error_type}\n"
        f"├ Details: {details}\n"
        f"└ Time: {_now_str()}"
    )


async def log_groups_added(user_id: int, added: int, failed: int):
    await log_to_channel(
        f"📂 <b>GROUPS ADDED</b>\n"
        f"├ User: <code>{user_id}</code>\n"
        f"├ Added: {added}\n"
        f"├ Invalid: {failed}\n"
        f"└ Time: {_now_str()}"
    )
