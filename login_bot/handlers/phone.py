"""
Phone number input handler for Login Bot.
Uses per-user API credentials collected during login.
"""

import re
from html import escape
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from login_bot.utils.keyboards import get_phone_input_keyboard, get_confirm_phone_keyboard, get_cancel_keyboard, get_api_input_keyboard

async def add_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add account flow - ask for API ID first."""
    from login_bot.handlers.login import WAITING_API_ID
    query = update.callback_query
    await query.answer()
    
    text = """
⚙️ <b>Step 1: Enter Telegram API ID</b>

Please enter your <b>API ID</b> from <a href="https://my.telegram.org">my.telegram.org</a>.
It should be a numeric value.
"""
    
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_api_input_keyboard(),
        disable_web_page_preview=True
    )
    
    return WAITING_API_ID


async def receive_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process received API ID."""
    from login_bot.handlers.login import WAITING_API_HASH, WAITING_API_ID
    
    api_id_text = update.message.text.strip()
    
    if not api_id_text.isdigit():
        await update.message.reply_text(
            "❌ <b>Invalid API ID</b>\n\nAPI ID must be a number. Please enter it again:",
            parse_mode="HTML",
            reply_markup=get_api_input_keyboard()
        )
        return WAITING_API_ID

    context.user_data["api_id"] = int(api_id_text)

    text = """
🔑 <b>Step 2: Enter Telegram API Hash</b>

Now please enter your <b>API Hash</b> from <a href="https://my.telegram.org">my.telegram.org</a>.
"""
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_api_input_keyboard()
    )
    return WAITING_API_HASH


async def receive_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process received API Hash."""
    from login_bot.handlers.login import WAITING_PHONE, WAITING_API_HASH
    
    api_hash = update.message.text.strip()
    
    if len(api_hash) < 10: # Basic validation
        await update.message.reply_text(
            "❌ <b>Invalid API Hash</b>\n\nPlease enter a valid API Hash:",
            parse_mode="HTML",
            reply_markup=get_api_input_keyboard()
        )
        return WAITING_API_HASH

    context.user_data["api_hash"] = api_hash

    text = """
📱 <b>Step 3: Enter Phone Number</b>

Finally, enter your phone number with country code.
Example: <code>+91XXXXXXXXXX</code>
"""
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_phone_input_keyboard()
    )
    return WAITING_PHONE


async def receive_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process received phone number."""
    from login_bot.handlers.login import CONFIRM_PHONE, WAITING_PHONE
    
    phone = update.message.text.strip()
    
    # Validate phone number
    if not phone.startswith("+"):
        await update.message.reply_text(
            "❌ Phone number must start with + (country code)\n\n"
            "Example: <code>+91XXXXXXXXXX</code>",
            parse_mode="HTML",
            reply_markup=get_phone_input_keyboard(),
        )
        return WAITING_PHONE
    
    # Remove spaces and dashes
    phone = re.sub(r"[\s\-]", "", phone)
    
    # Check if it contains only digits after +
    if not re.match(r"^\+\d{10,15}$", phone):
        await update.message.reply_text(
            "❌ Invalid phone number format.\n\n"
            "Please enter a valid phone number with country code.\n"
            "Example: <code>+91XXXXXXXXXX</code>",
            parse_mode="HTML",
            reply_markup=get_phone_input_keyboard(),
        )
        return WAITING_PHONE
    
    # Store phone and ask for confirmation
    context.user_data["phone"] = phone
    safe_phone = escape(phone)
    
    text = f"""
✅ <b>Confirm Your Details:</b>

📱 Phone: <code>{safe_phone}</code>

Send OTP now?
"""
    
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_confirm_phone_keyboard(),
    )
    return CONFIRM_PHONE


async def edit_phone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to phone input."""
    from login_bot.handlers.login import WAITING_PHONE
    query = update.callback_query
    await query.answer()
    
    text = """
📱 <b>Enter your phone number with country code:</b>

Example: <code>+91XXXXXXXXXX</code>

Make sure to include the + sign and country code.
"""
    
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_phone_input_keyboard(),
    )
    
    return WAITING_PHONE


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the login process."""
    query = update.callback_query or update.message
    if update.callback_query:
        await query.answer()
    
    # Clear user data
    context.user_data.clear()
    
    text = "❌ <b>Login Cancelled</b>\n\nYou can try again anytime."
    
    if update.callback_query:
        await query.edit_message_text(text, parse_mode="HTML")
    else:
        await query.reply_text(text, parse_mode="HTML")
    
    return ConversationHandler.END
