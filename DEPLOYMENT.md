# Deployment Guide (Standard Setup): KURUP ADS BOT 🚀

This guide walks you through deploying the premium KURUP ADS system directly on your local machine or VPS using **Python**.

## Prerequisites
- **Python 3.10+**
- **MongoDB Atlas** URI
- **API ID** & **API Hash** (from [my.telegram.org](https://my.telegram.org))
- **A Domain or Public IP** (for the WebApp)

---

## 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/amarhoonbhai/message.git
cd message

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your details:
   - `MAIN_BOT_TOKEN`: Your primary bot token.
   - `WEBAPP_URL`: The URL where your WebApp will be accessible.
   - `MONGODB_URI`: Your MongoDB Atlas connection string.
   - `OWNER_ID`: Your Telegram user ID.

---

## 3. Launching the Services

You need to run **three separate processes**. It is recommended to use `screen`, `tmux`, or `pm2` to keep them running in the background.

### Term 1: Main Bot (Gateway)
```bash
python -m main_bot.bot
```

### Term 2: WebApp API (Command Center)
```bash
python webapp/server.py
```

### Term 3: Sender Service (Heartbeat & Execution)
```bash
python -m services.sender.sender
```

---

## 4. Monitoring (PM2 - Recommended)

If you have `Node.js` installed, you can use `pm2` to manage the processes:

```bash
# Install pm2
npm install -g pm2

# Start all services
pm2 start "python -m main_bot.bot" --name kurup_bot
pm2 start "python webapp/server.py" --name kurup_webapp
pm2 start "python -m services.sender.sender" --name kurup_sender

# Monitor logs
pm2 logs
```

---

## 5. Troubleshooting

- **MongoDB connection**: Ensure your IP is whitelisted in MongoDB Atlas.
- **Bot Tokens**: Verify `MAIN_BOT_TOKEN` and `LOGIN_BOT_TOKEN` are unique.
- **Environment**: Always ensure `venv` is activated (`source venv/bin/activate`).

---

## Support
Join [@PHilobots](https://t.me/PHilobots) on Telegram for updates and assistance.
