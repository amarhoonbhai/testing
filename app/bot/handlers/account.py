"""
Account handler — Single Telegram account connection.

Connect, view, and disconnect a single Telethon account.
Uses ConversationHandler for the multi-step login flow.
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

from app.database.models import get_user, set_session, clear_session, set_broadcasting
from app.services.encryption_service import encrypt_session
from app.services.telethon_service import send_login_code, verify_code, verify_2fa
from app.services.channel_logger import log_account_connected, log_account_disconnected
from app.services import engine
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

# Conversation states
PHONE, OTP, PASSWORD_2FA = range(3)


def _mask_phone(phone: str) -> str:
    """Mask a phone number for display: +91xxxx1234."""
    if len(phone) < 6:
        return "***"
    return phone[:3] + "x" * (len(phone) - 7) + phone[-4:]


# ═══════════════════════════════════════════════════════════════════════════════
#  CONNECT ACCOUNT FLOW
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def connect_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: ask for phone number."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = await get_user(user_id)

    # Check if already connected
    if user and user.get("session_encrypted"):
        await _send_menu(
            update, context,
            messages.account_info_text(user.get("phone_masked", "Connected")),
            keyboards.account_info_keyboard(),
        )
        return ConversationHandler.END

    await _send_menu(
        update, context,
        messages.connect_account_text(),
        keyboards.cancel_keyboard(),
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive phone number, send login code."""
    phone = update.message.text.strip()

    if not phone.startswith("+") or len(phone) < 8:
        await update.message.reply_text(
            messages.error_text("Invalid format. Use: +1234567890"),
            parse_mode="HTML",
        )
        return PHONE

    await update.message.reply_text("⏳ Sending login code...", parse_mode="HTML")

    result = await send_login_code(phone)

    if not result["success"]:
        await update.message.reply_text(
            messages.error_text(result["error"]),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("dashboard"),
        )
        return ConversationHandler.END

    # Store data in context
    context.user_data["login_phone"] = phone
    context.user_data["login_client"] = result["client"]
    context.user_data["phone_code_hash"] = result["phone_code_hash"]

    await update.message.reply_text(
        messages.otp_prompt_text(),
        parse_mode="HTML",
        reply_markup=keyboards.cancel_keyboard(),
    )
    return OTP


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive OTP code, verify login."""
    code = update.message.text.strip()
    phone = context.user_data.get("login_phone")
    client = context.user_data.get("login_client")
    phone_code_hash = context.user_data.get("phone_code_hash")

    if not client or not phone:
        await update.message.reply_text(
            messages.error_text("Session expired. Please start over."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("dashboard"),
        )
        return ConversationHandler.END

    # Delete OTP message for security
    try:
        await update.message.delete()
    except Exception:
        pass

    result = await verify_code(client, phone, code, phone_code_hash)

    if result["needs_2fa"]:
        await update.message.reply_text(
            messages.password_2fa_text(),
            parse_mode="HTML",
            reply_markup=keyboards.cancel_keyboard(),
        )
        return PASSWORD_2FA

    if not result["success"]:
        await update.message.reply_text(
            messages.error_text(result["error"]),
            parse_mode="HTML",
            reply_markup=keyboards.cancel_keyboard(),
        )
        return OTP

    # Success — save account
    await _save_account(update, context, phone, result["session_string"], client)
    return ConversationHandler.END


async def receive_2fa_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive 2FA password, complete login."""
    password = update.message.text.strip()
    client = context.user_data.get("login_client")
    phone = context.user_data.get("login_phone")

    # Delete password for security
    try:
        await update.message.delete()
    except Exception:
        pass

    if not client or not phone:
        await update.message.reply_text(
            messages.error_text("Session expired. Please start over."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("dashboard"),
        )
        return ConversationHandler.END

    result = await verify_2fa(client, password)

    if not result["success"]:
        await update.message.reply_text(
            messages.error_text(result["error"]),
            parse_mode="HTML",
            reply_markup=keyboards.cancel_keyboard(),
        )
        return PASSWORD_2FA

    # Success — save account
    await _save_account(update, context, phone, result["session_string"], client)
    return ConversationHandler.END


async def _save_account(update, context, phone, session_string, client):
    """Encrypt session, save to DB, notify user."""
    user_id = update.effective_user.id
    phone_masked = _mask_phone(phone)

    # Encrypt and store
    encrypted = encrypt_session(session_string)
    await set_session(user_id, encrypted, phone_masked)

    # Disconnect the login client
    try:
        await client.disconnect()
    except Exception:
        pass

    # Clean up context
    context.user_data.pop("login_phone", None)
    context.user_data.pop("login_client", None)
    context.user_data.pop("phone_code_hash", None)

    # Log to channel
    await log_account_connected(user_id, phone_masked)

    await update.message.reply_text(
        messages.account_connected_text(phone_masked),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("dashboard"),
    )


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the connect-account conversation."""
    query = update.callback_query
    await query.answer()

    # Disconnect any pending client
    client = context.user_data.pop("login_client", None)
    if client:
        try:
            await client.disconnect()
        except Exception:
            pass

    context.user_data.pop("login_phone", None)
    context.user_data.pop("phone_code_hash", None)

    await _send_menu(
        update, context,
        messages.success_text("Operation cancelled."),
        keyboards.back_keyboard("dashboard"),
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
#  VIEW / DISCONNECT ACCOUNT
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def view_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show connected account info."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user or not user.get("session_encrypted"):
        await _send_menu(
            update, context,
            messages.no_account_text(),
            keyboards.no_account_keyboard(),
        )
        return

    await _send_menu(
        update, context,
        messages.account_info_text(user.get("phone_masked", "Connected")),
        keyboards.account_info_keyboard(),
    )


@require_join
async def disconnect_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm disconnect."""
    user_id = update.effective_user.id
    user = await get_user(user_id)

    if not user or not user.get("session_encrypted"):
        await _send_menu(
            update, context,
            messages.no_account_text(),
            keyboards.no_account_keyboard(),
        )
        return

    await _send_menu(
        update, context,
        messages.confirm_disconnect_text(user.get("phone_masked", "?")),
        keyboards.confirm_disconnect_keyboard(),
    )


@require_join
async def confirm_disconnect_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute account disconnect."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)

    phone = user.get("phone_masked", "?") if user else "?"

    # Stop broadcasting if active
    if engine.is_running(user_id):
        await engine.stop(user_id)

    await clear_session(user_id)
    await set_broadcasting(user_id, False)
    await log_account_disconnected(user_id, phone)

    await _send_menu(
        update, context,
        messages.account_disconnected_text(phone),
        keyboards.back_keyboard("dashboard"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  CONVERSATION HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

def build_account_conversation() -> ConversationHandler:
    """Build the ConversationHandler for account connection."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(connect_account_callback, pattern="^connect_account$"),
        ],
        states={
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone),
            ],
            OTP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp),
            ],
            PASSWORD_2FA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_2fa_password),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conversation, pattern="^cancel_conv$"),
            CallbackQueryHandler(cancel_conversation, pattern="^dashboard$"),
            CallbackQueryHandler(cancel_conversation, pattern="^home$"),
            CallbackQueryHandler(cancel_conversation, pattern="^view_account$"),
        ],
        per_user=True,
        per_chat=True,
        per_message=True,
    )
