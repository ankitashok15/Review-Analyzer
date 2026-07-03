import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.observability.metrics import get_metrics
from src.security.rate_limit import check_rate_limit


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request IDs, enforce rate limits, and record API latency metrics."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        client_key = request.client.host if request.client else "unknown"
        path = request.url.path
        if path.startswith("/api/v1/"):
            allowed, _ = check_rate_limit(client_key, path)
            if not allowed:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={"X-Request-ID": request_id},
                )

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id

        if path.endswith("/search"):
            get_metrics().observe_latency("search", duration_ms)
        elif path.endswith("/ask"):
            get_metrics().observe_latency("ask", duration_ms)

        return response
