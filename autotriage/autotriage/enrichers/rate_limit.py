from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    capacity: int
    refill_per_second: float
    tokens: float
    last_refill: float

    @classmethod
    def per_minute(cls, capacity: int) -> "TokenBucket":
        return cls(capacity=capacity, refill_per_second=capacity / 60.0, tokens=float(capacity), last_refill=time.time())

    def allow(self, cost: float = 1.0) -> bool:
        now = time.time()
        elapsed = max(0.0, now - self.last_refill)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

