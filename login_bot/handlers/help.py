"""
Help command handler for Login Bot.
Shows all available commands and features.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.config import MAIN_BOT_USERNAME, LOGIN_BOT_USERNAME


HELP_TEXT = """
╔══════════════════════════════╗
║   🔐  KURUP ADS LOGIN BOT   ║
╚══════════════════════════════╝

📋 *AVAILABLE COMMANDS*

┌─────────────────────────────
│ 🚀 */start*  —  Open home portal
│    Welcome screen + account status
│
│ ❓ */help*  —  Show this menu
│    All commands & feature guide
│
│ ℹ️ */status*  —  Your account info
│    View connected sessions count
│
│ ❌ */cancel*  —  Cancel current flow
│    Abort ongoing login process
└─────────────────────────────

🎛 *INLINE BUTTONS (from /start)*

┌─────────────────────────────
│ ➕ *Add Account / Connect*
│    Link a new Telegram account via
│    API ID → API Hash → Phone → OTP
│
│ 📱 *Manage Connected Accounts*
│    View, refresh, or disconnect
│    any of your linked sessions
│
│ 🔙 *Back to Main Bot*
│    Returns to @{main_bot}
└─────────────────────────────

🔐 *LOGIN FLOW STEPS*

  1️⃣  Enter your *API ID*
       (from [my.telegram.org](https://my.telegram.org))
  2️⃣  Enter your *API Hash*
  3️⃣  Enter your *Phone Number*
       (with country code, e.g. `+91XXXXXXXXXX`)
  4️⃣  Enter the *OTP* sent to Telegram
  5️⃣  Enter *2FA Password* if required

🛡 *SECURITY NOTE*
  ✅ Official Telegram API used
  ✅ Sessions encrypted with AES-256
  ✅ Your data is fully under your control
  ✅ 2FA passwords are never stored

💡 *TIPS*
  • Use */cancel* anytime to abort login
  • You can connect multiple accounts
  • Sessions carry over to the main scheduler

📡 *Support:* @PhiloBots
""".format(main_bot=MAIN_BOT_USERNAME)


def get_help_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🚀 Open Portal", callback_data="login_home"),
            InlineKeyboardButton("➕ Add Account", callback_data="add_account"),
        ],
        [
            InlineKeyboardButton("📱 My Accounts", callback_data="manage_accounts"),
        ],
        [
            InlineKeyboardButton("🤖 Main Bot", url=f"https://t.me/{MAIN_BOT_USERNAME}"),
            InlineKeyboardButton("📡 Support", url="https://t.me/PhiloBots"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - shows all commands and features."""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=get_help_keyboard(),
        disable_web_page_preview=True,
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the inline ❓ Help & Commands button (show_help callback)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        HELP_TEXT,
        parse_mode="Markdown",
        reply_markup=get_help_keyboard(),
        disable_web_page_preview=True,
    )
