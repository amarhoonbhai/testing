"""
Message handler — Set, preview, and clear the broadcast message.

Supports text, photo with caption, and video with caption.
Uses ConversationHandler for the set-message flow.
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

from app.database.models import get_user, set_message, clear_message
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join, end_conversation_callback

logger = logging.getLogger(__name__)

WAITING_MESSAGE = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  SET MESSAGE HUB
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def set_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show message management screen."""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    has_message = bool(user.get("message")) if user else False

    if has_message:
        text = messages.message_preview_text(user["message"])
    else:
        text = messages.no_message_text()

    await _send_menu(update, context, text, keyboards.message_keyboard(has_message))


# ═══════════════════════════════════════════════════════════════════════════════
#  INPUT MESSAGE CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def input_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask user for message content."""
    query = update.callback_query
    await query.answer()

    await _send_menu(
        update, context,
        messages.set_message_prompt_text(),
        keyboards.cancel_keyboard(),
    )
    return WAITING_MESSAGE


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the broadcast message (text, photo, or video)."""
    user_id = update.effective_user.id
    msg = update.message

    text = msg.text or msg.caption or ""
    media_type = None
    media_file_id = None

    if msg.photo:
        media_type = "photo"
        media_file_id = msg.photo[-1].file_id
    elif msg.video:
        media_type = "video"
        media_file_id = msg.video.file_id
    elif msg.text:
        media_type = None
    else:
        await update.message.reply_text(
            messages.error_text("Unsupported format. Send text, photo, or video."),
            parse_mode="HTML",
        )
        return WAITING_MESSAGE

    await set_message(user_id, text=text, media_type=media_type, media_file_id=media_file_id)

    await update.message.reply_text(
        messages.message_saved_text(),
        parse_mode="HTML",
        reply_markup=keyboards.after_message_saved_keyboard(),
    )
    return ConversationHandler.END


def build_message_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(input_message_callback, pattern="^input_message$"),
        ],
        states={
            WAITING_MESSAGE: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.VIDEO,
                    receive_message,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(end_conversation_callback, pattern="^cancel_conv$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^dashboard$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^set_message$"),
        ],
        per_user=True, per_chat=True, per_message=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PREVIEW & CLEAR
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def preview_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Preview the saved message."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)

    if not user or not user.get("message"):
        await _send_menu(
            update, context,
            messages.no_message_text(),
            keyboards.message_keyboard(False),
        )
        return

    msg = user["message"]
    text = msg.get("text") or ""
    media_type = msg.get("media_type")
    media_file_id = msg.get("media_file_id")

    caption = f"<b>MESSAGE PREVIEW</b>\n────────────────────\n\n{text}"
    chat_id = update.effective_chat.id

    try:
        # Delete the current message
        try:
            await query.message.delete()
        except Exception:
            pass

        if media_type == "photo" and media_file_id:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=media_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboards.back_keyboard("set_message"),
            )
        elif media_type == "video" and media_file_id:
            await context.bot.send_video(
                chat_id=chat_id,
                video=media_file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=keyboards.back_keyboard("set_message"),
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode="HTML",
                reply_markup=keyboards.back_keyboard("set_message"),
            )
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=messages.error_text("Failed to preview message."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("set_message"),
        )


@require_join
async def clear_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the saved message."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    await clear_message(user_id)

    await _send_menu(
        update, context,
        messages.message_cleared_text(),
        keyboards.back_keyboard("dashboard"),
    )
