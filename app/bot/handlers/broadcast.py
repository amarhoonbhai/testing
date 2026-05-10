"""
Broadcast handler — Start/Stop broadcasting + Set interval.

Validates prerequisites before starting and manages the broadcast engine.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from app.config import MIN_INTERVAL
from app.database.models import get_user, set_interval
from app.services import engine
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join, end_conversation_callback

logger = logging.getLogger(__name__)

WAITING_INTERVAL = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  START / STOP
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def start_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcasting."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    result = await engine.start(user_id)

    if result["success"]:
        await _send_menu(
            update, context,
            messages.broadcast_started_text(),
            keyboards.back_keyboard("dashboard"),
        )
    else:
        await _send_menu(
            update, context,
            messages.error_text(result["error"]),
            keyboards.back_keyboard("dashboard"),
        )


@require_join
async def stop_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop broadcasting."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    await engine.stop(user_id)

    await _send_menu(
        update, context,
        messages.broadcast_stopped_text(),
        keyboards.back_keyboard("dashboard"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  SET INTERVAL
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def set_interval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask user for interval in seconds."""
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        messages.set_interval_prompt_text(MIN_INTERVAL),
        keyboards.cancel_keyboard(),
    )
    return WAITING_INTERVAL


async def receive_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive interval value."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        seconds = int(text)
    except ValueError:
        await update.message.reply_text(
            messages.error_text("Please enter a valid number."),
            parse_mode="HTML",
        )
        return WAITING_INTERVAL

    if seconds < MIN_INTERVAL:
        await update.message.reply_text(
            messages.error_text(f"Minimum interval is {MIN_INTERVAL} seconds ({MIN_INTERVAL // 60} min)."),
            parse_mode="HTML",
        )
        return WAITING_INTERVAL

    await set_interval(user_id, seconds)

    await update.message.reply_text(
        messages.interval_saved_text(seconds),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("dashboard"),
    )
    return ConversationHandler.END


def build_interval_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_interval_callback, pattern="^set_interval$"),
        ],
        states={
            WAITING_INTERVAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_interval),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(end_conversation_callback, pattern="^cancel_conv$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^dashboard$"),
        ],
        per_user=True, per_chat=True,
    )
