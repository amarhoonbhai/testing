"""
Groups handler — Add, view, and manage broadcast target groups.

Supports:
- Single group/channel links (t.me/username, t.me/+invite, @username)
- Folder links (t.me/addlist/xxx)
- Multi-link paste (one per line)
- View/delete groups
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.database.models import (
    get_user_groups, get_group_count, add_groups_bulk,
    delete_all_groups, delete_group, parse_telegram_link,
)
from app.services.channel_logger import log_groups_added
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

WAITING_LINKS = 0


@require_join
async def manage_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show groups management screen."""
    user_id = update.effective_user.id
    groups = await get_user_groups(user_id)
    group_count = len(groups)

    active = sum(1 for g in groups if g.get("status") == "active")
    disabled = group_count - active

    text = messages.groups_text(group_count, active, disabled)
    await _send_menu(update, context, text, keyboards.groups_keyboard())


async def add_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask for group links."""
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        messages.add_groups_text(),
        keyboards.cancel_keyboard(),
    )
    return WAITING_LINKS


async def receive_group_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive group links (one per line)."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Split by newlines, filter empty
    links = [line.strip() for line in text.split("\n") if line.strip()]

    if not links:
        await update.message.reply_text(
            messages.error_text("No valid links found. Send one link per line."),
            parse_mode="HTML",
        )
        return WAITING_LINKS

    result = await add_groups_bulk(user_id, links)
    await log_groups_added(user_id, result["added"], result["failed"])

    await update.message.reply_text(
        messages.groups_added_text(result["added"], result["failed"]),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("manage_groups"),
    )
    return ConversationHandler.END


@require_join
async def view_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all added groups."""
    user_id = update.effective_user.id
    groups = await get_user_groups(user_id)

    if not groups:
        await _send_menu(
            update, context,
            messages.no_groups_text(),
            keyboards.groups_keyboard(),
        )
        return

    text = messages.groups_list_text(groups)
    await _send_menu(update, context, text, keyboards.groups_list_keyboard())


@require_join
async def clear_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask confirmation to clear all groups."""
    await _send_menu(
        update, context,
        "⌞_⌝ <b>CLEAR ALL GROUPS</b>\n\n"
        "⚠️ This will delete ALL your broadcast target groups.\n\n"
        "Are you sure?",
        keyboards.confirm_clear_groups_keyboard(),
    )


async def confirm_clear_groups_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Execute clear all groups."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    deleted = await delete_all_groups(user_id)

    await _send_menu(
        update, context,
        f"⌞_⌝ <b>GROUPS CLEARED</b> 🗑️\n\n"
        f"Removed <b>{deleted}</b> groups.",
        keyboards.back_keyboard("manage_groups"),
    )


def build_add_groups_conversation() -> ConversationHandler:
    """Build conversation handler for adding groups."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_groups_callback, pattern="^add_groups$"),
        ],
        states={
            WAITING_LINKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_group_links),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                lambda u, c: ConversationHandler.END, pattern="^cancel_conv$"
            ),
            CallbackQueryHandler(
                lambda u, c: ConversationHandler.END, pattern="^manage_groups$"
            ),
        ],
        per_user=True, per_chat=True, per_message=False,
    )
