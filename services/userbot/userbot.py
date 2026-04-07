"""
Userbot Service — keeps connected accounts listening for commands.
Runs a long-running process for each session to respond to .ping, .stats, etc.
"""

import asyncio
import logging
import signal
import platform

from core.logger import setup_service_logging
from core.database import init_database, close_connection, get_database
from services.worker.session_pool import SessionPool
from services.worker.commands import register_userbot_handlers, register_auto_responder

logger = logging.getLogger(__name__)

class UserbotService:
    def __init__(self):
        self.running = False
        self.pool = SessionPool()
        self._tasks = []

    async def get_all_connected_sessions(self) -> list:
        db = get_database()
        return await db.sessions.find({"connected": True}).to_list(length=1000)

    async def start(self):
        self.running = True
        logger.info("🚀 Userbot Service starting...")
        
        sessions = await self.get_all_connected_sessions()
        if not sessions:
            logger.info("No connected sessions found — waiting...")
            # We skip the main loop for now and just wait
            # Actually, let's just keep polling for new sessions every 60s
            while self.running:
                sessions = await self.get_all_connected_sessions()
                if sessions:
                    break
                await asyncio.sleep(60)

        for s in sessions:
            user_id = s.get("user_id")
            phone = s.get("phone")
            try:
                client = await self.pool.acquire(user_id, phone)
                register_userbot_handlers(client)
                register_auto_responder(client)
                task = asyncio.create_task(client.run_until_disconnected())
                self._tasks.append(task)
                logger.info(f"[{phone}] Commands listener ACTIVE")
            except Exception as e:
                logger.error(f"[{phone}] Failed to start listener: {e}")

        if self._tasks:
            await asyncio.gather(*self._tasks)

    async def stop(self):
        self.running = False
        for task in self._tasks:
            task.cancel()
        await self.pool.stop()
        logger.info("Userbot Service shut down.")

async def main():
    setup_service_logging("userbot")
    await init_database()
    service = UserbotService()
    
    # Handle signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(service.stop()))
        except NotImplementedError:
            pass # Windows

    try:
        await service.start()
    except asyncio.CancelledError:
        pass
    finally:
        await close_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
