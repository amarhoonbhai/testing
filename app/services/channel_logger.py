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


async def log_to_channel(text: str, silent: bool = True):
    if not _bot or not LOGS_CHANNEL_ID:
        return
    try:
        formatted_text = (
            f"📋 <b>Logs | Update</b>\n"
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


def _divider() -> str:
    return "━━━━━━━━━━━━━━━━━━"


# ═══════════════════════════════════════════════════════════════════════════════
#  LOG EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

async def log_user_start(user_id: int, username: str, first_name: str):
    await log_to_channel(
        f"🌟 <b>USER STARTED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"📝 Name: {first_name}\n"
        f"🔗 Handle: @{username or 'None'}\n"
        f"⏱ Time: {_now_str()}\n"
    )


async def log_account_connected(user_id: int, phone: str):
    await log_to_channel(
        f"📱 <b>ACCOUNT CONNECTED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"📞 Phone: <code>{phone}</code>\n"
        f"⏱ Time: {_now_str()}\n"
    )


async def log_account_disconnected(user_id: int, phone: str):
    await log_to_channel(
        f"📵 <b>ACCOUNT DISCONNECTED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"📞 Phone: <code>{phone}</code>\n"
        f"⏱ Time: {_now_str()}\n"
    )


async def log_broadcast_started(user_id: int, group_count: int, interval: int):
    await log_to_channel(
        f"🚀 <b>CAMPAIGN STARTED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"🎯 Targets: <code>{group_count}</code> groups\n"
        f"⏳ Interval: <code>{interval // 60}</code> min\n"
        f"⏱ Started: {_now_str()}\n",
        silent=False,
    )


async def log_broadcast_stopped(user_id: int):
    await log_to_channel(
        f"🛑 <b>CAMPAIGN STOPPED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"⏱ Time: {_now_str()}\n",
        silent=False,
    )


async def log_broadcast_cycle(user_id: int, sent: int, failed: int, skipped: int):
    total = sent + failed + skipped
    status = "CLEAN" if failed == 0 else "PARTIAL"
    await log_to_channel(
        f"✅ <b>CYCLE COMPLETE [{status}]</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"📤 Sent: <b>{sent}</b> / {total}\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"⏭ Skipped: <b>{skipped}</b>\n"
        f"⏱ Time: {_now_str()}\n"
    )


async def log_broadcast_cycle_complete(user_id: int, sent: int, failed: int, skipped: int):
    await log_broadcast_cycle(user_id, sent, failed, skipped)


async def log_send_failed(user_id: int, group_link: str, error_type: str, details: str):
    await log_to_channel(
        f"⚠️ <b>SEND FAILED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"📢 Target: {group_link}\n"
        f"❌ Reason: {error_type}\n"
        f"🧾 Details: {details[:100]}\n"
        f"➡️ Action: Skipped and continued\n"
    )


async def log_groups_added(user_id: int, added: int, total: int):
    await log_to_channel(
        f"📥 <b>GROUPS IMPORTED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"➕ Added: <b>{added}</b>\n"
        f"📊 Total: <b>{total}</b>\n"
        f"⏱ Time: {_now_str()}\n"
    )


async def log_error(user_id: int, error_type: str, details: str = ""):
    await log_to_channel(
        f"🚨 <b>CRITICAL ERROR</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"❌ Type: {error_type}\n"
        f"🧾 Detail: <i>{details[:150]}</i>\n"
        f"⏱ Time: {_now_str()}\n",
        silent=False,
    )


async def log_broadcast_error(user_id: int, details: str):
    await log_error(user_id, "Broadcast Error", details)


async def log_account_invalid(user_id: int, details: str):
    await log_to_channel(
        f"⚠️ <b>SESSION INVALID / REVOKED</b>\n"
        f"{_divider()}\n"
        f"👤 User: <code>{user_id}</code>\n"
        f"❌ Reason: {details}\n"
        f"➡️ Action: Session cleared & broadcasting stopped\n"
        f"⏱ Time: {_now_str()}\n",
        silent=False,
    )
