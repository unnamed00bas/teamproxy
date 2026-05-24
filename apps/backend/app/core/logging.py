"""Structured JSON logging with correlation/request IDs."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = logging.getLogger("request")

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            getattr(response, "status_code", "?"),
            elapsed_ms,
        )
        response.headers["x-request-id"] = rid
        return response
