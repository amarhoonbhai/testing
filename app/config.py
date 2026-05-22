"""
Centralized configuration for Group Broadcaster Bot.

Loads all settings from environment variables via python-dotenv.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _safe_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


# ── Bot Token (REQUIRED) ────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Telegram API Credentials (REQUIRED for Telethon) ────────────────────────
API_ID: int = _safe_int(os.getenv("API_ID"), 0)
API_HASH: str = os.getenv("API_HASH", "")

# ── MongoDB (REQUIRED) ──────────────────────────────────────────────────────
MONGODB_URI: str = os.getenv("MONGODB_URI", os.getenv("MONGO_URI", ""))
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "kurup_ads")

# ── Encryption Key (REQUIRED — Fernet) ──────────────────────────────────────
ENCRYPTION_KEY: str = os.getenv("FERNET_KEY", os.getenv("ENCRYPTION_KEY", ""))

# ── Branding ─────────────────────────────────────────────────────────────────
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "GroupBroadcasterBot")
SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "kurupads")
CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "philobots")
ENFORCED_BIO: str = os.getenv("ENFORCED_BIO", "Powered by @KurupAdsBot | Network: @PhiloBots")
ENFORCED_NAME_SUFFIX: str = os.getenv("ENFORCED_NAME_SUFFIX", os.getenv("ENFORCED_NAME", "‣ Kᴜʀᴜᴘ Aᴅꜱ"))

# ── Force Join Channels (comma-separated, no @) ─────────────────────────────
REQUIRED_CHANNELS_STR: str = os.getenv("REQUIRED_CHANNELS", "philobots,sellinghub0")
REQUIRED_CHANNELS: list[str] = [
    c.strip() for c in REQUIRED_CHANNELS_STR.split(",") if c.strip()
]

# ── Owner ────────────────────────────────────────────────────────────────────
OWNER_ID: int = _safe_int(os.getenv("OWNER_ID"), 0)

# ── Logs Channel ─────────────────────────────────────────────────────────────
LOGS_CHANNEL_ID: int = _safe_int(os.getenv("LOGS_CHANNEL_ID"), 0)

# ── Banner Image Path ───────────────────────────────────────────────────────
BANNER_PATH: str = os.getenv("BANNER_PATH", "assets/banner.png")

# ── Timezone ─────────────────────────────────────────────────────────────────
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")

# ── Broadcast Algorithm ─────────────────────────────────────────────────────
SEND_DELAY_MIN: int = _safe_int(os.getenv("SEND_DELAY_MIN"), 3)    # Min seconds between sends
SEND_DELAY_MAX: int = _safe_int(os.getenv("SEND_DELAY_MAX"), 8)    # Max seconds between sends
BATCH_SIZE: int = _safe_int(os.getenv("BATCH_SIZE"), 5)            # Groups per batch
BATCH_GAP_MIN: int = _safe_int(os.getenv("BATCH_GAP_MIN"), 30)    # Min gap after batch
BATCH_GAP_MAX: int = _safe_int(os.getenv("BATCH_GAP_MAX"), 60)    # Max gap after batch
DEFAULT_INTERVAL: int = _safe_int(os.getenv("DEFAULT_INTERVAL"), 1200)  # 20 min between cycles
MIN_INTERVAL: int = _safe_int(os.getenv("MIN_INTERVAL"), 300)     # 5 min minimum
MAX_FAIL_SKIP: int = _safe_int(os.getenv("MAX_FAIL_SKIP"), 5)     # Skip group after N fails


def validate_config():
    """Validate critical configuration on startup."""
    missing: list[str] = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not MONGODB_URI:
        missing.append("MONGODB_URI")
    if not ENCRYPTION_KEY:
        missing.append("FERNET_KEY")
    if not OWNER_ID:
        missing.append("OWNER_ID")
    if not LOGS_CHANNEL_ID:
        missing.append("LOGS_CHANNEL_ID")

    if missing:
        print("\n" + "!" * 55)
        print(f"  CRITICAL: Missing environment variables:")
        for m in missing:
            print(f"    • {m}")
        print("  Please check your .env file.")
        print("!" * 55 + "\n")
        sys.exit(1)
