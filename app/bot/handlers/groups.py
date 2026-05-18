"""
Groups handler — Add, view, manage broadcast target groups, diagnostics, and pruning.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.database.models import (
    get_user, add_groups, get_groups, get_group_count, clear_groups, update_user,
    get_group_reasons, prune_dead_groups
)
from app.config import MAX_FAIL_SKIP
from app.services.channel_logger import log_groups_added
from app.services import engine
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

WAITING_LINKS = 0


@require_join
async def manage_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show groups management screen."""
    user_id = update.effective_user.id
    count = await get_group_count(user_id)

    text = messages.groups_text(count)
    await _send_menu(update, context, text, keyboards.groups_keyboard())


@require_join
async def add_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask for group links."""
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        messages.add_groups_prompt_text(),
        keyboards.cancel_keyboard(),
    )
    return WAITING_LINKS


async def receive_group_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive group links (one per line)."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    links = [line.strip() for line in text.split("\n") if line.strip()]

    if not links:
        await update.message.reply_text(
            messages.error_text("No valid links found. Send one link per line."),
            parse_mode="HTML",
        )
        return WAITING_LINKS

    result = await add_groups(user_id, links)
    await log_groups_added(user_id, result["added"], result["total"])

    user = await get_user(user_id)
    if user and user.get("session_encrypted"):
        await engine.start(user_id)

    text = messages.groups_added_text(result["added"], result["total"])
    if result.get("limit_reached"):
        text += "\n\n⚠️ <b>Note:</b> Maximum limit of 50 groups per account reached."

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboards.groups_after_add_keyboard(),
    )
    return ConversationHandler.END


@require_join
async def view_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all added groups."""
    user_id = update.effective_user.id
    groups = await get_groups(user_id)

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
        messages.confirm_clear_groups_text(),
        keyboards.confirm_clear_groups_keyboard(),
    )


async def confirm_clear_groups_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Execute clear all groups."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    await engine.stop(user_id)
    deleted = await clear_groups(user_id)

    await _send_menu(
        update, context,
        messages.groups_cleared_text(deleted),
        keyboards.back_keyboard("manage_groups"),
    )


@require_join
async def live_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View active live groups."""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    groups = user.get("groups", []) if user else []
    group_fails = user.get("group_fails", {}) if user else {}

    live_groups = [g for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) < MAX_FAIL_SKIP]
    text = messages.live_groups_text(live_groups)
    await _send_menu(update, context, text, keyboards.back_keyboard("manage_groups"))


@require_join
async def paused_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View paused/skipped groups."""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    groups = user.get("groups", []) if user else []
    group_fails = user.get("group_fails", {}) if user else {}

    paused_groups = [g for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) >= MAX_FAIL_SKIP]
    text = messages.paused_groups_text(paused_groups)
    await _send_menu(update, context, text, keyboards.paused_groups_keyboard())


@require_join
async def reset_paused_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset fail counts for all groups to 0."""
    query = update.callback_query
    await query.answer("Resetting paused groups...")
    user_id = query.from_user.id

    await update_user(user_id, group_fails={}, group_reasons={})
    await _send_menu(
        update, context,
        messages.success_text("All paused groups have been reset to Live status!"),
        keyboards.back_keyboard("manage_groups")
    )


@require_join
async def group_diagnostics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View detailed failure reasons for paused/failing groups."""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    groups = user.get("groups", []) if user else []
    group_fails = user.get("group_fails", {}) if user else {}
    reasons = await get_group_reasons(user_id)

    paused_groups = [g for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) >= MAX_FAIL_SKIP]
    
    text = messages.group_diagnostics_text(reasons, paused_groups)
    await _send_menu(update, context, text, keyboards.back_keyboard("manage_groups"))


@require_join
async def prune_dead_groups_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Automatically remove all permanently failing groups."""
    query = update.callback_query
    await query.answer("Pruning dead groups...")
    user_id = query.from_user.id

    pruned = await prune_dead_groups(user_id, MAX_FAIL_SKIP)

    await _send_menu(
        update, context,
        messages.success_text(f"Successfully pruned <b>{pruned}</b> permanently failing groups from your roster."),
        keyboards.back_keyboard("manage_groups")
    )


async def _cancel_to_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation and go back to groups."""
    query = update.callback_query
    if query:
        await query.answer()
    await manage_groups_callback(update, context)
    return ConversationHandler.END


def build_add_groups_conversation() -> ConversationHandler:
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
        per_user=True, per_chat=True,
    )
