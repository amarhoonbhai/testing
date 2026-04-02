# VPS Deployment Guide: KURUP ADS BOT 🚀

Complete guide to deploy the premium KURUP ADS system on a VPS (Ubuntu/Debian) using **Systemd** for high availability.

## Prerequisites
- VPS with Ubuntu 20.04+ or Debian 11+
- SSH access to your server
- Python 3.9+ installed
- MongoDB Atlas (or local MongoDB)

---

## Step 1: System Update & Dependencies
```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv git screen -y
```

---

## Step 2: Clone & Setup
```bash
mkdir -p /opt/kurup-ads
cd /opt/kurup-ads
git clone https://github.com/amarhoonbhai/message.git .

# Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Step 3: Configure Environment
```bash
cp .env.example .env
nano .env
```

**Required Variables:**
```ini
MAIN_BOT_TOKEN=your_primary_bot_token
LOGIN_BOT_TOKEN=your_login_bot_token
OWNER_ID=your_telegram_id
MONGODB_URI=mongodb+srv://...
```

---

## Step 4: Run with Systemd (Recommended)

### 1. Main Bot Service
`sudo nano /etc/systemd/system/kurup-bot.service`
```ini
[Unit]
Description=KURUP ADS - Main Bot
After=network.target

[Service]
WorkingDirectory=/opt/kurup-ads
ExecStart=/opt/kurup-ads/venv/bin/python -m main_bot.bot
Restart=always
EnvironmentFile=/opt/kurup-ads/.env

[Install]
WantedBy=multi-user.target
```

### 2. Login Bot Service
`sudo nano /etc/systemd/system/kurup-login.service`
```ini
[Unit]
Description=KURUP ADS - Login Bot
After=network.target

[Service]
WorkingDirectory=/opt/kurup-ads
ExecStart=/opt/kurup-ads/venv/bin/python -m login_bot.bot
Restart=always
EnvironmentFile=/opt/kurup-ads/.env

[Install]
WantedBy=multi-user.target
```

### 3. Sender (Worker) Service
`sudo nano /etc/systemd/system/kurup-sender.service`
```ini
[Unit]
Description=KURUP ADS - Sender Service
After=network.target

[Service]
WorkingDirectory=/opt/kurup-ads
ExecStart=/opt/kurup-ads/venv/bin/python -m services.sender.sender
Restart=always
EnvironmentFile=/opt/kurup-ads/.env

[Install]
WantedBy=multi-user.target
```

### 4. Branding Service
`sudo nano /etc/systemd/system/kurup-branding.service`
```ini
[Unit]
Description=KURUP ADS - Branding Enforcement
After=network.target

[Service]
WorkingDirectory=/opt/kurup-ads
ExecStart=/opt/kurup-ads/venv/bin/python -m services.branding.branding
Restart=always
EnvironmentFile=/opt/kurup-ads/.env

[Install]
WantedBy=multi-user.target
```

---

## Step 5: Enable & Start

```bash
sudo systemctl daemon-reload

# Enable all
sudo systemctl enable kurup-bot kurup-login kurup-sender kurup-branding

# Start all
sudo systemctl start kurup-bot kurup-login kurup-sender kurup-branding

# Check Status
sudo systemctl status kurup-*
```

---

## Useful Commands

```bash
# View Live Logs
journalctl -u kurup-bot -f
journalctl -u kurup-login -f
journalctl -u kurup-sender -f
journalctl -u kurup-branding -f

# Global Operations
sudo systemctl restart kurup-bot kurup-login kurup-sender kurup-branding
sudo systemctl stop kurup-bot kurup-login kurup-sender kurup-branding
```

---

## Support
Join [@PHilobots](https://t.me/PHilobots) on Telegram for updates and assistance.
