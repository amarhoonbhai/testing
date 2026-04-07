# Deployment Guide (Standard Setup): KURUP ADS BOT 🚀

This guide walks you through deploying the premium KURUP ADS system using **Python**. The system operates as 4 independent background services.

## Prerequisites
- **Python 3.10+**
- **MongoDB Atlas** URI
- **API ID** & **API Hash** (from [my.telegram.org](https://my.telegram.org))

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
   - `MAIN_BOT_TOKEN`: Primary bot token for user management.
   - `LOGIN_BOT_TOKEN`: Secondary bot token for session login.
   - `MONGODB_URI`: Your MongoDB Atlas connection string.
   - `OWNER_ID`: Your Telegram user ID.

---

## 3. Launching the Services (4 Processes)

You need to run **four separate processes**. It is highly recommended to use `pm2` or `screen` to keep them running.

### Term 1: Main Bot (User Dashboard)
```bash
python -m main_bot.bot
```

### Term 2: Login Bot (Session Manager)
```bash
python -m login_bot.bot
```

### Term 3: Sender Service (Message Worker)
```bash
python -m services.sender.sender
```

### Term 4: Branding Service (Security Enforcer)
```bash
python -m services.branding.branding
```

### Term 5: Userbot Service (Account Commands)
```bash
python -m services.userbot.userbot
```

---

## 4. Monitoring (PM2 - Recommended)

Using `pm2` allows for automatic restarts and easy log management:

```bash
# Install pm2
npm install -g pm2

# Start all kurup services
pm2 start "python -m main_bot.bot" --name main_bot
pm2 start "python -m login_bot.bot" --name login_bot
pm2 start "python -m services.sender.sender" --name sender
pm2 start "python -m services.branding.branding" --name branding
pm2 start "python -m services.userbot.userbot" --name userbot

# Useful commands
pm2 list          # Check status
pm2 logs          # View live logs
pm2 restart all   # Restart everything
```

---

## 5. Troubleshooting

- **MongoDB connection**: Ensure your IP is whitelisted in MongoDB Atlas.
- **Bot Tokens**: Verify `MAIN_BOT_TOKEN` and `LOGIN_BOT_TOKEN` are unique.
- **Environment**: Always ensure `venv` is activated before running.

---

## Support
Join [@PHilobots](https://t.me/PHilobots) on Telegram for updates and assistance.
