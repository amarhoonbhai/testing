"""
Accounts handler — Add, View, and Delete hosted Telegram accounts.

Uses ConversationHandler for the multi-step add-account flow.
Enforces name branding and bio on successful account connection.
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

from app.config import MAX_ACCOUNTS, ENFORCED_NAME, ENFORCED_BIO
from app.database.models import (
    get_user,
    get_user_accounts,
    get_account_count,
    add_account,
    delete_account,
    mask_phone,
)
from app.services.encryption_service import encrypt_session
from app.services.telethon_service import send_login_code, verify_code, verify_2fa
from app.services.branding_service import enforce_branding
from app.services.channel_logger import log_account_added, log_account_deleted
from app.bot import messages, keyboards
from app.bot.handlers.start import _send_menu, require_join

logger = logging.getLogger(__name__)

# Conversation states
PHONE, OTP, PASSWORD_2FA = range(3)


# ═══════════════════════════════════════════════════════════════════════════════
#  ADD ACCOUNT FLOW
# ═══════════════════════════════════════════════════════════════════════════════

async def add_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: ask for phone number."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    count = await get_account_count(user_id)

    if count >= MAX_ACCOUNTS:
        await _send_menu(
            update, context,
            messages.max_accounts_text(MAX_ACCOUNTS),
            keyboards.back_keyboard("dashboard"),
        )
        return ConversationHandler.END

    await _send_menu(
        update, context,
        messages.add_account_text(),
        keyboards.cancel_keyboard(),
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive phone number, send login code."""
    phone = update.message.text.strip()

    # Basic validation
    if not phone.startswith("+") or len(phone) < 8:
        await update.message.reply_text(
            "⌞_⌝ Invalid format. Please enter with country code:\n"
            "<code>Example: +1234567890</code>",
            parse_mode="HTML",
        )
        return PHONE

    await update.message.reply_text(
        "⌞_⌝ Sending login code... ⏳",
        parse_mode="HTML",
    )

    result = await send_login_code(phone)

    if not result["success"]:
        await update.message.reply_text(
            messages.error_text(result["error"]),
            parse_mode="HTML",
            reply_markup=keyboards.back_keyboard("dashboard"),
        )
        return ConversationHandler.END

    # Store data in context for next step
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

    # Delete the OTP message for security
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
        return OTP  # Let them retry

    # Success — save account
    await _save_account(update, context, phone, result["session_string"], client)
    return ConversationHandler.END


async def receive_2fa_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive 2FA password, complete login."""
    password = update.message.text.strip()
    client = context.user_data.get("login_client")
    phone = context.user_data.get("login_phone")

    # Delete the password message for security
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
        return PASSWORD_2FA  # Let them retry

    # Success — save account
    await _save_account(update, context, phone, result["session_string"], client)
    return ConversationHandler.END


async def _save_account(update, context, phone, session_string, client):
    """Encrypt session, save to DB, enforce branding, notify user."""
    user_id = update.effective_user.id
    phone_masked = mask_phone(phone)

    # Encrypt and store
    encrypted = encrypt_session(session_string)
    await add_account(user_id, phone, phone_masked, encrypted)

    # Enforce branding (name + bio) on the connected account
    try:
        await enforce_branding(client, update.effective_user.first_name or "")
        logger.info(f"Branding enforced on newly connected account")
    except Exception:
        logger.warning("Failed to enforce branding on new account")

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
    await log_account_added(user_id, phone_masked)

    await update.message.reply_text(
        messages.account_added_text(phone_masked),
        parse_mode="HTML",
        reply_markup=keyboards.back_keyboard("dashboard"),
    )


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add-account conversation."""
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
        "<b>K U R U P  A D S</b>\n"
        "────────────────────────\n"
        "<b>TERMINATED</b>\n"
        "\n"
        "The operation has been cancelled.\n"
        "Returning to Command Center.\n"
        "────────────────────────",
        keyboards.back_keyboard("dashboard"),
    )
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════════
#  MY ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def my_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of hosted accounts."""
    user_id = update.effective_user.id
    accounts = await get_user_accounts(user_id)

    if not accounts:
        await _send_menu(
            update, context,
            messages.no_accounts_text(),
            keyboards.no_accounts_keyboard(),
        )
        return

    await _send_menu(
        update, context,
        messages.accounts_list_text(accounts),
        keyboards.accounts_list_keyboard(accounts),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  DELETE ACCOUNTS
# ═══════════════════════════════════════════════════════════════════════════════

@require_join
async def delete_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show accounts available for deletion."""
    user_id = update.effective_user.id
    accounts = await get_user_accounts(user_id)

    if not accounts:
        await _send_menu(
            update, context,
            messages.no_accounts_text(),
            keyboards.no_accounts_keyboard(),
        )
        return

    await _send_menu(
        update, context,
        "<b>K U R U P  A D S</b>\n"
        "────────────────────────\n"
        "<b>REMOVE ASSET</b>\n"
        "\n"
        "Select the account to disconnect:\n"
        "────────────────────────",
        keyboards.delete_accounts_keyboard(accounts),
    )


@require_join
async def del_acc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account deletion selection — show confirmation."""
    query = update.callback_query
    await query.answer()

    phone_masked = query.data.split(":", 1)[1]

    await _send_menu(
        update, context,
        messages.delete_confirm_text(phone_masked),
        keyboards.confirm_delete_keyboard(phone_masked),
    )


async def confirm_del_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and execute account deletion."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    phone_masked = query.data.split(":", 1)[1]

    deleted = await delete_account(user_id, phone_masked)

    if deleted:
        await log_account_deleted(user_id, phone_masked)
        await _send_menu(
            update, context,
            messages.account_deleted_text(phone_masked),
            keyboards.back_keyboard("dashboard"),
        )
    else:
        await _send_menu(
            update, context,
            messages.error_text("Account not found or already deleted."),
            keyboards.back_keyboard("dashboard"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  CONVERSATION HANDLER BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_add_account_conversation() -> ConversationHandler:
    """Build the ConversationHandler for the add-account flow."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_account_callback, pattern="^add_account$"),
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
            CallbackQueryHandler(cancel_conversation, pattern="^my_accounts$"),
        ],
        per_user=True,
        per_chat=True,
        per_message=False,
    )
