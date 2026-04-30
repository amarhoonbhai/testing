"""
Auto Reply handler — configure automatic reply messages.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.database.models import get_user, update_user
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

WAITING_AR_TEXT = 0


@require_join
async def auto_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show auto-reply settings."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    enabled = user.get("auto_reply_enabled", False) if user else False
    reply_text = user.get("auto_reply_text") if user else None

    text = messages.auto_reply_text(enabled, reply_text)
    await _send_menu(update, context, text, keyboards.auto_reply_keyboard(enabled))


@require_join
async def ar_enable_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable auto-reply."""
    query = update.callback_query
    await query.answer("✅ Auto Reply Enabled")
    await update_user(query.from_user.id, auto_reply_enabled=True)

    user = await get_user(query.from_user.id)
    text = messages.auto_reply_text(True, user.get("auto_reply_text"))
    await _send_menu(update, context, text, keyboards.auto_reply_keyboard(True))


@require_join
async def ar_disable_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable auto-reply."""
    query = update.callback_query
    await query.answer("🔴 Auto Reply Disabled")
    await update_user(query.from_user.id, auto_reply_enabled=False)

    user = await get_user(query.from_user.id)
    text = messages.auto_reply_text(False, user.get("auto_reply_text"))
    await _send_menu(update, context, text, keyboards.auto_reply_keyboard(False))


async def ar_set_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask for auto-reply text."""
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        messages.set_auto_reply_prompt_text(),
        keyboards.cancel_keyboard(),
    )
    return WAITING_AR_TEXT


async def receive_ar_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive auto-reply text."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    await update_user(user_id, auto_reply_text=text)
    await update.message.reply_text(
        messages.auto_reply_saved_text(),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("auto_reply"),
    )
    return ConversationHandler.END


def build_auto_reply_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ar_set_text_callback, pattern="^ar_set_text$"),
        ],
        states={
            WAITING_AR_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ar_text),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                lambda u, c: ConversationHandler.END, pattern="^cancel_conv$"
            ),
        ],
        per_user=True, per_chat=True, per_message=False,
    )
