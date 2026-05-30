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

from app.database.models import (
    get_user, set_session, clear_session, set_broadcasting,
    update_user_api_credentials, clear_user_api_credentials
)
from app.services.encryption_service import encrypt_session
from app.services.telethon_service import send_login_code, verify_code, verify_2fa
from app.services.channel_logger import log_account_connected, log_account_disconnected
from app.services import engine
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join


logger = logging.getLogger(__name__)

# Conversation states
PHONE, OTP, PASSWORD_2FA = range(3)

# Custom API configuration states
WAITING_API_ID, WAITING_API_HASH = range(5, 7)



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

    user_id = update.effective_user.id
    result = await send_login_code(phone, user_id)


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

    # Check if Saved Messages has any valid messages
    has_saved_msgs = False
    try:
        if client and client.is_connected():
            msgs = await client.get_messages("me", limit=100)
            valid_msgs = [m for m in msgs if m.message or m.media]
            if valid_msgs:
                has_saved_msgs = True
    except Exception as e:
        logger.warning(f"Failed to check Saved Messages on login: {e}")

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

    # Check if user has groups, start autonomous broadcasting
    user = await get_user(user_id)
    if user and user.get("groups"):
        await engine.start(user_id)

    await update.message.reply_text(
        messages.account_connected_text(phone_masked, has_saved_messages=has_saved_msgs),
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
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  CUSTOM API KEY ASSIGNMENT
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def setup_custom_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the custom API settings screen."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await get_user(user_id)
    if not user:
        return

    api_id = user.get("custom_api_id")
    api_hash = user.get("custom_api_hash")
    has_custom = api_id is not None and api_hash is not None

    text = messages.custom_api_menu_text(has_custom, api_id, api_hash)
    await _send_menu(update, context, text, keyboards.custom_api_keyboard(has_custom))


@require_join
async def clear_custom_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear custom API credentials and show status."""
    query = update.callback_query
    await query.answer("Clearing custom API credentials...")
    user_id = query.from_user.id

    await clear_user_api_credentials(user_id)

    # Re-render custom API settings screen showing cleared status
    text = messages.api_credentials_cleared_text()
    await _send_menu(update, context, text, keyboards.back_keyboard("view_account"))


@require_join
async def change_custom_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation entry point: Prompt user for API ID."""
    query = update.callback_query
    await query.answer()

    await _send_menu(
        update, context,
        messages.prompt_custom_api_id_text(),
        keyboards.cancel_keyboard(),
    )
    return WAITING_API_ID


async def receive_custom_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and validate API ID."""
    text = update.message.text.strip()

    try:
        api_id = int(text)
        if api_id <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            messages.error_text("Invalid API ID. It must be a positive integer. Please try again:"),
            parse_mode="HTML",
            reply_markup=keyboards.cancel_keyboard(),
        )
        return WAITING_API_ID

    context.user_data["temp_custom_api_id"] = api_id

    await update.message.reply_text(
        messages.prompt_custom_api_hash_text(),
        parse_mode="HTML",
        reply_markup=keyboards.cancel_keyboard(),
    )
    return WAITING_API_HASH


async def receive_custom_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save API Hash."""
    text = update.message.text.strip()

    # Telethon API hash is normally a 32-character hexadecimal string. Let's validate.
    if len(text) != 32 or not text.isalnum():
        await update.message.reply_text(
            messages.error_text("Invalid API Hash format. It should be a 32-character alphanumeric hash. Please check and send again:"),
            parse_mode="HTML",
            reply_markup=keyboards.cancel_keyboard(),
        )
        return WAITING_API_HASH

    user_id = update.effective_user.id
    api_id = context.user_data.pop("temp_custom_api_id", None)

    if not api_id:
        await update.message.reply_text(
            messages.error_text("Session expired. Please restart the custom API configuration."),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("view_account"),
        )
        return ConversationHandler.END

    # Save to database
    await update_user_api_credentials(user_id, api_id, text)

    await update.message.reply_text(
        messages.api_credentials_saved_text(),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("view_account"),
    )
    return ConversationHandler.END


async def cancel_custom_api_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel custom API configuration."""
    query = update.callback_query
    await query.answer()

    context.user_data.pop("temp_custom_api_id", None)

    await _send_menu(
        update, context,
        messages.success_text("Custom API configuration cancelled."),
        keyboards.back_keyboard("view_account"),
    )
    return ConversationHandler.END


def build_custom_api_conversation() -> ConversationHandler:
    """Build the ConversationHandler for custom API ID/Hash configuration."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(change_custom_api_callback, pattern="^change_custom_api$"),
        ],
        states={
            WAITING_API_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_api_id),
            ],
            WAITING_API_HASH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_api_hash),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_custom_api_conversation, pattern="^cancel_conv$"),
            CallbackQueryHandler(cancel_custom_api_conversation, pattern="^dashboard$"),
            CallbackQueryHandler(cancel_custom_api_conversation, pattern="^home$"),
            CallbackQueryHandler(cancel_custom_api_conversation, pattern="^view_account$"),
        ],
        per_user=True,
        per_chat=True,
    )

