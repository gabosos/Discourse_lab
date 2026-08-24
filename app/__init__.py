from flask import Flask
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "educational-platform-dev"),
        DATABASE_URL=os.environ.get("DATABASE_URL", "sqlite:///educational_platform.db"),
        JSON_SORT_KEYS=False,
    )

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
