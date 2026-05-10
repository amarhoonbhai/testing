"""
Admin panel handler — Owner-only system dashboard.
Shows total users, broadcasting count, and global stats.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

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
