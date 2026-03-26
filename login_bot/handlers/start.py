"""
Start and welcome handler for Login Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes

from models.user import upsert_user as create_user
from models.session import get_all_user_sessions
from login_bot.utils.keyboards import get_login_welcome_keyboard


WELCOME_TEXT = """
🔐 *KURUP ADS — SECURE LOGIN*

*★ PRO ACCOUNT PORTAL ★*

Welcome to the official account connection portal for *KURUP ADS* Group Message Scheduler.

🛡️ *YOUR SECURITY IS OUR PRIORITY*
✅ Official Telegram API used
✅ Sessions encrypted using AES-256
✅ Complete control over your data

To connect your account, you will need:
1️⃣ Your **API ID** & **API Hash** (from [my.telegram.org](https://my.telegram.org))
2️⃣ Your **Phone Number**
3️⃣ The **OTP** sent to your Telegram
4️⃣ Your **2FA Password** (if enabled)

👇 *Tap below to start the connection process*
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - shows welcome and account status."""
    user = update.effective_user
    user_id = user.id
    
    # Ensure user exists in db
    await create_user(user_id)
    
    # Get account stats
    accounts = await get_all_user_sessions(user_id)
    acc_count = len(accounts)
    
    first_name = user.first_name or "User"
    greeting = f"👋 *Greeting {first_name},*\n\n"
    
    # Dynamic status line
    if acc_count > 0:
        status_line = f"📱 *STATUS:* You have `{acc_count}` account(s) connected.\n\n"
    else:
        status_line = "⚪ *STATUS:* No accounts connected yet.\n\n"
    
    await update.message.reply_text(
        greeting + status_line + WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=get_login_welcome_keyboard(),
    )
