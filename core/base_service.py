"""
V5 Elite Framework — Abstract Base Service.
Provides standardized lifecycle management, logging, and graceful shutdown.
"""

import asyncio
import logging
import signal
import platform
from abc import ABC, abstractmethod
from core.logger import setup_service_logging
from core.database import init_database, close_connection

logger = logging.getLogger(__name__)

class BaseService(ABC):
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.running = False
        self._loop = asyncio.get_event_loop()
        self._stop_event = asyncio.Event()

    async def _setup_signals(self):
        """Standard SIGINT/SIGTERM handling across OS platforms."""
        if platform.system() != "Windows":
            for sig in (signal.SIGINT, signal.SIGTERM):
                self._loop.add_signal_handler(sig, self.trigger_stop)
        else:
            # On Windows, we rely on try/except KeyboardInterrupt or asyncio.CancelledError
            pass

    def trigger_stop(self):
        """Signal the service to stop gracefully."""
        logger.info(f"🛑 Shutdown signal received for {self.service_name}...")
        self.running = False
        self._stop_event.set()

    @abstractmethod
    async def on_start(self):
        """Implemented by child classes to perform startup logic."""
        pass

    @abstractmethod
    async def on_stop(self):
        """Implemented by child classes to perform cleanup logic."""
        pass

    async def run_forever(self):
        """Main entry point for all V5 services."""
        setup_service_logging(self.service_name)
        logger.info(f"🚀 Initializing {self.service_name} Elite (V5)...")
        
        try:
            await init_database()
            await self._setup_signals()
            self.running = True
            
            # Subclass startup
            await self.on_start()
            
            # Wait until stop is triggered
            await self._stop_event.wait()
            
        except asyncio.CancelledError:
            logger.info("Service task cancelled.")
        except Exception as e:
            logger.critical(f"FATAL ERROR in {self.service_name}: {e}", exc_info=True)
        finally:
            await self._shutdown()

    async def _shutdown(self):
        """Final cleanup orchestrator."""
        self.running = False
        logger.info(f"🧹 Commencing graceful shutdown for {self.service_name}...")
        
        try:
            await asyncio.wait_for(self.on_stop(), timeout=10.0)
        except Exception as e:
            logger.error(f"Error during {self.service_name} cleanup: {e}")
            
        await close_connection()
        logger.info(f"✅ {self.service_name} shut down successfully.")
