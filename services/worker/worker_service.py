"""
Orchestrator wrapper for the Unified Worker Manager.
Integrates the standalone WorkerManager into the KURUP V5 ELITE service architecture.
"""

import logging
import asyncio
from typing import Optional

from core.base_service import BaseService
from services.worker.worker import WorkerManager

logger = logging.getLogger(__name__)

class WorkerService(BaseService):
    """
    Consolidated Worker Service.
    Replaces Userbot (listening) and Sender (sending) with a unified per-account architecture.
    """
    
    def __init__(self):
        super().__init__("WorkerService")
        self.manager: Optional[WorkerManager] = None
    
    async def start(self):
        """Start the worker manager."""
        logger.info("Initializing Unified Worker Service...")
        self.manager = WorkerManager()
        
        # The WorkerManager's start() is a long-running loop
        # We run it as a background task via the base class or directly
        try:
            await self.manager.start()
        except asyncio.CancelledError:
            logger.info("Worker service cancelled")
        except Exception as e:
            logger.error(f"Worker service error: {e}")
            raise
    
    async def stop(self):
        """Gracefully stop all worker tasks."""
        if self.manager:
            logger.info("Shutting down Unified Worker Service...")
            self.manager.stop()
            await self.manager.stop_all()
        logger.info("Worker service stopped.")

if __name__ == "__main__":
    # For standalone testing
    service = WorkerService()
    asyncio.run(service.run())
