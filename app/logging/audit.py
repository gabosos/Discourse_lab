from .logger import get_audit_logger
from datetime import datetime, timezone
import json


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def record_audit(action: str, actor_id=None, resource=None, before=None, after=None, metadata=None, request_id=None, correlation_id=None, ip=None):
    logger = get_audit_logger()
    payload = {
        "timestamp": _now_iso(),
        "action": action,
        "actor_id": actor_id,
        "resource": resource,
        "before": before,
        "after": after,
        "metadata": metadata or {},
        "request_id": request_id,
        "correlation_id": correlation_id,
        "ip": ip,
    }
    logger.info(json.dumps(payload, ensure_ascii=False))
