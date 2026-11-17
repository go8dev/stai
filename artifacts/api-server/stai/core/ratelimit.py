"""In-memory sliding-window rate limiter.

State lives in this process only: it resets on restart and is not shared between
processes. That is enough for the sign-in routes of a single-owner app.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable


class RateLimiter:
    def __init__(self, *, max_keys: int = 10_000, clock: Callable[[], float] = time.monotonic):
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._max_keys = max_keys
        self._clock = clock
        self._lock = threading.Lock()

    def allow(self, key: str, *, limit: int, window_seconds: float) -> bool:
        """Record one attempt for `key`. False means the limit is already used up."""
        now = self._clock()
        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                hits = deque()
                self._hits[key] = hits
                while len(self._hits) > self._max_keys:
                    self._hits.popitem(last=False)
            else:
                self._hits.move_to_end(key)

            cutoff = now - window_seconds
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
