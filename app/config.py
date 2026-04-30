"""
Centralized configuration for Kurup Ads Bot.

Loads all settings from environment variables via python-dotenv.
Never exposes sensitive values in logs.
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
MONGO_URI: str = os.getenv("MONGO_URI", "")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "kurup_ads")

# ── Encryption Key (REQUIRED — Fernet) ──────────────────────────────────────
ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

# ── Branding ─────────────────────────────────────────────────────────────────
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "KurupAdsBot")
SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "kurupads")
CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "philobots")

# ── Enforced Branding (appended to hosted accounts) ─────────────────────────
ENFORCED_NAME: str = os.getenv("ENFORCED_NAME", "‣ Kᴜʀᴜᴘ Aᴅs")
ENFORCED_BIO: str = os.getenv("ENFORCED_BIO", "Powered by @KurupAdsBot | Network: @PhiloBots")

# ── Force Join Channels (comma-separated, no @) ─────────────────────────────
REQUIRED_CHANNELS_STR: str = os.getenv("REQUIRED_CHANNELS", "philobots,sellinghub0")
REQUIRED_CHANNELS: list[str] = [
    c.strip() for c in REQUIRED_CHANNELS_STR.split(",") if c.strip()
]

# ── Limits ───────────────────────────────────────────────────────────────────
MAX_ACCOUNTS: int = _safe_int(os.getenv("MAX_ACCOUNTS"), 5)
MIN_INTERVAL: int = _safe_int(os.getenv("MIN_INTERVAL"), 1200)   # 20 minutes minimum
DEFAULT_INTERVAL: int = 1200  # 20 minutes

# ── Rate Limiting (Anti-Freeze Protection) ──────────────────────────────────
SEND_GAP_SECONDS: int = _safe_int(os.getenv("SEND_GAP_SECONDS"), 300)  # 5 min between msgs
SEND_JITTER_MIN: int = _safe_int(os.getenv("SEND_JITTER_MIN"), 30)     # Random jitter range
SEND_JITTER_MAX: int = _safe_int(os.getenv("SEND_JITTER_MAX"), 90)     # Random jitter range
FLOOD_BACKOFF_BASE: int = _safe_int(os.getenv("FLOOD_BACKOFF_BASE"), 60)
FLOOD_BACKOFF_MAX: int = _safe_int(os.getenv("FLOOD_BACKOFF_MAX"), 3600)  # Max 1 hour
MAX_CONSECUTIVE_ERRORS: int = _safe_int(os.getenv("MAX_CONSECUTIVE_ERRORS"), 5)

# ── Night Mode (IST) ────────────────────────────────────────────────────────
NIGHT_MODE_ENABLED: bool = os.getenv("NIGHT_MODE_ENABLED", "true").lower() == "true"
NIGHT_MODE_START_HOUR: int = _safe_int(os.getenv("NIGHT_MODE_START"), 0)   # 12:00 AM
NIGHT_MODE_END_HOUR: int = _safe_int(os.getenv("NIGHT_MODE_END"), 5)       # 5:00 AM
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")

# ── Owner ────────────────────────────────────────────────────────────────────
OWNER_ID: int = _safe_int(os.getenv("OWNER_ID"), 0)

# ── Logs Channel ─────────────────────────────────────────────────────────────
LOGS_CHANNEL_ID: int = _safe_int(os.getenv("LOGS_CHANNEL_ID"), -1003818032027)

# ── Banner Image Path ───────────────────────────────────────────────────────
BANNER_PATH: str = os.getenv("BANNER_PATH", "assets/banner.png")


def validate_config():
    """Validate critical configuration on startup."""
    missing: list[str] = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not MONGO_URI:
        missing.append("MONGO_URI")
    if not ENCRYPTION_KEY:
        missing.append("ENCRYPTION_KEY")

    if missing:
        print("\n" + "!" * 55)
        print(f"  CRITICAL: Missing environment variables:")
        for m in missing:
            print(f"    • {m}")
        print("  Please check your .env file.")
        print("!" * 55 + "\n")
        sys.exit(1)
