# VPS Deployment Guide: KURUP ADS BOT 🚀

Complete guide to deploy the premium KURUP ADS system on a VPS (Ubuntu/Debian).

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
MAIN_BOT_TOKEN=your_bot_token
WEBAPP_URL=https://your-webapp-domain.com
OWNER_ID=your_id
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

### 2. WebApp API Service
`sudo nano /etc/systemd/system/kurup-webapp.service`
```ini
[Unit]
Description=KURUP ADS - WebApp API
After=network.target

[Service]
WorkingDirectory=/opt/kurup-ads
ExecStart=/opt/kurup-ads/venv/bin/python webapp/server.py
Restart=always
EnvironmentFile=/opt/kurup-ads/.env

[Install]
WantedBy=multi-user.target
```

### 3. Sender Service
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

---

## Step 5: Enable & Start
```bash
sudo systemctl daemon-reload
sudo systemctl enable kurup-bot kurup-webapp kurup-sender
sudo systemctl start kurup-bot kurup-webapp kurup-sender

# Check Status
sudo systemctl status kurup-bot kurup-webapp kurup-sender
```

---

## Step 6: Public Access (Nginx Reverse Proxy)
Since the WebApp runs on **port 8000**, you need Nginx to point your domain (`cinetimetv.store`) to the app.

1. **Install Nginx:**
   ```bash
   sudo apt install nginx -y
   ```
2. **Create Config:**
   `sudo nano /etc/nginx/sites-available/kurup`
   ```nginx
   server {
       listen 80;
       server_name cinetimetv.store;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
3. **Enable & Reload:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/kurup /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **SSL (REQUIRED by Telegram):**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d cinetimetv.store
   ```

---

## Useful Commands
```bash
# View Live Logs
journalctl -u kurup-webapp -f
journalctl -u kurup-sender -f

# Restart All
sudo systemctl restart kurup-bot kurup-webapp kurup-sender
```

---

## Support
Join [@PHilobots](https://t.me/PHilobots) on Telegram for updates and assistance.
