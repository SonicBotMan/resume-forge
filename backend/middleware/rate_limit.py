"""Per-device sliding window rate limiter with separate buckets."""

import asyncio
import os
import jwt as pyjwt
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from services.auth import JWT_ALGORITHM

_JWT_SECRET = os.environ.get("JWT_SECRET", "")
_JWT_ISSUER = "resume-forge"
_JWT_AUDIENCE = "resume-forge-api"


def get_client_key(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = pyjwt.decode(
                token,
                _JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                audience=_JWT_AUDIENCE,
                issuer=_JWT_ISSUER,
            )
            sub = payload.get("sub", "")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host}"


class RateLimiter:
    # Limits per bucket type
    BUCKET_LIMITS = {
        "get": (120, timedelta(minutes=1)),
        "ai": (20, timedelta(hours=1)),
        "general": (60, timedelta(minutes=1)),
        "login": (10, timedelta(minutes=15)),
        "admin": (30, timedelta(minutes=1)),
    }
    MAX_DEVICES = 10000

    def __init__(self) -> None:
        # { device_key: { bucket_type: [timestamps] } }
        self._requests: Dict[str, Dict[str, List[datetime]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._lock = asyncio.Lock()

    def _cleanup(self, now: datetime) -> None:
        if len(self._requests) > self.MAX_DEVICES:
            all_keys = [
                (k, sum(len(v) for v in buckets.values()))
                for k, buckets in self._requests.items()
                if buckets
            ]
            all_keys.sort(key=lambda x: x[1])
            to_remove = len(self._requests) - self.MAX_DEVICES // 2
            for k, _ in all_keys[:to_remove]:
                del self._requests[k]

    def _prune_bucket(self, device_id: str, bucket: str, now: datetime) -> List[datetime]:
        """Remove expired entries and return remaining timestamps."""
        _, window = self.BUCKET_LIMITS[bucket]
        timestamps = self._requests[device_id][bucket]
        self._requests[device_id][bucket] = [
            t for t in timestamps if now - t < window
        ]
        return self._requests[device_id][bucket]

    async def check(self, device_id: str, is_ai: bool = False, is_get: bool = False) -> bool:
        async with self._lock:
            now = datetime.now()
            bucket = "ai" if is_ai else ("get" if is_get else "general")
            limit, _ = self.BUCKET_LIMITS[bucket]
            current = self._prune_bucket(device_id, bucket, now)
            if len(current) >= limit:
                return False
            current.append(now)
            self._cleanup(now)
            return True

    async def get_retry_after(self, device_id: str, is_ai: bool = False, is_get: bool = False) -> int:
        async with self._lock:
            now = datetime.now()
            bucket = "ai" if is_ai else ("get" if is_get else "general")
            _, window = self.BUCKET_LIMITS[bucket]
            timestamps = self._prune_bucket(device_id, bucket, now)
            if not timestamps:
                return 0
            oldest = min(timestamps)
            remaining = int((oldest + window - now).total_seconds())
            return max(remaining, 0)

    async def check_login(self, device_id: str) -> bool:
        async with self._lock:
            now = datetime.now()
            limit, _ = self.BUCKET_LIMITS["login"]
            current = self._prune_bucket(device_id, "login", now)
            if len(current) >= limit:
                return False
            current.append(now)
            return True

    async def check_admin(self, device_id: str) -> bool:
        async with self._lock:
            now = datetime.now()
            limit, _ = self.BUCKET_LIMITS["admin"]
            current = self._prune_bucket(device_id, "admin", now)
            if len(current) >= limit:
                return False
            current.append(now)
            return True


AI_PATHS = ["/analyze", "/match", "/generate", "/optimize", "/ats-score", "/jd-parse", "/merge", "/rewrite"]

rate_limiter = RateLimiter()
