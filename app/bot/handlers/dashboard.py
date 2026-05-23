"""
Dashboard handler — Executive Overview, Health Monitor, Auto Responder, Telemetry, Premium.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters,
)

from app.database.models import (
    get_user, update_user, add_keyword_rule, delete_keyword_rule,
)
from app.config import OWNER_ID, DEFAULT_INTERVAL
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join, end_conversation_callback
from app.services.encryption_service import decrypt_session
from app.services.telethon_service import get_client_from_session, check_account_health

logger = logging.getLogger(__name__)

WAITING_AR_MESSAGE = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the main executive dashboard."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    has_account = bool(user.get("session_encrypted")) if user else False
    group_count = len(user.get("groups", [])) if user else 0
    total_sent = user.get("total_sent", 0) if user else 0
    total_failed = user.get("total_failed", 0) if user else 0
    is_broadcasting = user.get("is_broadcasting", False) if user else False
    interval = user.get("interval_seconds", DEFAULT_INTERVAL) if user else DEFAULT_INTERVAL
    phone_masked = user.get("phone_masked") if user else None
    is_premium = user.get("is_premium", False) if user else False
    health_status = user.get("health_status", "Not Checked") if user else "Not Checked"
    sleep_enabled = user.get("sleep_mode_enabled", True) if user else True
    sleep_start = user.get("sleep_mode_start_hour", 0) if user else 0
    sleep_end = user.get("sleep_mode_end_hour", 5) if user else 5

    is_owner = (user_id == OWNER_ID)

    text = messages.dashboard_text(
        has_account=has_account,
        group_count=group_count,
        total_sent=total_sent,
        total_failed=total_failed,
        is_broadcasting=is_broadcasting,
        interval=interval,
        phone_masked=phone_masked,
        is_premium=is_premium,
        health_status=health_status,
        sleep_enabled=sleep_enabled,
        sleep_start_hour=sleep_start,
        sleep_end_hour=sleep_end,
    )

    markup = keyboards.dashboard_keyboard(
        is_broadcasting=is_broadcasting,
        has_account=has_account,
        is_owner=is_owner,
    )

    await _send_menu(update, context, text, markup)


# ═══════════════════════════════════════════════════════════════════════════════
#  HEALTH MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def health_monitor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perform deep account health evaluation and display report."""
    query = update.callback_query
    await query.answer("Evaluating account health...")
    user_id = query.from_user.id

    user = await get_user(user_id)
    if not user or not user.get("session_encrypted"):
        await _send_menu(
            update, context,
            messages.error_text("You must connect your Telegram account first to evaluate health standing."),
            keyboards.back_keyboard("dashboard")
        )
        return

    client = None
    try:
        session = decrypt_session(user["session_encrypted"])
        client = await get_client_from_session(session, user_id)
        
        report = await check_account_health(user_id, client)
        
        text = messages.health_monitor_text(
            score=report["score"],
            status=report["status"],
            details=report["details"],
        )
        await _send_menu(update, context, text, keyboards.health_monitor_keyboard())

    except Exception as e:
        logger.error(f"Health monitor failed: {e}")
        await _send_menu(
            update, context,
            messages.error_text(f"Health evaluation failed: {type(e).__name__}"),
            keyboards.back_keyboard("dashboard")
        )
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
#  SMART AUTO RESPONDER
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View auto-responder settings."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    enabled = user.get("auto_responder_enabled", False) if user else False
    msg = user.get("auto_responder_message", "Hello! I am currently busy.") if user else "Hello! I am currently busy."
    rules = user.get("auto_responder_rules", {}) if user else {}

    text = messages.auto_responder_text(enabled, msg, rules)
    await _send_menu(update, context, text, keyboards.auto_responder_keyboard(enabled, rules))


@require_join
async def toggle_auto_responder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto responder on/off."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    enabled = not user.get("auto_responder_enabled", False) if user else True
    await update_user(user_id, auto_responder_enabled=enabled)

    await auto_responder_callback(update, context)


@require_join
async def toggle_rule_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle rule: respond only during broadcast."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    rules = user.get("auto_responder_rules", {}) if user else {}
    rules["only_during_broadcast"] = not rules.get("only_during_broadcast", True)
    await update_user(user_id, auto_responder_rules=rules)

    await auto_responder_callback(update, context)


@require_join
async def toggle_rule_contacts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle rule: exclude known contacts."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user = await get_user(user_id)
    rules = user.get("auto_responder_rules", {}) if user else {}
    rules["exclude_contacts"] = not rules.get("exclude_contacts", True)
    await update_user(user_id, auto_responder_rules=rules)

    await auto_responder_callback(update, context)


@require_join
async def set_auto_responder_prompt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for new auto-responder reply message."""
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        messages.auto_responder_prompt_text(),
        keyboards.cancel_keyboard()
    )
    return WAITING_AR_MESSAGE


async def receive_auto_responder_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save auto-responder message."""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    await update_user(user_id, auto_responder_message=text)

    await update.message.reply_text(
        messages.auto_responder_saved_text(),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("auto_responder"),
    )
    return ConversationHandler.END


def build_auto_responder_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_auto_responder_prompt_callback, pattern="^set_auto_responder_message$"),
        ],
        states={
            WAITING_AR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_auto_responder_message),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(end_conversation_callback, pattern="^cancel_conv$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^dashboard$"),
        ],
        per_user=True, per_chat=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  LIVE STATS & PREMIUM
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def live_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View real-time user telemetry."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user:
        return

    from app.config import MAX_FAIL_SKIP
    groups = user.get("groups", [])
    group_fails = user.get("group_fails", {})
    live_count = sum(1 for g in groups if group_fails.get(g.replace(".", "_DOT_").replace("$", "_DOLLAR_"), 0) < MAX_FAIL_SKIP)
    paused_count = len(groups) - live_count

    text = messages.live_stats_text(user, live_count, paused_count)
    await _send_menu(update, context, text, keyboards.live_stats_keyboard())


@require_join
async def premium_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View premium membership info."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)

    is_premium = user.get("is_premium", False) if user else False
    text = messages.premium_info_text(is_premium)
    await _send_menu(update, context, text, keyboards.premium_info_keyboard(is_premium))


@require_join
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command by displaying live stats."""
    await live_stats_callback(update, context)


# ── Advanced Enhancements ───────────────────────────────────────────────────

@require_join
async def view_activity_logs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View recent broadcaster activity logs."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)
    logs = user.get("activity_logs", []) if user else []
    
    text = messages.activity_logs_text(logs)
    await _send_menu(update, context, text, keyboards.back_keyboard("live_stats"))


@require_join
async def quiet_hours_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View quiet hours settings."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    enabled = user.get("sleep_mode_enabled", True) if user else True
    start_h = user.get("sleep_mode_start_hour", 0) if user else 0
    end_h = user.get("sleep_mode_end_hour", 5) if user else 5
    
    text = messages.quiet_hours_menu_text(enabled, start_h, end_h)
    await _send_menu(update, context, text, keyboards.quiet_hours_keyboard(enabled))


@require_join
async def toggle_sleep_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle sleep mode on/off."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user = await get_user(user_id)
    enabled = not user.get("sleep_mode_enabled", True) if user else False
    await update_user(user_id, sleep_mode_enabled=enabled)
    
    await quiet_hours_menu_callback(update, context)


@require_join
async def set_responder_cooldown_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View responder cooldown selection preset menu."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)
    
    current_cooldown = user.get("auto_responder_cooldown_seconds", 21600) if user else 21600
    text = messages.responder_cooldown_text(current_cooldown)
    await _send_menu(update, context, text, keyboards.cooldown_settings_keyboard(current_cooldown))


@require_join
async def save_responder_cooldown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the selected responder cooldown preset."""
    query = update.callback_query
    val = int(query.data.split("_")[-1])
    await query.answer("Cooldown updated successfully.")
    user_id = query.from_user.id
    
    await update_user(user_id, auto_responder_cooldown_seconds=val)
    await auto_responder_callback(update, context)


@require_join
async def manage_keywords_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View auto-reply keyword rules list."""
    query = update.callback_query
    if query:
        await query.answer()
    user_id = update.effective_user.id
    user = await get_user(user_id)
    keywords = user.get("auto_responder_keywords", {}) if user else {}
    
    text = messages.keyword_rules_text(keywords)
    await _send_menu(update, context, text, keyboards.keyword_rules_keyboard(keywords))


@require_join
async def delete_keyword_rule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a keyword rule."""
    query = update.callback_query
    keyword = query.data.replace("del_keyword_", "").strip()
    await query.answer(f"Deleted rule for '{keyword}'")
    user_id = query.from_user.id
    
    await delete_keyword_rule(user_id, keyword)
    await manage_keywords_callback(update, context)


# ── Conversation Handlers for Text Configuration Inputs ───────────────────────

WAITING_SLEEP_START = 1
WAITING_SLEEP_END = 2
WAITING_KEYWORD = 3
WAITING_KEYWORD_REPLY = 4


@require_join
async def set_sleep_start_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        "🌅 <b>Set Sleep Start Hour</b>\n\nEnter the hour when Sleep Mode should begin (0 to 23).\n\n• <i>0 = Midnight, 12 = Noon, 23 = 11 PM</i>",
        keyboards.cancel_keyboard()
    )
    return WAITING_SLEEP_START


async def receive_sleep_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        val = int(text)
        if not (0 <= val <= 23):
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid hour between 0 and 23.")
        return WAITING_SLEEP_START

    context.user_data["temp_sleep_start"] = val
    
    await update.message.reply_text(
        "🌄 <b>Set Sleep End Hour</b>\n\nEnter the hour when Sleep Mode should end (0 to 23).\n\n• <i>e.g., 5 for 5:00 AM</i>",
        parse_mode="HTML",
        reply_markup=keyboards.cancel_keyboard()
    )
    return WAITING_SLEEP_END


async def receive_sleep_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        val = int(text)
        if not (0 <= val <= 23):
            raise ValueError()
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid hour between 0 and 23.")
        return WAITING_SLEEP_END

    start_h = context.user_data.pop("temp_sleep_start", 0)
    end_h = val

    await update_user(user_id, sleep_mode_start_hour=start_h, sleep_mode_end_hour=end_h)

    def format_h(h: int) -> str:
        if h == 0:
            return "12:00 AM"
        elif h == 12:
            return "12:00 PM"
        elif h < 12:
            return f"{h}:00 AM"
        else:
            return f"{h-12}:00 PM"

    await update.message.reply_text(
        f"✅ <b>Quiet Hours Configured</b>\n\nBroadcasting will now rest between <b>{format_h(start_h)}</b> and <b>{format_h(end_h)}</b>.",
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("quiet_hours_menu")
    )
    return ConversationHandler.END


@require_join
async def add_keyword_rule_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await _send_menu(
        update, context,
        "🔍 <b>Add Keyword Rule</b>\n\nEnter the keyword or phrase to match (case-insensitive).\n\n• <i>e.g., price</i>",
        keyboards.cancel_keyboard()
    )
    return WAITING_KEYWORD


async def receive_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if not text:
        await update.message.reply_text("⚠️ Keyword cannot be empty. Please enter a valid keyword.")
        return WAITING_KEYWORD
    
    context.user_data["temp_keyword"] = text
    
    await update.message.reply_text(
        "📝 <b>Set Keyword Reply Message</b>\n\nEnter the message the bot should reply with when this keyword is detected.",
        parse_mode="HTML",
        reply_markup=keyboards.cancel_keyboard()
    )
    return WAITING_KEYWORD_REPLY


async def receive_keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reply_msg = update.message.text.strip()
    
    keyword = context.user_data.pop("temp_keyword", None)
    if not keyword:
        await update.message.reply_text("⚠️ Something went wrong. Restarting operation.")
        return ConversationHandler.END

    await add_keyword_rule(user_id, keyword, reply_msg)
    
    await update.message.reply_text(
        f"✅ <b>Keyword Rule Added</b>\n\nKeyword: <code>{keyword}</code>\nReply: <i>{reply_msg[:40]}...</i>",
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("manage_keywords")
    )
    return ConversationHandler.END


def build_sleep_settings_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_sleep_start_prompt, pattern="^set_sleep_start$"),
            CallbackQueryHandler(set_sleep_start_prompt, pattern="^set_sleep_end$"),
        ],
        states={
            WAITING_SLEEP_START: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_sleep_start),
            ],
            WAITING_SLEEP_END: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_sleep_end),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(end_conversation_callback, pattern="^cancel_conv$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^dashboard$"),
        ],
        per_user=True, per_chat=True,
    )


def build_keyword_rules_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_keyword_rule_prompt, pattern="^add_keyword_rule$"),
        ],
        states={
            WAITING_KEYWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_keyword),
            ],
            WAITING_KEYWORD_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_keyword_reply),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(end_conversation_callback, pattern="^cancel_conv$"),
            CallbackQueryHandler(end_conversation_callback, pattern="^dashboard$"),
        ],
        per_user=True, per_chat=True,
    )

