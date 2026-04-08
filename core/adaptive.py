"""
Adaptive Delay Controller — ports the dynamic wait logic from message.git.
Includes the UserLogAdapter for professional contextual logging.
"""

import logging
import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class UserLogAdapter(logging.LoggerAdapter):
    """
    Adapter that adds user/account context to log messages.
    Format: [User ID][Phone] Message
    """
    def process(self, msg, kwargs):
        user_id = self.extra.get('user_id', 'Unknown')
        phone = self.extra.get('phone', 'Unknown')
        return f"[User {user_id}][{phone}] {msg}", kwargs

class AdaptiveDelayController:
    """Dynamically adjusts gaps based on FloodWait and success rates."""
    MAX_MULTIPLIER = 10.0  # Hard cap — prevents runaway wait times

    def __init__(self, base_gap: int):
        self.base_gap = base_gap
        self.multiplier = 1.0
        self.success_streak = 0
        self.last_flood_at = None

    def get_gap(self) -> int:
        """Returns the current gap (base * multiplier)."""
        return int(self.base_gap * self.multiplier)

    def on_flood(self, wait_seconds: int):
        """Increase multiplier significantly when a flood wait is encountered."""
        self.last_flood_at = datetime.datetime.utcnow()
        new_mult = max(self.multiplier * 1.5, (wait_seconds / self.base_gap) * 1.1)
        self.multiplier = min(new_mult, self.MAX_MULTIPLIER)
        self.success_streak = 0

    def on_success(self):
        """Gradually decrease multiplier as success streak grows."""
        self.success_streak += 1
        if self.success_streak >= 10 and self.multiplier > 1.0:
            self.multiplier = max(1.0, self.multiplier * 0.9)
            self.success_streak = 0
