from __future__ import annotations

import time


class CooldownManager:
    def __init__(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds
        self._last_seen: dict[int, float] = {}

    def check(self, user_id: int, authorized_users: set[int]) -> int:
        if user_id in authorized_users:
            return 0
        now = time.time()
        previous = self._last_seen.get(user_id)
        self._last_seen[user_id] = now
        # Cleanup old entries to prevent memory growth
        self._cleanup_old_entries(now)
        if previous is None:
            return 0
        elapsed = now - previous
        if elapsed >= self.timeout_seconds:
            return 0
        return int(self.timeout_seconds - elapsed)

    def _cleanup_old_entries(self, now: float) -> None:
        """Remove entries older than 2x timeout to prevent memory leak."""
        cutoff = now - (self.timeout_seconds * 2)
        to_remove = [uid for uid, ts in self._last_seen.items() if ts < cutoff]
        for uid in to_remove:
            del self._last_seen[uid]
