"""Tiny in-process TTL cache for expensive read paths (facts, timeline, analytics).

Not distributed — good enough to make repeated reads (dashboard, tab switches,
follow-up questions) fast without standing up Redis. Entries expire after `ttl`
seconds; callers can `invalidate(key)` after writes when freshness matters.
"""
from __future__ import annotations

import threading
import time
from typing import Any


class TTLCache:
    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            hit = self._store.get(key)
            if hit is None:
                return None
            expires_at, value = hit
            if time.monotonic() > expires_at:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self.ttl, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
