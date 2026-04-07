# 👑 KURUP ADS BOT: ELITE V5 EDITION

Welcome to the official repository for the **Kurup Ads Bot Elite V5**. This is a professional-grade Telegram automation system featuring a unified architecture, proactive session monitoring, and a single-entry orchestrator.

---

## 🛠 Prerequisites

- **Python 3.10+** (Recommended)
- **MongoDB Atlas** Connection String
- **Telegram Account Owner ID** (Your user ID)
- **API ID** & **API Hash** (From [my.telegram.org](https://my.telegram.org))

---

## 🚀 1. Initial Setup

### Clone & Install
```bash
# Clone the repository
git clone https://github.com/amarhoonbhai/testing.git
cd testing

# Setup Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment (`.env`)
Copy `.env.example` to `.env` and fill in your details:
- `MAIN_BOT_TOKEN`: The token for your main management bot.
- `LOGIN_BOT_TOKEN`: The token for your account connector bot.
- `MONGODB_URI`: Your MongoDB Atlas URI.
- `OWNER_ID`: Your numerical Telegram ID.

---

## 🎮 2. Running the Bot (The Orchestrator)

The V5 Elite architecture uses a single entry point: `main.py`.

### For Development / Single Instance
Run all services together in one process:
```bash
python main.py all
```

### For Production / Scaling
Run each service as an independent process for maximum stability:
```bash
python main.py main_bot    # User Dashboard
python main.py login_bot   # Account Connector
python main.py sender      # Message Delivery engine
python main.py userbot     # Account Command Listener
```

---

## 🛡️ 3. Deployment (Production)

### Option A: PM2 (Recommended)
```bash
# Start all services separately
pm2 start "python main.py main_bot" --name kurup-main
pm2 start "python main.py login_bot" --name kurup-login
pm2 start "python main.py sender" --name kurup-sender
pm2 start "python main.py userbot" --name kurup-userbot

# Management
pm2 list          # Check status
pm2 logs          # View live logs
pm2 restart all   # Restart everything
```

### Option B: Systemd (Linux VPS)
Create a service file for each mode (e.g., `/etc/systemd/system/kurup-sender.service`):
```ini
[Unit]
Description=KURUP ADS - Sender Service
After=network.target

[Service]
WorkingDirectory=/opt/testing
ExecStart=/opt/testing/venv/bin/python main.py sender
Restart=always
EnvironmentFile=/opt/testing/.env

[Install]
WantedBy=multi-user.target
```

---

## ❓ Troubleshooting

- **MongoDB Timeout**: Ensure your server's IP address (e.g., `103.211.52.66`) is added to the **Network Access** whitelist in MongoDB Atlas.
- **ImportErrors**: Ensure your `venv` is activated before running any service.
- **Bot Not Responding**: Check your `.env` for trailing spaces or incorrect tokens.

---

## 📞 Support
Join [@PHilobots](https://t.me/PHilobots) on Telegram for updates and professional assistance.
