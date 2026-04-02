@echo off
title KURUP ADS BOT - ONE CLICK SETUP
echo ============================================
echo 🚀 KURUP ADS BOT - Windows Setup & Launch
echo ============================================

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python from python.org and add it to PATH.
    pause
    exit /b
)

:: 2. Create Virtual Env
if not exist "venv" (
    echo Step 1: Creating virtual environment...
    python -m venv venv
)

:: 3. Install Requirements
echo Step 2: Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

:: 4. Check for .env
if not exist ".env" (
    echo ⚠️  .env file not found! Creating from example...
    copy .env.example .env
    echo ❌ Please edit your .env file and then run this script again!
    notepad .env
    exit /b
)

:: 5. Launch
echo Step 3: Launching all services...
echo ============================================
start "MAIN BOT" cmd /k "venv\Scripts\python -m main_bot.bot"
start "WEBAPP" cmd /k "venv\Scripts\python webapp/server.py"
start "SENDER" cmd /k "venv\Scripts\python -m services.sender.sender"

echo ✅ ALL SERVICES STARTED!
echo Check the individual windows for activity.
pause
