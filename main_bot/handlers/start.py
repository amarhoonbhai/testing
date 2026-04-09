"""
Start and welcome handler for Main Bot.
"""

from telegram import Update
from telegram.ext import ContextTypes

from core.config import REQUIRED_CHANNELS, CHANNEL_USERNAME
from models.user import create_user
from models.session import get_all_user_sessions
from main_bot.utils.keyboards import get_welcome_keyboard


from core.utils import escape_markdown
from main_bot.utils.force_join import force_join_check


async def build_welcome_text(user) -> str:
    """Build personalized welcome text with user profile info."""
    first_name = user.first_name or "User"
    last_name = user.last_name or ""
    full_name = escape_markdown(f"{first_name} {last_name}".strip())
    username = escape_markdown(f"@{user.username}" if user.username else "Not set")
    user_id = user.id

    # Get account info
    sessions = await get_all_user_sessions(user_id)
    accounts_count = len(sessions) if sessions else 0

    # Branding info
    from models.user import is_user_branded
    is_branded = await is_user_branded(user_id)
    branding_tag = "🟢 ACTIVE" if is_branded else "🔴 MISSING"

    text = f"""
⚡ *GROUP MESSAGE SCHEDULER* ⚡

*★ V5 ELITE — FREE EDITION ★*

*Welcome, {full_name}!*
*Username:* {username}
*User ID:* `{user_id}`
*Accounts:* {accounts_count} connected
*Branding Status:* {branding_tag}

🎯 *AUTOMATE YOUR TELEGRAM ADS*

📤 *Auto-forward* to 15+ Groups
🛡️ *Smart Anti-Flood* Protection
🌙 *Auto Night Mode* (12AM-6AM)
📊 *Real-time* Dashboard
🔄 *Copy Mode & Shuffle* Mode
💬 *Auto-Responder* (DMs)
🔐 *Secure Encrypted* Sessions

⚙️ *HOW IT WORKS*

1️⃣ Connect your Telegram account
2️⃣ Add your target groups
3️⃣ Drop messages in *Saved Messages*
4️⃣ Sit back — we forward them! 🚀

👇 *TAP A BUTTON BELOW TO BEGIN*
"""
    return text


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and deep links."""
    user = update.effective_user
    args = context.args

    # Check for referral or connected deep link
    referred_by = None
    show_dashboard = False

    if args:
        arg = args[0]
        if arg.startswith("ref_"):
            referred_by = arg[4:]
        elif arg == "connected":
            show_dashboard = True

    # Create or get user
    await create_user(user.id, referred_by=referred_by)

    if show_dashboard:
        from main_bot.handlers.dashboard import show_dashboard
        await show_dashboard(update, context)
        return

    # Force join check
    if not await force_join_check(update, context):
        return

    # Build personalized welcome
    welcome_text = await build_welcome_text(user)

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_welcome_keyboard(),
    )


async def home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle home button callback - return to welcome screen."""
    query = update.callback_query
    await query.answer()

    # Force join check
    if not await force_join_check(update, context):
        return

    user = update.effective_user
    welcome_text = await build_welcome_text(user)

    await query.edit_message_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_welcome_keyboard(),
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Check Again' button for force join."""
    query = update.callback_query
    await query.answer("Checking...")
    
    if await force_join_check(update, context):
        # If joined, show home
        await home_callback(update, context)
