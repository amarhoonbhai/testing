# Kurup Ads Bot

**Premium Telegram Ad Broadcasting Bot** — The Future of Telegram Automation.

A Telegram bot for legitimate opt-in marketing with multi-account support, smart delays, encrypted sessions, and a polished inline keyboard UI.

## Features

- **Multi-Account Hosting** — Host up to 5 Telegram accounts with encrypted sessions
- **Ad Broadcasting** — Send text, photo, or video ads to your groups/channels
- **Smart Intervals** — Configurable broadcast cycles (minimum 1200s)
- **Auto Reply** — Automated reply messages on hosted accounts
- **Analytics Dashboard** — Track sent messages, failures, and broadcast status
- **Enforced Branding** — Auto-apply name suffix and bio on hosted accounts
- **Force Join** — Channel verification before bot access
- **Session Encryption** — Fernet-encrypted Telethon sessions stored in MongoDB

## Quick Start

### 1. Prerequisites

- Python 3.10+
- MongoDB (Atlas or local)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- API credentials from [my.telegram.org](https://my.telegram.org)

### 2. Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd testing

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 3. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output to `ENCRYPTION_KEY` in your `.env` file.

### 4. Run

```bash
python -m app.bot.main
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop
docker-compose down
```

## Ubuntu VPS Deployment

```bash
# Install Python 3.11
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip

# Clone and setup
git clone <your-repo> && cd testing
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your credentials

# Run with systemd
sudo tee /etc/systemd/system/kurup-ads.service << EOF
[Unit]
Description=Kurup Ads Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python -m app.bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable kurup-ads
sudo systemctl start kurup-ads
sudo systemctl status kurup-ads
```

## Folder Structure

```
app/
├── __init__.py
├── config.py                    # Environment configuration
├── bot/
│   ├── main.py                  # Bot entry point & handler registration
│   ├── messages.py              # All text templates
│   ├── keyboards.py             # Inline keyboard builders
│   └── handlers/
│       ├── start.py             # /start, force-join, welcome
│       ├── dashboard.py         # Dashboard with live stats
│       ├── accounts.py          # Add/View/Delete accounts
│       ├── ads.py               # Set ad, interval, start/stop
│       ├── analytics.py         # Broadcasting analytics
│       └── auto_reply.py        # Auto-reply configuration
├── services/
│   ├── encryption_service.py    # Fernet session encryption
│   ├── telethon_service.py      # Telegram account management
│   ├── broadcast_service.py     # Background broadcasting
│   └── branding_service.py      # Enforced name/bio
├── database/
│   ├── mongo.py                 # Motor async MongoDB client
│   └── models.py                # Users, accounts, analytics CRUD
└── utils/
    └── logger.py                # Structured logging with redaction
```

## Security

- Sessions encrypted with **Fernet symmetric encryption**
- Phone numbers, OTPs, passwords **never logged**
- Automatic log sanitization filter
- OTP/password messages deleted after receipt
- Rate limiting on all broadcast operations

## Compliance

This bot is for **legitimate opt-in marketing only**:
- Only broadcasts to groups/channels the account is a member of
- Minimum 300-second broadcast interval
- Pause controls and flood-wait handling
- Clear Telegram ToS warnings

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Telegram bot token |
| `API_ID` | ✅ | Telegram API ID |
| `API_HASH` | ✅ | Telegram API hash |
| `MONGO_URI` | ✅ | MongoDB connection string |
| `ENCRYPTION_KEY` | ✅ | Fernet encryption key |
| `BOT_USERNAME` | ❌ | Bot username (default: KurupAdsBot) |
| `SUPPORT_USERNAME` | ❌ | Support username (default: kurupads) |
| `CHANNEL_USERNAME` | ❌ | Updates channel (default: philobots) |
| `ENFORCED_NAME` | ❌ | Name suffix for hosted accounts |
| `ENFORCED_BIO` | ❌ | Bio for hosted accounts |
| `REQUIRED_CHANNELS` | ❌ | Force-join channels (comma-separated) |
| `MAX_ACCOUNTS` | ❌ | Max accounts per user (default: 5) |
| `MIN_INTERVAL` | ❌ | Min broadcast interval in seconds (default: 300) |
