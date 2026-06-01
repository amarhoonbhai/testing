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


def get_bot():
    return _bot


async def log_to_channel(text: str, header: str, silent: bool = True):
    if not _bot or not LOGS_CHANNEL_ID:
        return
    try:
        formatted_text = (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{text}"
        )
        await _bot.send_message(
            chat_id=LOGS_CHANNEL_ID,
            text=formatted_text,
            parse_mode="HTML",
            disable_notification=silent,
        )
    except Exception as e:
        logger.warning(f"Failed to send log to channel: {type(e).__name__}")


def _now_str() -> str:
    return datetime.now(_tz).strftime("%I:%M %p")


def _progress_bar(percentage: float, width: int = 10) -> str:
    filled = int(round(percentage * width / 100))
    return "▰" * filled + "▱" * (width - filled)


# ═══════════════════════════════════════════════════════════════════════════════
#  LOG EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_user_start(user_id: int, username: str, first_name: str):
    user_link = f"<a href='tg://user?id={user_id}'>{first_name}</a>"
    handle = f"@{username}" if username else "None"
    text = (
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Name: {user_link}\n"
        f"🔗 Handle: {handle}\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="👤 <b>NEW USER REGISTERED</b>")


async def log_account_connected(user_id: int, phone: str):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"📞 Phone: <code>{phone}</code>\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="🟢 <b>ACCOUNT AUTHORIZED</b>", silent=False)


async def log_account_disconnected(user_id: int, phone: str):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"📞 Phone: <code>{phone}</code>\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="🔴 <b>ACCOUNT DISCONNECTED</b>", silent=False)


async def log_broadcast_started(user_id: int, group_count: int, interval: int):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"🎯 Targets: <code>{group_count}</code> groups\n"
        f"⏳ Interval: <code>{interval // 60}</code> min\n"
        f"⏱ Started: {_now_str()}\n"
    )
    await log_to_channel(text, header="🚀 <b>CAMPAIGN ACTIVATED</b>", silent=False)


async def log_broadcast_stopped(user_id: int):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="🛑 <b>CAMPAIGN SUSPENDED</b>", silent=False)


async def log_broadcast_cycle(user_id: int, sent: int, failed: int, skipped: int):
    total = sent + failed + skipped
    status = "CLEAN" if failed == 0 else "PARTIAL"
    
    pct = (sent / total * 100) if total > 0 else 0.0
    pbar = _progress_bar(pct, width=10)
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    
    text = (
        f"📊 Status: <code>{status}</code>\n"
        f"👤 User: {user_link}\n"
        f"📈 Progress: <code>{pbar}</code> {pct:.1f}%\n"
        f"📤 Success: <b>{sent}</b> / {total}\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"⏭ Skipped: <b>{skipped}</b>\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header=f"⚡ <b>CYCLE COMPLETED [{status}]</b>")


async def log_broadcast_cycle_complete(user_id: int, sent: int, failed: int, skipped: int):
    await log_broadcast_cycle(user_id, sent, failed, skipped)


async def log_send_failed(user_id: int, group_link: str, error_type: str, details: str):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"📢 Target: {group_link}\n"
        f"❌ Reason: {error_type}\n"
        f"🧾 Details: <i>{details[:100]}</i>\n"
        f"➡️ Action: Skipped and continued\n"
    )
    await log_to_channel(text, header="⚠️ <b>MESSAGE DISPATCH FAILED</b>")


async def log_groups_added(user_id: int, added: int, total: int):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"➕ Added: <b>{added}</b>\n"
        f"📊 Total Roster: <b>{total}</b>\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="📥 <b>ROSTER TARGETS IMPORTED</b>")


async def log_error(user_id: int, error_type: str, details: str = ""):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"❌ Type: {error_type}\n"
        f"🧾 Detail: <i>{details[:150]}</i>\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="🚨 <b>SYSTEM CRITICAL ERROR</b>", silent=False)


async def log_broadcast_error(user_id: int, details: str):
    await log_error(user_id, "Broadcast Error", details)


async def log_account_invalid(user_id: int, details: str):
    user_link = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    text = (
        f"👤 User: {user_link}\n"
        f"❌ Reason: <b>{details}</b>\n"
        f"➡️ Action: Session cleared & broadcasting stopped\n"
        f"⏱ Time: {_now_str()}\n"
    )
    await log_to_channel(text, header="🔒 <b>SESSION REVOKED / INVALID</b>", silent=False)
