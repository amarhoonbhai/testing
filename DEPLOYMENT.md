# Deployment Guide (Standard Setup)

This guide walks you through deploying the Group Message Scheduler directly on your system (VPS or local machine) using **Python**.

## Prerequisites
- **Python 3.10+**
- **MongoDB Atlas** URI (or local MongoDB)
- **API ID** & **API Hash** (from [my.telegram.org](https://my.telegram.org))

---

## 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/amarhoonbhai/message.git
cd message

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

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
   - `MAIN_BOT_TOKEN`, `LOGIN_BOT_TOKEN`
   - `API_ID`, `API_HASH`
   - `MONGODB_URI`
   - `OWNER_ID`

---

## 3. Launching the Services

You need to run **three separate processes**. It is recommended to use `screen`, `tmux`, or `pm2` to keep them running in the background.

### Term 1: Main Bot (User Dashboard)
```bash
python -m main_bot.bot
```

### Term 2: Login Bot (Account Connection)
```bash
python -m login_bot.bot
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
pm2 start "python -m main_bot.bot" --name main_bot
pm2 start "python -m login_bot.bot" --name login_bot
pm2 start "python -m services.sender.sender" --name sender

# Monitor logs
pm2 logs
```

---

## 5. Troubleshooting

- **MongoDB connection**: Ensure your VPS IP is whitelisted in MongoDB Atlas.
- **Port issues**: Ensure the machine has access to necessary ports (default MongoDB/HTTPS).
- **Environment**: Always ensure `venv` is activated before running.
