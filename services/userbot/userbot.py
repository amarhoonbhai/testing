"""
Userbot Service — keeps connected accounts listening for commands.
Runs a long-running process for each session to respond to .ping, .stats, etc.
"""

import asyncio
import logging
import signal
import platform

from core.base_service import BaseService
from core.database import get_database
from services.worker.session_pool import SessionManager
from services.worker.commands import register_userbot_handlers, register_auto_responder

logger = logging.getLogger(__name__)

class UserbotService(BaseService):
    def __init__(self):
        super().__init__("Userbot")
        self.pool = SessionManager()
        self._active_sessions = set() # (user_id, phone)
        self._listeners = {} # (user_id, phone) -> Task

    async def on_start(self):
        """Startup logic for the Userbot service."""
        await self.pool.start()
        # Start the Discovery Loop as a background task
        asyncio.create_task(self._discovery_loop())

    async def on_stop(self):
        """Cleanup logic for the Userbot service."""
        for task in self._listeners.values():
            task.cancel()
        await self.pool.stop()

    async def _discovery_loop(self):
        """Periodic sweep for new connected sessions."""
        while self.running:
            try:
                db = get_database()
                sessions = await db.sessions.find({"connected": True}).to_list(length=1000)
                
                for s in sessions:
                    user_id = s.get("user_id")
                    phone = s.get("phone")
                    sid = (user_id, phone)
                    
                    if sid in self._active_sessions:
                        continue
                        
                    logger.info(f"[{phone}] New session detected — activating listener...")
                    try:
                        client = await self.pool.acquire(user_id, phone)
                        
                        # Register handlers
                        register_userbot_handlers(client)
                        register_auto_responder(client)
                        
                        # Start persistent listener task and keep reference
                        fut = client.run_until_disconnected()
                        task = asyncio.create_task(fut)
                        
                        # Add callback to cleanup when task ends
                        def _on_finish(t, sid=sid):
                            self._listeners.pop(sid, None)
                            self._active_sessions.discard(sid)
                            logger.warning(f"[{sid[1]}] Listener task ended.")
                            
                        task.add_done_callback(_on_finish)
                        
                        self._listeners[sid] = task
                        self._active_sessions.add(sid)
                        logger.info(f"[{phone}] Command listener ACTIVE")
                        
                    except Exception as e:
                        logger.error(f"[{phone}] Failed to activate listener: {e}")

                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in Userbot discovery loop: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(UserbotService().run_forever())
