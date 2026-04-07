"""
Unified Login Conversation Handler for Login Bot.
Combines phone, OTP, and 2FA states into a single flow.
"""

from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Import state-specific functions
from login_bot.handlers.phone import (
    add_account_callback,
    receive_api_id,
    receive_api_hash,
    receive_phone_number,
    edit_phone_callback,
    cancel_callback,
)
from login_bot.handlers.otp import (
    send_otp_callback,
    resend_otp_callback,
    otp_keypad_callback,
)
from login_bot.handlers.twofa import receive_2fa_password

# Define state constants (should match what's used in sub-handlers)
WAITING_API_ID = "waiting_api_id"
WAITING_API_HASH = "waiting_api_hash"
WAITING_PHONE = "waiting_phone"
CONFIRM_PHONE = "confirm_phone"
WAITING_OTP = "waiting_otp"
WAITING_2FA = "waiting_2fa"

login_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_account_callback, pattern="^add_account$")
    ],
    states={
        WAITING_API_ID: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_id)
        ],
        WAITING_API_HASH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_hash)
        ],
        WAITING_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone_number)
        ],
        CONFIRM_PHONE: [
            CallbackQueryHandler(send_otp_callback, pattern="^send_otp$"),
            CallbackQueryHandler(edit_phone_callback, pattern="^edit_phone$"),
        ],
        WAITING_OTP: [
            CallbackQueryHandler(otp_keypad_callback, pattern="^otp:"),
            CallbackQueryHandler(resend_otp_callback, pattern="^resend_otp$"),
        ],
        WAITING_2FA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_2fa_password)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
        # We can add a catch-all /cancel command too
        MessageHandler(filters.COMMAND, cancel_callback),
    ],
    per_user=True,
    per_chat=True,
)
