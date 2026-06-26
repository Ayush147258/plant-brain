"""Custom middleware for PlantBrain request logging, errors, and rate limiting."""

import logging
import threading
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming request and outgoing response with timing metadata."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response details, then add tracing headers."""

        start_time = time.time()
        request_id = str(uuid4())[:8]
        client_host = request.client.host if request.client else "unknown"

        logger.info(f"[{request_id}] {request.method} {request.url.path} - Client: {client_host}")
        response = await call_next(request)
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({elapsed_ms}ms)")

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Return clean JSON responses for unhandled server errors."""

    async def dispatch(self, request: Request, call_next):
        """Catch unhandled exceptions and hide stack traces from clients."""

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                f"Unhandled error on {request.method} {request.url.path}: {str(exc)}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again.",
                    "path": str(request.url.path),
                },
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter keyed by client IP."""

    _request_counts: dict[str, list[float]] = {}
    _lock: threading.Lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        """Limit requests per IP over a one-minute sliding window."""

        if not settings.rate_limit_enabled:
            return await call_next(request)

        if request.url.path in ["/", "/api/v1/health"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60
        limit = settings.rate_limit_requests_per_minute

        with self._lock:
            if client_ip not in self._request_counts:
                self._request_counts[client_ip] = []

            self._request_counts[client_ip] = [
                timestamp for timestamp in self._request_counts[client_ip] if now - timestamp < window
            ]
            count = len(self._request_counts[client_ip])

            if count >= limit:
                retry_after = int(window - (now - self._request_counts[client_ip][0]))
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Limit: {limit} per minute.",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            self._request_counts[client_ip].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(limit - count - 1)
        return response
