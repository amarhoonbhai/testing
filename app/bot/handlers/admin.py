"""
Admin panel handler — Owner-only system dashboard.
Shows total users, broadcasting count, and global stats.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.config import OWNER_ID
from app.database.models import get_global_stats
from app.bot import keyboards, messages
from app.bot.handlers.start import _send_menu

logger = logging.getLogger(__name__)


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
    """Build and show the admin panel."""
    stats = await get_global_stats()
    text = messages.admin_panel_text(stats)
    await _send_menu(update, context, text, keyboards.admin_keyboard())


# ── View All Users Telemetry ─────────────────────────────────────────────────

async def admin_view_all_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all users stats & health."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        query = update.callback_query
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    from app.database.models import get_all_users
    users = await get_all_users()
    text = messages.admin_all_users_stats_text(users)
    await _send_menu(update, context, text, keyboards.admin_all_users_keyboard())


# ── Manage Premium ───────────────────────────────────────────────────────────

WAITING_USER_ID = 1

async def admin_manage_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for user ID to manage premium."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        query = update.callback_query
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    await _send_menu(
        update, context,
        messages.admin_premium_prompt_text(),
        keyboards.back_keyboard("admin")
    )
    return WAITING_USER_ID


async def receive_premium_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive user ID and show premium status."""
    user_id = update.effective_user.id
    if not _is_owner(user_id):
        return ConversationHandler.END

    target_id_str = update.message.text.strip()
    try:
        target_id = int(target_id_str)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID format. Please enter a valid number.",
            reply_markup=keyboards.back_keyboard("admin")
        )
        return ConversationHandler.END

    from app.database.models import get_user
    target_user = await get_user(target_id)
    if not target_user:
        await update.message.reply_text(
            f"❌ User ID <code>{target_id}</code> not found in database.",
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("admin")
        )
        return ConversationHandler.END

    text = messages.admin_premium_user_text(target_user)
    reply_markup = keyboards.admin_manage_premium_keyboard(target_id, target_user.get("is_premium", False))
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    return ConversationHandler.END


async def admin_toggle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant or revoke premium status."""
    query = update.callback_query
    user_id = query.from_user.id
    if not _is_owner(user_id):
        await query.answer("⛔ Access denied.", show_alert=True)
        return

    data = query.data
    from app.database.models import update_user_premium
    if data.startswith("grant_prem_"):
        target_id = int(data.split("_")[2])
        await update_user_premium(target_id, True)
        await query.answer("✅ Premium granted!", show_alert=True)
    elif data.startswith("revoke_prem_"):
        target_id = int(data.split("_")[2])
        await update_user_premium(target_id, False)
        await query.answer("❌ Premium revoked!", show_alert=True)

    await _show_admin_panel(update, context)


async def _cancel_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    await _show_admin_panel(update, context)
    return ConversationHandler.END


def build_admin_premium_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_manage_premium_callback, pattern="^admin_manage_premium$"),
        ],
        states={
            WAITING_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_premium_user_id),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(_cancel_to_admin, pattern="^admin$"),
            CallbackQueryHandler(_cancel_to_admin, pattern="^dashboard$"),
            CallbackQueryHandler(_cancel_to_admin, pattern="^home$"),
        ],
        per_user=True, per_chat=True,
    )
