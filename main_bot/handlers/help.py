"""
Help & Guide handler for Main Bot — KURUP ADS.
"""

from telegram import Update
from telegram.ext import ContextTypes

from main_bot.utils.keyboards import get_back_home_keyboard, get_guide_keyboard


HELP_TEXT = """
📘 *HELP & COMMANDS — KURUP ADS*

🤖 *BOT COMMANDS*
🔹 `/start` — Return to home screen
🔹 `/dashboard` — Open your live dashboard
🔹 `/stats` — View your personal stats
🔹 `/redeem <code>` — Apply a premium promo code
🔹 `/help` — Show this menu

👨‍💻 *SUPPORT:* @spinify
"""


GUIDE_TEXT = """
📖 *BEGINNER'S GUIDE — KURUP ADS*
_Step-by-step to start auto-forwarding in 5 minutes_

━━━━━━━━━━━━━━━━━━━━━

*STEP 1 — Get Your API Keys*

1. Open [my.telegram.org](https://my.telegram.org) in a browser
2. Log in with your phone number
3. Go to *API Development Tools*
4. Create a new app (any name/description)
5. Copy your *API ID* and *API Hash*

━━━━━━━━━━━━━━━━━━━━━

*STEP 2 — Connect Your Account*

1. Tap *Add Account* on the home screen
2. You'll be sent to @kurupLoginBot
3. Enter your *API ID*, then *API Hash*
4. Enter your phone number with country code (e.g. `+91XXXXXXXXXX`)
5. Enter the OTP sent to your Telegram
6. Enter 2FA password if your account has it enabled

✅ Done! Your account is now connected.

━━━━━━━━━━━━━━━━━━━━━

*STEP 3 — Add Groups*

Go to your *Dashboard* → *Manage Groups* → *Add Group*
Enter the group link or username:
`https://t.me/yourgroupname` or `@yourgroupname`

You can add up to 10,000 groups!

━━━━━━━━━━━━━━━━━━━━━

*STEP 4 — Start Sending*

1. Open your *Saved Messages* (in Telegram)
2. Send any message you want to forward
3. KURUP ADS will automatically send it to all your groups!

━━━━━━━━━━━━━━━━━━━━━

*⚙️ SETTINGS YOU CAN CONFIGURE*

🔹 *Interval* — Time (in minutes) between each round of sends
🔹 *Send Mode* — Sequential / Rotate / Random
🔹 *Shuffle* — Randomize which group gets the message first
🔹 *Copy Mode* — Hide "Forwarded from" label
🔹 *Auto Responder* — Auto-reply to DMs

━━━━━━━━━━━━━━━━━━━━━

*🛡️ BUILT-IN SAFETY*

✅ 45-second gap between each group (Flood protection)
✅ Smart auto-pause from 12AM–6AM IST (Night Mode)
✅ Auto-removes invalid/banned groups
✅ Your API keys are never shared or stored in plain text

━━━━━━━━━━━━━━━━━━━━━

📩 *Need help? DM @spinify on Telegram.*
"""


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help screen."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=get_guide_keyboard(),
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=get_guide_keyboard(),
        disable_web_page_preview=True,
    )


async def guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show full beginner guide."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        GUIDE_TEXT,
        parse_mode="Markdown",
        reply_markup=get_back_home_keyboard(),
        disable_web_page_preview=True,
    )
