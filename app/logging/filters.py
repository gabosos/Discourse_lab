import contextvars
from datetime import datetime, timezone

# Context variables to carry request-scoped values into logs
REQUEST_ID = contextvars.ContextVar("request_id", default=None)
CORRELATION_ID = contextvars.ContextVar("correlation_id", default=None)
USER_ID = contextvars.ContextVar("user_id", default=None)
SESSION_ID = contextvars.ContextVar("session_id", default=None)
REMOTE_IP = contextvars.ContextVar("remote_ip", default=None)
START_TIME = contextvars.ContextVar("start_time", default=None)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class ContextFilter:
    """Logging filter that injects request/session context into log records."""

    def filter(self, record):
        context = {
            "request_id": REQUEST_ID.get(),
            "correlation_id": CORRELATION_ID.get(),
            "user_id": USER_ID.get(),
            "session_id": SESSION_ID.get(),
            "ip": REMOTE_IP.get(),
            "timestamp_utc": now_iso(),
        }
        # Attach to record so formatters can pick it up
        record.context = context
        return True
