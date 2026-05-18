"""
Message handler — Set, preview, and clear the broadcast message.

Supports text, photo with caption, and video with caption.
Uses ConversationHandler for the set-message flow.
"""

import logging
import os
import uuid
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
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session, send_message_to_saved_messages

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
    media_path = None

    if msg.photo or msg.video:
        media_dir = "downloads"
        os.makedirs(media_dir, exist_ok=True)
        file_ext = ".jpg" if msg.photo else ".mp4"
        media_path = os.path.join(media_dir, f"{user_id}_{uuid.uuid4().hex}{file_ext}")
        
        if msg.photo:
            media_type = "photo"
            file = await context.bot.get_file(msg.photo[-1].file_id)
        else:
            media_type = "video"
            file = await context.bot.get_file(msg.video.file_id)
            
        await file.download_to_drive(media_path)
    elif msg.text:
        media_type = None
    else:
        await update.message.reply_text(
            messages.error_text("Unsupported format. Send text, photo, or video."),
            parse_mode="HTML",
        )
        return WAITING_MESSAGE

    await set_message(user_id, text=text, media_type=media_type, media_path=media_path)

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
        per_user=True, per_chat=True,
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
    media_path = msg.get("media_path")

    caption = f"<b>MESSAGE PREVIEW</b>\n────────────────────\n\n{text}"
    chat_id = update.effective_chat.id

    try:
        # Delete the current message
        try:
            await query.message.delete()
        except Exception:
            pass

        if media_type == "photo" and media_path and os.path.exists(media_path):
            with open(media_path, 'rb') as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=keyboards.back_keyboard("set_message"),
                )
        elif media_type == "video" and media_path and os.path.exists(media_path):
            with open(media_path, 'rb') as f:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=f,
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


@require_join
async def send_to_saved_messages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast message to user's Saved Messages."""
    query = update.callback_query
    await query.answer("Connecting to Telegram...")
    user_id = query.from_user.id

    user = await get_user(user_id)
    if not user or not user.get("session_encrypted"):
        await query.edit_message_text(
            messages.error_text("You must connect your Telegram account first."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("set_message"),
        )
        return

    message = user.get("message")
    if not message:
        await query.edit_message_text(
            messages.error_text("No broadcast message configured."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("set_message"),
        )
        return

    client = None
    try:
        session = decrypt_session(user["session_encrypted"])
        client = await get_client_from_session(session)
        
        result = await send_message_to_saved_messages(client, message)
        if result.get("success"):
            text = messages.saved_messages_success_text()
        else:
            text = messages.saved_messages_error_text(result.get("error_message", "Unknown Error"))

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("set_message"),
        )
    except Exception as e:
        logger.error(f"Send to saved messages failed: {e}")
        await query.edit_message_text(
            messages.saved_messages_error_text(str(e)),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("set_message"),
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
