#!/bin/bash

echo "============================================"
echo "🚀 KURUP ADS BOT - One-Click Deploy"
echo "============================================"

# 1. Update & Dependencies
echo "Step 1: Installing system dependencies..."
sudo apt update && sudo apt install -y python3-pip python3-venv git pm2 2>/dev/null

# 2. Virtual Env
echo "Step 2: Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Environment Check
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found! Creating from example..."
    cp .env.example .env
    echo "❌ Please edit your .env file with nano .env and then run this script again!"
    exit 1
fi

# 4. Launch with PM2 (Recommended for 1-click & auto-restart)
echo "Step 4: Launching services with PM2..."

if command -v pm2 &> /dev/null
then
    pm2 stop all 2>/dev/null
    pm2 delete all 2>/dev/null
    
    pm2 start "venv/bin/python -m main_bot.bot" --name kurup_bot
    pm2 start "venv/bin/python webapp/server.py" --name kurup_webapp
    pm2 start "venv/bin/python -m services.sender.sender" --name kurup_sender
    
    pm2 save
    pm2 startup
    
    echo ""
    echo "✅ SERVICES STARTED! Use 'pm2 logs' to view activity."
    echo "============================================"
else
    echo "⚠️  PM2 not found. Using basic background start..."
    chmod +x scripts/start_all.sh
    ./scripts/start_all.sh
fi
