"""
Two-Factor Authentication handler for Login Bot.
Uses per-user API credentials collected during login.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telethon.errors import PasswordHashInvalidError, FloodWaitError


from html import escape

async def receive_2fa_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process 2FA password input."""
    from login_bot.handlers.login import WAITING_2FA
    
    user_id = update.effective_user.id
    password = update.message.text.strip()
    
    login_data = _login_clients.get(user_id)
    
    if not login_data:
        await update.message.reply_text(
            "❌ <b>Session expired.</b> Please start over.",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )
        return ConversationHandler.END
    
    client = login_data["client"]
    phone = login_data["phone"]
    
    # Delete the password message for security
    try:
        await update.message.delete()
    except Exception:
        pass
    
    # Send verifying message
    verifying_msg = await update.effective_chat.send_message("🔄 Verifying password...")
    
    try:
        # Sign in with password
        await client.sign_in(password=password)
        
        # Success! Get session string
        session_string = client.session.save()
        
        # Get API credentials from context
        api_id = context.user_data.get("api_id")
        api_hash = context.user_data.get("api_hash")
        
        # Save to database WITH per-user API credentials
        await create_user(user_id)
        await create_session(user_id, phone, session_string, api_id, api_hash)
        
        # Disconnect client
        await client.disconnect()
        
        # Clean up
        if user_id in _login_clients:
            del _login_clients[user_id]
        
        context.user_data.clear()
        
        # Fetch the user's current branding status
        from models.user import is_user_branded
        from core.utils import build_connection_success_text
        is_branded = await is_user_branded(user_id)
        text = build_connection_success_text(phone, is_branded)
        
        await verifying_msg.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_success_keyboard(),
        )
        return ConversationHandler.END
        
    except PasswordHashInvalidError:
        await verifying_msg.edit_text(
            "❌ <b>Invalid Password</b>\n\n"
            "The 2FA password is incorrect. Please try again.",
            parse_mode="HTML",
            reply_markup=get_2fa_keyboard(),
        )
        return WAITING_2FA
        
    except FloodWaitError as e:
        await verifying_msg.edit_text(
            f"⏳ <b>Too Many Attempts</b>\n\n"
            f"Please wait {e.seconds} seconds before trying again.",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )
        return WAITING_2FA
        
    except Exception as e:
        logger.error(f"2FA error: {e}")
        await verifying_msg.edit_text(
            f"❌ <b>Error</b>\n\n{escape(str(e))}",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )
        return WAITING_2FA
