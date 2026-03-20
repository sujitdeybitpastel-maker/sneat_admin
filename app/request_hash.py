"""
MD5 Request Hash System
=======================
Generates a unique MD5 hash for every HTTP request. The hash is derived from:
  - Current timestamp (microsecond precision)
  - Client IP address
  - HTTP method
  - Request path
  - A random 8-byte salt (os.urandom)

The hash is stored on Flask's `g` object and injected into every log line
via a custom logging.Filter. This allows full request traceability:
  grep "a3f8c1d2" logs/app.log   ->  shows every log line for that request.

The hash is also returned in all JSON error responses so that support/devs
can cross-reference a user-reported error with the exact server-side trace.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time

from flask import Flask, g, request

logger = logging.getLogger(__name__)


def _generate_request_hash() -> str:
    """Build a short MD5 hex digest unique to this request."""
    raw = (
        f"{time.time_ns()}"
        f"|{request.remote_addr or '0.0.0.0'}"
        f"|{request.method}"
        f"|{request.path}"
        f"|{os.urandom(8).hex()}"
    )
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


class RequestHashFilter(logging.Filter):
    """Logging filter that injects `req_hash` into every LogRecord.

    If we are inside a Flask request context and `g.req_hash` exists, use it.
    Otherwise fall back to '--------' (no request context, e.g. startup logs).

    This filter ALWAYS sets the attribute, so the formatter never gets a
    KeyError — even for log records emitted by third-party libraries on
    background threads.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "req_hash"):
            try:
                record.req_hash = g.req_hash  # type: ignore[attr-defined]
            except (RuntimeError, AttributeError):
                record.req_hash = "--------"
        return True


def init_request_hash(app: Flask) -> None:
    """Register before/after-request hooks that manage the MD5 hash lifecycle."""

    @app.before_request
    def _set_request_hash() -> None:
        g.req_hash = _generate_request_hash()
        logger.info(
            "[HASH-START] %s %s | hash=%s | ip=%s | user_agent=%s",
            request.method,
            request.path,
            g.req_hash,
            request.remote_addr,
            request.user_agent.string[:80] if request.user_agent else "-",
        )

    @app.after_request
    def _log_request_end(response):
        req_hash = getattr(g, "req_hash", "--------")
        logger.info(
            "[HASH-END]   %s %s | hash=%s | status=%d | size=%s",
            request.method,
            request.path,
            req_hash,
            response.status_code,
            response.content_length or "-",
        )
        # Inject hash into JSON error responses so users can report it
        if response.content_type and "application/json" in response.content_type:
            if response.status_code >= 400:
                try:
                    data = response.get_json(silent=True)
                    if isinstance(data, dict) and "req_hash" not in data:
                        data["req_hash"] = req_hash
                        response.set_data(
                            __import__("json").dumps(data, ensure_ascii=False)
                        )
                except Exception:
                    pass  # Don't break the response if injection fails
        return response
