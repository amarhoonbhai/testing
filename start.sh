#!/bin/bash

# Kill all running processes (including login_bot)
pkill -f scheduler
pkill -f branding
pkill -f sender
pkill -f main_bot
pkill -f login_bot

# Pull latest code
git pull origin main

# Restart all services
nohup python -m main_bot.bot > main_bot.log 2>&1 &
nohup python -m login_bot.bot > login_bot.log 2>&1 &
nohup python -m services.scheduler.scheduler > scheduler.log 2>&1 &
nohup python -m services.sender.sender > sender.log 2>&1 &
nohup python -m services.branding.branding > branding.log 2>&1 &
