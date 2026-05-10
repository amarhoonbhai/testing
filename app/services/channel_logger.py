"""
Telegram channel logger — Group Broadcaster.

Sends system activity to the centralized logs channel.
"""

import logging
from datetime import datetime
import pytz

from app.config import LOGS_CHANNEL_ID, TIMEZONE

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
#  LOG EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_user_start(user_id: int, username: str, first_name: str):
    await log_to_channel(
        f"<b>USER ACCESS</b>\n"
        f"{_divider()}\n"
        f"┊ Name      <code>{first_name}</code>\n"
        f"┊ ID        <code>{user_id}</code>\n"
        f"┊ Handle    @{username or 'None'}\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_account_connected(user_id: int, phone: str):
    await log_to_channel(
        f"<b>ACCOUNT CONNECTED</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Phone     <code>{phone}</code>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_account_disconnected(user_id: int, phone: str):
    await log_to_channel(
        f"<b>ACCOUNT DISCONNECTED</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Phone     <code>{phone}</code>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_broadcast_started(user_id: int, group_count: int, interval: int):
    await log_to_channel(
        f"<b>BROADCAST STARTED</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Groups    {group_count}\n"
        f"┊ Interval  {interval // 60} min\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}",
        silent=False,
    )


async def log_broadcast_stopped(user_id: int):
    await log_to_channel(
        f"<b>BROADCAST STOPPED</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}",
        silent=False,
    )


async def log_broadcast_cycle(user_id: int, sent: int, failed: int, skipped: int):
    total = sent + failed + skipped
    status = "CLEAN" if failed == 0 else "PARTIAL"
    await log_to_channel(
        f"<b>CYCLE COMPLETE [{status}]</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Sent      <b>{sent}</b> / {total}\n"
        f"┊ Failed    <b>{failed}</b>\n"
        f"┊ Skipped   <b>{skipped}</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_groups_added(user_id: int, added: int, total: int):
    await log_to_channel(
        f"<b>GROUPS IMPORTED</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Added     <b>{added}</b>\n"
        f"┊ Total     <b>{total}</b>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}"
    )


async def log_error(user_id: int, error_type: str, details: str = ""):
    await log_to_channel(
        f"<b>ERROR</b>\n"
        f"{_divider()}\n"
        f"┊ User      <code>{user_id}</code>\n"
        f"┊ Type      {error_type}\n"
        f"┊ Detail    <i>{details}</i>\n"
        f"┊ Time      {_now_str()}\n"
        f"{_divider()}",
        silent=False,
    )
