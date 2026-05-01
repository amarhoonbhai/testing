"""
Ads handler — Set Ad Message, Set Interval, Start/Stop Ads.
Uses ConversationHandler for multi-step flows.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.config import MIN_INTERVAL
from app.database.models import (
    get_user, update_user, get_user_accounts, get_account_count, get_group_count,
)
from app.services.broadcast_service import start_broadcast, stop_broadcast
from app.services.channel_logger import log_ads_started, log_ads_stopped
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

# Conversation states
WAITING_AD, WAITING_INTERVAL = range(2)


# ═══════════════════════════════════════════════════════════════════════════════
#  SET AD MESSAGE
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def set_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask user for ad content."""
    query = update.callback_query
    await query.answer()
    await _send_menu(update, context, messages.set_ad_text(), keyboards.cancel_keyboard())
    return WAITING_AD


async def receive_ad_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the ad message (text, photo, or video)."""
    user_id = update.effective_user.id
    fields = {}

    if update.message.photo:
        fields["ad_media_type"] = "photo"
        fields["ad_media_file_id"] = update.message.photo[-1].file_id
        fields["ad_message"] = update.message.caption or ""
    elif update.message.video:
        fields["ad_media_type"] = "video"
        fields["ad_media_file_id"] = update.message.video.file_id
        fields["ad_message"] = update.message.caption or ""
    elif update.message.text:
        fields["ad_media_type"] = None
        fields["ad_media_file_id"] = None
        fields["ad_message"] = update.message.text
    else:
        await update.message.reply_text(
            messages.error_text("Unsupported format. Send text, photo, or video."),
            parse_mode="HTML",
        )
        return WAITING_AD

    await update_user(user_id, **fields)
    await update.message.reply_text(
        messages.ad_saved_text(), parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("dashboard"),
    )
    return ConversationHandler.END


def build_set_ad_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(set_ad_callback, pattern="^set_ad$")],
        states={
            WAITING_AD: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.VIDEO & ~filters.COMMAND,
                    receive_ad_message,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancel_conv$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^dashboard$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^home$"),
        ],
        per_user=True, per_chat=True, per_message=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  SET TIME INTERVAL
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def set_interval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask user for interval in seconds."""
    query = update.callback_query
    await query.answer()
    await _send_menu(update, context, messages.set_interval_text(), keyboards.cancel_keyboard())
    return WAITING_INTERVAL


async def receive_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive interval value."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        seconds = int(text)
    except ValueError:
        await update.message.reply_text(
            messages.error_text("Please enter a valid number."), parse_mode="HTML",
        )
        return WAITING_INTERVAL

    if seconds < MIN_INTERVAL:
        await update.message.reply_text(
            messages.error_text(f"Minimum interval is {MIN_INTERVAL} seconds."),
            parse_mode="HTML",
        )
        return WAITING_INTERVAL

    await update_user(user_id, interval_seconds=seconds)
    await update.message.reply_text(
        messages.interval_saved_text(seconds), parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("dashboard"),
    )
    return ConversationHandler.END


def build_set_interval_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(set_interval_callback, pattern="^set_interval$")],
        states={
            WAITING_INTERVAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_interval),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancel_conv$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^dashboard$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^home$"),
        ],
        per_user=True, per_chat=True, per_message=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  START / STOP ADS
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def start_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start advertising."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    result = await start_broadcast(user_id)

    if result["success"]:
        user = await get_user(user_id)
        accounts = await get_user_accounts(user_id)
        groups = await get_group_count(user_id)
        active = sum(1 for a in accounts if a.get("status") == "active")
        await log_ads_started(user_id, active, groups, user.get("interval_seconds", 1200))
        await _send_menu(update, context, messages.ads_started_text(), keyboards.back_keyboard("dashboard"))
    else:
        await _send_menu(update, context, messages.error_text(result["error"]), keyboards.back_keyboard("dashboard"))


@require_join
async def view_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Preview the current ad creative."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)

    msg = user.get("ad_message")
    media_type = user.get("ad_media_type")
    media_id = user.get("ad_media_file_id")

    if not msg and not media_id:
        await _send_menu(
            update, context,
            "<b>K U R U P  A D S</b>\n"
            "────────────────────────\n"
            "<b>NO AD CREATIVE</b>\n"
            "\n"
            "You haven't set an ad yet.\n"
            "────────────────────────",
            keyboards.back_keyboard("dashboard")
        )
        return

    # Send the ad as a preview
    if media_type == "photo" and media_id:
        await update.effective_chat.send_photo(
            photo=media_id,
            caption=f"<b>AD PREVIEW</b>\n────────────────────────\n\n{msg}",
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("dashboard")
        )
    elif media_type == "video" and media_id:
        await update.effective_chat.send_video(
            video=media_id,
            caption=f"<b>AD PREVIEW</b>\n────────────────────────\n\n{msg}",
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("dashboard")
        )
    else:
        await _send_menu(
            update, context,
            f"<b>AD PREVIEW</b>\n────────────────────────\n\n{msg}",
            keyboards.back_keyboard("dashboard")
        )


@require_join
async def stop_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop advertising."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    await stop_broadcast(user_id)
    await log_ads_stopped(user_id)
    await _send_menu(update, context, messages.ads_stopped_text(), keyboards.back_keyboard("dashboard"))
