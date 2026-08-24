import uuid
from flask import request, g
from .filters import REQUEST_ID, CORRELATION_ID, USER_ID, SESSION_ID, REMOTE_IP, START_TIME
from .logger import get_logger
import time


def generate_id(prefix="rid"):
    return f"{prefix}-{uuid.uuid4().hex}"


def before_request():
    # generate or extract request and correlation ids
    rid = request.headers.get("X-Request-ID") or generate_id("req")
    cid = request.headers.get("X-Correlation-ID") or rid
    REQUEST_ID.set(rid)
    CORRELATION_ID.set(cid)
    START_TIME.set(time.time())

    # user/session info if available
    user = (g.get("user") if hasattr(g, "user") else None) or None
    if user and isinstance(user, dict):
        USER_ID.set(user.get("id"))
        SESSION_ID.set(user.get("session_id"))
    else:
        USER_ID.set(None)
        SESSION_ID.set(None)

    REMOTE_IP.set(request.remote_addr or request.headers.get("X-Forwarded-For"))


def after_request(response):
    logger = get_logger("app.request")
    start = START_TIME.get() or None
    duration = None
    if start:
        duration = round((time.time() - start) * 1000, 2)

    logger.info(
        f"HTTP {request.method} {request.path} {response.status_code}",
        extra={
            "context": {
                "request_id": REQUEST_ID.get(),
                "correlation_id": CORRELATION_ID.get(),
                "method": request.method,
                "endpoint": request.path,
                "status_code": response.status_code,
                "duration_ms": duration,
            }
        },
    )
    return response


def register_middleware(app):
    app.before_request(before_request)
    app.after_request(after_request)
