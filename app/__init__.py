from flask import Flask
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app_env = os.environ.get("APP_ENV", "development").lower()
    secret_key = os.environ.get("SECRET_KEY")
    if app_env == "production" and not secret_key:
        raise RuntimeError("SECRET_KEY debe configurarse como variable secreta en producción.")
    app.config.from_mapping(
        SECRET_KEY=secret_key or "development-only-change-me",
        DATABASE_URL=os.environ.get("DATABASE_URL", "sqlite:///data/educational_platform.db"),
        JSON_SORT_KEYS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=app_env == "production",
    )
    # Render and similar hosts terminate HTTPS at a proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure centralized logging system (structured, JSON, rotation, context)
    from app.logging.logger import configure_logging
    from app.logging.middleware import register_middleware

    configure_logging(app)
    register_middleware(app)

    from app.interfaces.routes import register_routes
    register_routes(app)

    from app.infrastructure.database import init_db
    with app.app_context():
        init_db()

    return app
