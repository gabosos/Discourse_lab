import json
from datetime import datetime, timezone


def iso_utc_now():
    return datetime.now(timezone.utc).isoformat()


class JSONFormatter:
    def __init__(self, service_name: str, app_env: str, app_version: str):
        self.service_name = service_name
        self.app_env = app_env
        self.app_version = app_version

    def format(self, record):
        payload = {
            "timestamp": iso_utc_now(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "service": self.service_name,
            "environment": self.app_env,
            "version": self.app_version,
            "module": getattr(record, "module", None),
            "funcName": getattr(record, "funcName", None),
        }

        # Include any contextual fields added by filters
        context_fields = getattr(record, "context", {}) or {}
        payload.update(context_fields)

        # Include exception info if present
        if record.exc_info:
            try:
                import traceback

                payload["error"] = "\n".join(traceback.format_exception(*record.exc_info))
            except Exception:
                payload["error"] = str(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)
