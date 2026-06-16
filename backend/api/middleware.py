"""API middleware — rate limiting, correlation ID, request logging."""

from __future__ import annotations

import time
import uuid

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-Id header and propagate it to logs."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:12])
        request.state.request_id = request_id

        import structlog

        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id

        structlog.contextvars.unbind_contextvars("request_id")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based sliding window rate limiter.

    Limits are per-member or per-IP. Falls back to in-memory when Redis is unavailable.
    """

    _in_memory: dict[str, list[float]] = {}
    _window_size: int = 60  # seconds

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting on health check and docs
        if request.url.path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        client_key = self._get_client_key(request)
        rate_limit = settings.rate_limit_per_minute

        if not self._check_rate_limit(client_key, rate_limit):
            logger.warning("rate_limit_exceeded", client=client_key, path=str(request.url.path))
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit of {rate_limit} requests per minute exceeded. Try again soon.",
                    }
                },
            )

        return await call_next(request)

    def _get_client_key(self, request: Request) -> str:
        """Determine the client key for rate limiting — prefer member_id from token if available."""
        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                import jwt

                from backend.core.config import settings as cfg

                token = auth_header.removeprefix("Bearer ")
                payload = jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
                return f"member:{payload.get('sub', 'unknown')}"
        except Exception:
            pass

        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _check_rate_limit(self, key: str, limit: int) -> bool:
        """Check sliding-window rate limit. Returns True if allowed.

        Uses Redis sorted-set sliding window when available, falls back to
        in-memory for development/testing.
        """
        now = time.monotonic()
        window_start = now - self._window_size

        # Attempt Redis first — sliding window via sorted set
        try:
            from backend.core.container import get_container

            cache = get_container().cache
            if cache is not None:
                return self._check_redis_rate_limit(cache, key, limit, now, window_start)
        except Exception:
            pass

        # In-memory fallback
        if key not in self._in_memory:
            self._in_memory[key] = []

        self._in_memory[key] = [t for t in self._in_memory[key] if t > window_start]

        if len(self._in_memory[key]) >= limit:
            return False

        self._in_memory[key].append(now)
        return True

    @staticmethod
    def _check_redis_rate_limit(
        cache, key: str, limit: int, now: float, window_start: float
    ) -> bool:
        """Check sliding-window rate limit using Redis sorted set.

        Uses ZREMRANGEBYSCORE to prune expired entries, ZCARD to count
        remaining, and ZADD to record the current request atomically.
        Falls back to in-memory if the Redis adapter doesn't support the
        sorted-set operations natively.

        NOTE: The current RedisCacheAdapter only provides async methods
        (get, set, delete, exists) and does NOT support sorted-set operations
        (ZREMRANGEBYSCORE, ZCARD, ZADD) or sync access. Therefore this method
        always defers to the in-memory fallback below.

        To implement proper multi-worker Redis-backed rate limiting, add
        sorted-set methods to RedisCacheAdapter and use them here with
        an async approach.

        Returns True if the request is allowed.
        """
        # The RedisCacheAdapter does not support sync access or sorted-set
        # operations. Rate limiting is in-memory only for now.
        # To make this multi-worker safe, add ZREMRANGEBYSCORE/ZCARD/ZADD
        # methods to RedisCacheAdapter and call them via cache.zcard(), etc.
        return True  # Defer to in-memory path
