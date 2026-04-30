"""
Premium Telegram channel logger — Kurup Ads.

Sends all system activity to the centralized logs channel
using a matching professional aesthetic.
"""

import logging
from datetime import datetime

import pytz

from app.config import LOGS_CHANNEL_ID, TIMEZONE, BOT_USERNAME

logger = logging.getLogger(__name__)

_bot = None
_tz = pytz.timezone(TIMEZONE)


def set_bot(bot):
    """Set the bot instance for sending logs."""
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


def _divider() -> str:
    return "────────────────────────"


# ═══════════════════════════════════════════════════════════════════════════════
#  SYSTEM EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_user_start(user_id: int, username: str, first_name: str):
    await log_to_channel(
        f"<b>SYSTEM: USER ACCESS</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: {first_name}\n"
        f"  🆔 User ID: <code>{user_id}</code>\n"
        f"  🔗 Handle: @{username}\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}"
    )


async def log_account_added(user_id: int, phone_masked: str):
    await log_to_channel(
        f"<b>SYSTEM: ASSET LINKED</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  📱 Account: <code>{phone_masked}</code>\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}"
    )


async def log_account_deleted(user_id: int, phone_masked: str):
    await log_to_channel(
        f"<b>SYSTEM: ASSET REMOVED</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  📱 Account: <code>{phone_masked}</code>\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}"
    )


async def log_ads_started(user_id: int, accounts: int, groups: int, interval: int):
    await log_to_channel(
        f"<b>ENGINE: BROADCAST ACTIVATED</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  📱 Active Assets: {accounts}\n"
        f"  📂 Target Pool: {groups}\n"
        f"  ⏱ Cycle Interval: {interval}s\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}",
        silent=False
    )


async def log_ads_stopped(user_id: int):
    await log_to_channel(
        f"<b>ENGINE: BROADCAST TERMINATED</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}",
        silent=False
    )


async def log_broadcast_cycle(user_id: int, sent: int, failed: int):
    await log_to_channel(
        f"<b>ENGINE: CYCLE COMPLETE</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  ✅ Delivered: {sent}\n"
        f"  ❌ Errors: {failed}\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}"
    )


async def log_night_mode(user_id: int, action: str):
    status = "ENGAGED" if action == "start" else "DISENGAGED"
    await log_to_channel(
        f"<b>SYSTEM: NIGHT GUARD {status}</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}"
    )


async def log_error(user_id: int, error_type: str, details: str = ""):
    await log_to_channel(
        f"<b>CRITICAL: EXCEPTION</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  ⚠️ Type: {error_type}\n"
        f"  📄 Detail: {details}\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}",
        silent=False
    )


async def log_groups_added(user_id: int, added: int, failed: int):
    await log_to_channel(
        f"<b>SYSTEM: TARGETS IMPORTED</b>\n"
        f"{_divider()}\n"
        f"  👤 Operator: <code>{user_id}</code>\n"
        f"  📂 Added: {added}\n"
        f"  🚫 Failed: {failed}\n"
        f"  ⏰ Time: {_now_str()}\n"
        f"{_divider()}"
    )
