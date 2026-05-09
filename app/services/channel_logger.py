"""
Premium Telegram channel logger — Kurup Ads.

Sends system activity to the centralized logs channel with a professional aesthetic.
Redesigned to match the business UI style.
"""

import logging
from datetime import datetime
import pytz

from app.config import LOGS_CHANNEL_ID, TIMEZONE, BOT_USERNAME

logger = logging.getLogger(__name__)

_bot = None
_tz = pytz.timezone(TIMEZONE)


def set_bot(bot):
    global _bot
    _bot = bot


async def log_to_channel(text: str, silent: bool = True):
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
    return "━━━━━━━━━━━━━━━━━━━━━"


# ═══════════════════════════════════════════════════════════════════════════════
#  SYSTEM EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_user_start(user_id: int, username: str, first_name: str):
    await log_to_channel(
        f"<b>SYSTEM ‣ USER ACCESS</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{first_name}</code>\n"
        f"┊ ID        <code>{user_id}</code>\n"
        f"┊ Handle    @{username or 'None'}\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_account_added(user_id: int, phone: str):
    await log_to_channel(
        f"<b>SYSTEM ‣ ASSET LINKED</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Account   <code>{phone}</code>\n"
        f"┊ Status    <b>OPERATIONAL</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_account_deleted(user_id: int, phone: str):
    await log_to_channel(
        f"<b>SYSTEM ‣ ASSET REMOVED</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Account   <code>{phone}</code>\n"
        f"┊ Status    <b>DELETED</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_ads_started(user_id: int, accounts: int, groups: int, interval: int):
    await log_to_channel(
        f"<b>ENGINE ‣ BROADCAST INITIATED</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Assets    {accounts} active\n"
        f"┊ Targets   {groups} groups\n"
        f"┊ Interval  {interval // 60} min\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}",
        silent=False
    )


async def log_ads_stopped(user_id: int):
    await log_to_channel(
        f"<b>ENGINE ‣ BROADCAST HALTED</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Status    <b>PAUSED</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}",
        silent=False
    )


async def log_broadcast_cycle(user_id: int, sent: int, failed: int):
    status = "SUCCESS" if failed == 0 else "PARTIAL" if sent > 0 else "CRITICAL"
    await log_to_channel(
        f"<b>ENGINE ‣ CYCLE COMPLETE [{status}]</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Delivered <b>{sent}</b>\n"
        f"┊ Failed    <b>{failed}</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_message_sent(user_id: int, group: str, account: str, success: bool, error: str = None):
    # Only log failures to avoid flooding the channel during large cycles
    if success: return 
    
    await log_to_channel(
        f"<b>ENGINE ‣ DELIVERY EXCEPTION</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Account   <code>{account}</code>\n"
        f"┊ Target    <code>{group}</code>\n"
        f"┊ Reason    <i>{error or 'Unknown'}</i>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_error(user_id: int, error_type: str, details: str = ""):
    await log_to_channel(
        f"<b>CRITICAL ‣ SYSTEM EXCEPTION</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Type      {error_type}\n"
        f"┊ Detail    <i>{details}</i>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}",
        silent=False
    )


async def log_groups_added(user_id: int, added: int, failed: int):
    await log_to_channel(
        f"<b>SYSTEM ‣ TARGETS IMPORTED</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Added     <b>{added}</b>\n"
        f"┊ Failed    <b>{failed}</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_night_mode(user_id: int, action: str):
    status = "ENGAGED" if action == "start" else "DISENGAGED"
    await log_to_channel(
        f"<b>SYSTEM ‣ NIGHT GUARD {status}</b>\n"
        f"{_divider()}\n"
        f"┊ Operator  <code>{user_id}</code>\n"
        f"┊ Status    <b>{status}</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )
