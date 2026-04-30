"""
Admin panel handler — Owner-only system dashboard.

Shows all users, accounts, broadcast health, and performance.
Only accessible by OWNER_ID.
"""

import logging
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from app.config import OWNER_ID, TIMEZONE, BOT_USERNAME
from app.database.mongo import get_db
from app.bot import keyboards
from app.bot.handlers.start import _send_menu
from app.services.broadcast_service import get_active_broadcast_count

logger = logging.getLogger(__name__)
_tz = pytz.timezone(TIMEZONE)


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        await update.message.reply_text("⛔ Access denied.", parse_mode="HTML")
        return
    await _show_admin_panel(update, context)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callback."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        query = update.callback_query
        await query.answer("⛔ Access denied.", show_alert=True)
        return
    await _show_admin_panel(update, context)


async def _show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Build and show the admin panel with live system stats."""
    db = get_db()

    # Gather stats
    total_users = await db.users.count_documents({})
    total_accounts = await db.accounts.count_documents({})
    active_accounts = await db.accounts.count_documents({"status": "active"})
    error_accounts = await db.accounts.count_documents({"status": "error"})
    total_groups = await db.groups.count_documents({})
    active_groups = await db.groups.count_documents({"status": "active"})

    # Ads stats
    running_users = await db.users.count_documents({"ads_status": "running"})
    paused_users = await db.users.count_documents({"ads_status": "paused"})

    # Analytics aggregation
    pipeline = [
        {"$group": {
            "_id": None,
            "total_sent": {"$sum": "$total_sent"},
            "total_failed": {"$sum": "$failed_count"},
        }}
    ]
    agg = await db.analytics.aggregate(pipeline).to_list(1)
    global_sent = agg[0]["total_sent"] if agg else 0
    global_failed = agg[0]["total_failed"] if agg else 0

    # Active broadcasts
    active_broadcasts = get_active_broadcast_count()

    now = datetime.now(_tz).strftime("%Y-%m-%d %H:%M:%S IST")

    text = (
        f"        ─── ⚙ ───\n"
        f"    <b>Admin Panel</b>\n"
        f"    @{BOT_USERNAME}\n"
        f"        ─── ⚙ ───\n"
        f"\n"
        f"   <b>Users</b>\n"
        f"   ┊ Total       {total_users}\n"
        f"   ┊ Running     {running_users}\n"
        f"   ┊ Paused      {paused_users}\n"
        f"\n"
        f"   <b>Accounts</b>\n"
        f"   ┊ Total       {total_accounts}\n"
        f"   ┊ Active      {active_accounts} ●\n"
        f"   ┊ Errors      {error_accounts} ✕\n"
        f"\n"
        f"   <b>Groups</b>\n"
        f"   ┊ Total       {total_groups}\n"
        f"   ┊ Active      {active_groups}\n"
        f"\n"
        f"   <b>Performance</b>\n"
        f"   ┊ Sent        {global_sent}\n"
        f"   ┊ Failed      {global_failed}\n"
        f"   ┊ Live Now    {active_broadcasts}\n"
        f"   ┊ Rate        {_success_rate(global_sent, global_failed)}\n"
        f"\n"
        f"   🕐 {now}"
    )

    await _send_menu(update, context, text, keyboards.admin_keyboard())


async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent users list."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        return

    db = get_db()
    cursor = db.users.find({}).sort("last_seen", -1).limit(20)
    users = await cursor.to_list(20)

    lines = [
        f"        ─── 👥 ───",
        f"    <b>Recent Users</b>",
        f"        ─── 👥 ───",
        f"",
    ]
    for i, u in enumerate(users, 1):
        uid = u.get("telegram_user_id", "?")
        uname = u.get("username", "—")
        status = u.get("ads_status", "paused")
        dot = "●" if status == "running" else "○"
        lines.append(f"   {dot}  {i}. <code>{uid}</code>  @{uname}")

    text = "\n".join(lines)
    await _send_menu(update, context, text, keyboards.admin_back_keyboard())


async def admin_health_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show account health overview."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        return

    db = get_db()
    accounts = await db.accounts.find({}).to_list(100)

    lines = [
        f"        ─── 🏥 ───",
        f"    <b>Account Health</b>",
        f"        ─── 🏥 ───",
        f"",
    ]

    for acc in accounts[:30]:
        phone = acc.get("phone_masked", "***")
        status = acc.get("status", "?")
        uid = acc.get("user_id", "?")

        if status == "active":
            dot = "●"
        elif status == "error":
            dot = "✕"
        else:
            dot = "○"

        lines.append(f"   {dot}  <code>{phone}</code>  user:<code>{uid}</code>")

    total = len(accounts)
    if total > 30:
        lines.append(f"\n   <i>+ {total - 30} more</i>")

    text = "\n".join(lines)
    await _send_menu(update, context, text, keyboards.admin_back_keyboard())


async def admin_broadcast_stats_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Show per-user broadcast statistics."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        return

    db = get_db()
    cursor = db.analytics.find({}).sort("total_sent", -1).limit(20)
    stats = await cursor.to_list(20)

    lines = [
        f"        ─── 📊 ───",
        f"    <b>Top Broadcasters</b>",
        f"        ─── 📊 ───",
        f"",
    ]

    for i, s in enumerate(stats, 1):
        uid = s.get("user_id", "?")
        sent = s.get("total_sent", 0)
        failed = s.get("failed_count", 0)
        last = s.get("last_broadcast_at")
        last_str = last.strftime("%m/%d %H:%M") if last else "Never"
        lines.append(
            f"   {i}. <code>{uid}</code>  "
            f"sent:{sent}  fail:{failed}  {last_str}"
        )

    text = "\n".join(lines)
    await _send_menu(update, context, text, keyboards.admin_back_keyboard())


def _success_rate(sent: int, failed: int) -> str:
    total = sent + failed
    if total == 0:
        return "N/A"
    rate = (sent / total) * 100
    return f"{rate:.1f}%"
