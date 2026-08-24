import logging
from .config import APP_NAME, ENVIRONMENT, APP_VERSION, LOG_LEVEL, JSON_LOGS
from .formatters import JSONFormatter
from .filters import ContextFilter
from .handlers import make_rotating_file_handler, make_audit_handler
import sys


def configure_logging(app=None):
    # Root logger
    root = logging.getLogger()
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    root.setLevel(level)

    # Avoid duplicate handlers when reconfiguring
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(level)
        if JSON_LOGS:
            sh.setFormatter(_json_formatter())
        root.addHandler(sh)

    # File handler
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers):
        fh = make_rotating_file_handler("app.log", level=level)
        if JSON_LOGS:
            fh.setFormatter(_json_formatter())
        root.addHandler(fh)

    # Attach context filter
    root.addFilter(ContextFilter())


def _json_formatter():
    return logging.Formatter(fmt="%(message)s") if not JSON_LOGS else _JSONAdapter()


class _JSONAdapter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self._fmt = None
        self._inner = JSONFormatter(APP_NAME, ENVIRONMENT, APP_VERSION)

    def format(self, record):
        return self._inner.format(record)


def get_logger(name: str):
    return logging.getLogger(name)


def get_audit_logger():
    logger = logging.getLogger("audit")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = make_audit_handler()
        handler.setFormatter(_JSONAdapter())
        logger.addHandler(handler)
    return logger
