# KURUP ADS BOT 🚀
The ultimate premium Telegram ad automation system. 

A unified platform to manage multiple Telegram accounts, target groups, and automated ad campaigns through a powerful **Telegram WebApp**.

## ✨ Features
- 🚀 **Unified WebApp** - Manage groups, accounts, and settings in one place.
- 🛡️ **Anti-Freeze Algorithm** - Human-like behavior, spintax, and auto-pauses to prevent bans.
- ⏳ **Master Control** - Global Start/Stop toggle for all your campaigns.
- 💎 **Premium Dashboard** - Real-time stats and live session monitor.
- 🔐 **Secure Login** - Interactive OTP & 2FA linking directly in the WebApp.

## 🛠️ Quick Start (One-Click Deploy)

**Linux (VPS):**
```bash
chmod +x setup.sh && ./setup.sh
```

**Windows (Local):**
Double-click `setup.bat`.

### Manual Configuration
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with your `MAIN_BOT_TOKEN`, `WEBAPP_URL`, and `MONGODB_URI`.

### 3. Run the Services

**Windows:**
```bash
scripts\start_all.bat
```

**Linux:**
```bash
chmod +x scripts/start_all.sh
./scripts/start_all.sh
```

## 🏗️ Architecture
- **Main Bot**: Gateway to the WebApp dashboard.
- **WebApp**: Central command center for management.
- **Worker Service**: High-performance background message dispatcher.
- **Sender**: Heartbeat service managing job execution and flood-waits.

## ⚙️ Configuration
| Variable | Description |
|----------|-------------|
| `MAIN_BOT_TOKEN` | Token for your KURUP ADS HUB bot |
| `WEBAPP_URL` | URL for the Telegram Mini App |
| `OWNER_ID` | Your Telegram user ID |
| `MONGODB_URI` | MongoDB Atlas connection string |

## ⚖️ License
MIT
