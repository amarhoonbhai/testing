"""
KURUP V5 ELITE — Unified Orchestrator.
The single entry point to manage all bot services.
"""

import asyncio
import argparse
import sys
import logging
from core.base_service import BaseService
from services.sender.sender import UnifiedSender
from services.sender.scheduler import UnifiedScheduler
from services.branding.branding import BrandingService
from services.userbot.userbot import UserbotService
from main_bot.bot import MainBotService
from login_bot.bot import LoginBotService

logger = logging.getLogger("Orchestrator")

async def run_composite(services: list):
    """Run multiple BaseServices within a single event loop."""
    tasks = [asyncio.create_task(s.run_forever()) for s in services]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Composite tasks cancelled.")

def main():
    parser = argparse.ArgumentParser(description="KURUP V5 ELITE Unified Orchestrator")
    parser.add_argument(
        "mode", 
        choices=["main_bot", "login_bot", "sender", "scheduler", "userbot", "all"], 
        help="Service to run"
    )
    
    args = parser.parse_args()
    
    if args.mode == "main_bot":
        asyncio.run(MainBotService().run_forever())
    elif args.mode == "login_bot":
        asyncio.run(LoginBotService().run_forever())
    elif args.mode == "sender":
        asyncio.run(UnifiedSender().run_forever())
    elif args.mode == "scheduler":
        asyncio.run(UnifiedScheduler().run_forever())
    elif args.mode == "userbot":
        asyncio.run(UserbotService().run_forever())
    elif args.mode == "all":
        # Note: In production, high-load bots should run in separate processes.
        # This 'all' mode is perfect for development or low-to-medium load.
        services = [
            MainBotService(), LoginBotService(), 
            UnifiedSender(), UnifiedScheduler(), 
            BrandingService(), UserbotService()
        ]
        try:
            asyncio.run(run_composite(services))
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
