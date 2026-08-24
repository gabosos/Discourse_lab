import os


def get_env(key: str, default: str = None):
    return os.environ.get(key, default)


LOG_DIR = get_env("LOG_DIR", "logs")
LOG_LEVEL = get_env("LOG_LEVEL", "INFO").upper()
APP_NAME = get_env("APP_NAME", "gramatical_app")
ENVIRONMENT = get_env("APP_ENV", get_env("FLASK_ENV", "development"))
APP_VERSION = get_env("APP_VERSION", "0.0.0")
JSON_LOGS = get_env("JSON_LOGS", "1") in ("1", "true", "True")
LOG_MAX_BYTES = int(get_env("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(get_env("LOG_BACKUP_COUNT", "10"))
AUDIT_LOG_FILE = get_env("AUDIT_LOG_FILE", "audit.log")
