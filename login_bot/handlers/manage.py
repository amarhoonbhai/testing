"""
Account management handlers for Login Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes
from models.session import get_all_user_sessions, disconnect_session
from login_bot.utils.keyboards import (
    get_manage_accounts_keyboard,
    get_account_options_keyboard,
    get_disconnect_confirm_keyboard,
    get_login_welcome_keyboard,
)


async def manage_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all accounts for the user."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    accounts = await get_all_user_sessions(user_id)

    if not accounts:
        text = (
            "📭 *No Accounts Connected*\n\n"
            "You haven't linked any Telegram accounts yet\\.\n\n"
            "Tap *➕ Add Account* to get started\\!"
        )
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=get_manage_accounts_keyboard([]),
        )
        return

    total = len(accounts)
    active = sum(1 for a in accounts if a.get("connected"))
    paused = sum(1 for a in accounts if a.get("paused_until"))

    text = (
        f"📱 *Connected Accounts \\({total}\\)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Active: `{active}` │ ⏸️ Paused: `{paused}`\n\n"
        f"_Tap an account to view options or disconnect it\\._"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_manage_accounts_keyboard(accounts),
    )


async def manage_acc_details_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show options for a specific account."""
    query = update.callback_query
    await query.answer()

    phone = query.data.split(":")[1]

    text = (
        f"🔧 *Manage Account*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 Number: `{phone}`\n\n"
        f"_Choose an action for this account:_"
    )
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_account_options_keyboard(phone),
    )


async def disconnect_acc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for confirmation to disconnect."""
    query = update.callback_query
    await query.answer()

    phone = query.data.split(":")[1]

    text = (
        f"⚠️ *Confirm Disconnection*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 Account: `{phone}`\n\n"
        f"This will *stop all active forwarding jobs* for this account\\.\n"
        f"Are you sure you want to proceed?"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=get_disconnect_confirm_keyboard(phone),
    )


async def confirm_disconnect_acc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute disconnection."""
    query = update.callback_query
    user_id = update.effective_user.id
    phone = query.data.split(":")[1]

    await disconnect_session(user_id, phone)
    await query.answer("✅ Account Disconnected", show_alert=True)

    # Go back to updated account list
    await manage_accounts_callback(update, context)


async def login_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Back to home screen."""
    from login_bot.handlers.start import build_welcome_text
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "User"

    accounts = await get_all_user_sessions(user_id)
    acc_count = len(accounts)

    await query.edit_message_text(
        build_welcome_text(first_name, acc_count),
        parse_mode="MarkdownV2",
        reply_markup=get_login_welcome_keyboard(),
        disable_web_page_preview=True,
    )
