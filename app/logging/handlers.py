import logging
from logging.handlers import RotatingFileHandler
import os
from .config import LOG_DIR, LOG_MAX_BYTES, LOG_BACKUP_COUNT, AUDIT_LOG_FILE


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def make_rotating_file_handler(filename: str, level=logging.INFO, max_bytes=None, backup_count=None):
    ensure_dir(LOG_DIR)
    path = os.path.join(LOG_DIR, filename)
    handler = RotatingFileHandler(path, maxBytes=max_bytes or LOG_MAX_BYTES, backupCount=backup_count or LOG_BACKUP_COUNT, encoding="utf-8")
    handler.setLevel(level)
    return handler


def make_audit_handler(level=logging.INFO):
    return make_rotating_file_handler(AUDIT_LOG_FILE, level=level)
