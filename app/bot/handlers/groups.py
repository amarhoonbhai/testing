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


@require_join
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
    initial_links = [line.strip() for line in text.split("\n") if line.strip()]

    if not initial_links:
        await update.message.reply_text(
            messages.error_text("No valid links found. Send one link per line."),
            parse_mode="HTML",
        )
        return WAITING_LINKS

    final_links = []
    status_msg = await update.message.reply_text("<i>🔍 Analyzing links...</i>", parse_mode="HTML")

    from app.database.models import parse_telegram_link, get_user_accounts
    from app.services.encryption_service import decrypt_session
    from app.services.telethon_service import get_client_from_session, expand_folder_link

    accounts = await get_user_accounts(user_id)
    active_acc = next((a for a in accounts if a.get("status") == "active"), None)

    for link in initial_links:
        parsed = parse_telegram_link(link)
        if parsed and parsed["type"] == "folder":
            if not active_acc:
                await update.message.reply_text(
                    messages.error_text("Connect at least one active account to expand Folder links."),
                    parse_mode="HTML"
                )
                continue
            
            # Expand folder
            try:
                session = decrypt_session(active_acc["encrypted_session"])
                async with await get_client_from_session(session) as client:
                    folder_links = await expand_folder_link(client, parsed["identifier"])
                    final_links.extend(folder_links)
            except Exception as e:
                logger.error(f"Folder expansion failed: {e}")
                final_links.append(link) # Fallback to original
        else:
            final_links.append(link)

    result = await add_groups_bulk(user_id, final_links)
    await log_groups_added(user_id, result["added"], result["failed"])

    await status_msg.delete()
    await update.message.reply_text(
        messages.groups_added_text(result["added"], result["failed"]),
        parse_mode="HTML",
        reply_markup=keyboards.groups_after_add_keyboard(),
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
        "<b>K U R U P  A D S</b>\n"
        "────────────────────────\n"
        "<b>CONFIRM PURGE</b>\n"
        "\n"
        "This will remove ALL your broadcast\n"
        "target groups. Proceed?\n"
        "────────────────────────",
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
        "<b>K U R U P  A D S</b>\n"
        "────────────────────────\n"
        "<b>POOL CLEARED</b>\n"
        "\n"
        f"Successfully removed <b>{deleted}</b> targets.\n"
        "────────────────────────",
        keyboards.back_keyboard("manage_groups"),
    )


async def _cancel_to_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation and go back to groups."""
    query = update.callback_query
    if query:
        await query.answer()
    await manage_groups_callback(update, context)
    return ConversationHandler.END


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
            CallbackQueryHandler(_cancel_to_groups, pattern="^cancel_conv$"),
            CallbackQueryHandler(_cancel_to_groups, pattern="^manage_groups$"),
            CallbackQueryHandler(_cancel_to_groups, pattern="^dashboard$"),
            CallbackQueryHandler(_cancel_to_groups, pattern="^home$"),
        ],
        per_user=True, per_chat=True, per_message=False,
    )
