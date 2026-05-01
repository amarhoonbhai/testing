"""
Ads handler — Set Ad Message, Set Interval, Start/Stop Ads.
Uses ConversationHandler for multi-step flows.
Supports up to 3 ads.
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
    add_user_ad, delete_user_ad,
)
from app.services.broadcast_service import start_broadcast, stop_broadcast
from app.services.channel_logger import log_ads_started, log_ads_stopped
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

# Conversation states
WAITING_AD, WAITING_INTERVAL = range(2)


# ═══════════════════════════════════════════════════════════════════════════════
#  AD MANAGEMENT HUB
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def manage_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: Show ads management console."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)
    ads = user.get("ads", [])

    text = (
        f"<b>K U R U P  A D S</b>\n"
        f"────────────────────────\n"
        f"<b>AD CONSOLE</b>\n"
        f"\n"
        f"  Total Ads: {len(ads)} / 3\n"
        f"  Rotation: Sequential\n"
        f"\n"
        f"Manage your broadcast creatives below:\n"
        f"────────────────────────"
    )
    await _send_menu(update, context, text, keyboards.ads_list_keyboard(ads))


@require_join
async def view_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Preview a specific ad creative."""
    query = update.callback_query
    await query.answer()
    ad_id = query.data.split(":")[1]
    
    user_id = query.from_user.id
    user = await get_user(user_id)
    ads = user.get("ads", [])
    
    ad = next((a for a in ads if a["id"] == ad_id), None)
    if not ad:
        await query.message.reply_text("Ad not found.")
        return

    msg = ad.get("ad_message", "")
    mode = ad.get("ad_mode", "direct")
    media_type = ad.get("ad_media_type")
    media_id = ad.get("ad_media_file_id")
    forward_mid = ad.get("ad_forward_mid")

    caption = f"<b>AD PREVIEW ({mode.upper()})</b>\n────────────────────────\n\n{msg}"

    if mode == "forward" and forward_mid:
        from app.config import BOT_USERNAME
        # For preview, we just show text since we can't easily forward to user
        # without potentially violating privacy or needing session
        await update.effective_chat.send_message(
            f"<b>AD PREVIEW (FORWARD)</b>\n────────────────────────\n\n"
            f"<i>This message will be forwarded from your chat history.</i>\n\n"
            f"{msg}",
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("manage_ads")
        )
    elif media_type == "photo" and media_id:
        await update.effective_chat.send_photo(
            photo=media_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("manage_ads")
        )
    elif media_type == "video" and media_id:
        await update.effective_chat.send_video(
            video=media_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("manage_ads")
        )
    else:
        await update.effective_chat.send_message(
            caption,
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("manage_ads")
        )


@require_join
async def del_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm delete ad."""
    query = update.callback_query
    await query.answer()
    ad_id = query.data.split(":")[1]
    
    await _send_menu(
        update, context,
        "<b>K U R U P  A D S</b>\n"
        "────────────────────────\n"
        "<b>CONFIRM DELETION</b>\n"
        "\n"
        "Are you sure you want to remove this ad?\n"
        "────────────────────────",
        keyboards.confirm_delete_ad_keyboard(ad_id)
    )


async def confirm_del_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute ad deletion."""
    query = update.callback_query
    await query.answer()
    ad_id = query.data.split(":")[1]
    user_id = query.from_user.id
    
    await delete_user_ad(user_id, ad_id)
    await manage_ads_callback(update, context)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADD AD CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def add_ad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry: ask user for ad content."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = await get_user(user_id)
    if len(user.get("ads", [])) >= 3:
        await query.message.reply_text("Maximum limit of 3 ads reached.")
        return ConversationHandler.END

    await _send_menu(
        update, context,
        "<b>K U R U P  A D S</b>\n"
        "────────────────────────\n"
        "<b>NEW CREATIVE</b>\n"
        "\n"
        "Send your ad content. Supports:\n"
        "  ‣ Text\n"
        "  ‣ Photo + Caption\n"
        "  ‣ Video + Caption\n"
        "  ‣ Forwarded Message\n"
        "────────────────────────",
        keyboards.cancel_keyboard()
    )
    return WAITING_AD


async def receive_ad_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the ad message (text, photo, video, or forward)."""
    user_id = update.effective_user.id
    ad_data = {}

    if update.message.forward_date:
        ad_data["ad_mode"] = "forward"
        ad_data["ad_forward_cid"] = update.message.chat_id
        ad_data["ad_forward_mid"] = update.message.message_id
        ad_data["ad_message"] = update.message.text or update.message.caption or "Forwarded Content"
        ad_data["ad_media_type"] = None
        ad_data["ad_media_file_id"] = None
    elif update.message.photo:
        ad_data["ad_mode"] = "direct"
        ad_data["ad_media_type"] = "photo"
        ad_data["ad_media_file_id"] = update.message.photo[-1].file_id
        ad_data["ad_message"] = update.message.caption or ""
    elif update.message.video:
        ad_data["ad_mode"] = "direct"
        ad_data["ad_media_type"] = "video"
        ad_data["ad_media_file_id"] = update.message.video.file_id
        ad_data["ad_message"] = update.message.caption or ""
    elif update.message.text:
        ad_data["ad_mode"] = "direct"
        ad_data["ad_media_type"] = None
        ad_data["ad_media_file_id"] = None
        ad_data["ad_message"] = update.message.text
    else:
        await update.message.reply_text(
            messages.error_text("Unsupported format. Send text, photo, video, or forward a message."),
            parse_mode="HTML",
        )
        return WAITING_AD

    await add_user_ad(user_id, ad_data)
    await update.message.reply_text(
        "<b>✅ CREATIVE SAVED</b>\n"
        "────────────────────────\n"
        "Your ad has been added to the console.\n"
        "────────────────────────",
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("manage_ads"),
    )
    return ConversationHandler.END


def build_set_ad_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(add_ad_callback, pattern="^add_ad$")],
        states={
            WAITING_AD: [
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.VIDEO | filters.FORWARDED,
                    receive_ad_message,
                ),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancel_conv$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^dashboard$"),
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^manage_ads$"),
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
    
    user = await get_user(user_id)
    if not user.get("ads"):
        await query.message.reply_text("You haven't set any ads yet.")
        return

    result = await start_broadcast(user_id)

    if result["success"]:
        accounts = await get_user_accounts(user_id)
        groups = await get_group_count(user_id)
        active = sum(1 for a in accounts if a.get("status") == "active")
        await log_ads_started(user_id, active, groups, user.get("interval_seconds", 1200))
        await _send_menu(update, context, messages.ads_started_text(), keyboards.back_keyboard("dashboard"))
    else:
        await _send_menu(update, context, messages.error_text(result["error"]), keyboards.back_keyboard("dashboard"))


@require_join
async def stop_ads_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop advertising."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    await stop_broadcast(user_id)
    await log_ads_stopped(user_id)
    await _send_menu(update, context, messages.ads_stopped_text(), keyboards.back_keyboard("dashboard"))
