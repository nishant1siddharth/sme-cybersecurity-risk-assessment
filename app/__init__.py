import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .extensions import db


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)


def environment_boolean(
    name,
    default=False,
):
    """Read a boolean environment variable safely."""
    value = os.environ.get(
        name,
        str(default),
    ).strip().lower()

    return value in {
        "1",
        "true",
        "yes",
        "on",
    }


def create_app(test_config=None):
    """Create and configure the Flask application."""

    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    default_database_path = (
        Path(app.instance_path)
        / "database.db"
    )

    app.config.from_mapping(

        SECRET_KEY=(
            os.environ.get("SECRET_KEY")
            or os.urandom(32)
        ),

        SQLALCHEMY_DATABASE_URI=(
            f"sqlite:///{default_database_path.as_posix()}"
        ),

        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        DATABASE_PATH=str(
            default_database_path
        ),

        SESSION_COOKIE_HTTPONLY=True,

        SESSION_COOKIE_SAMESITE="Lax",

        SESSION_COOKIE_SECURE=environment_boolean(
            "SESSION_COOKIE_SECURE",
            default=False,
        ),

        PERMANENT_SESSION_LIFETIME=timedelta(
            hours=1
        ),
    )

    if test_config is not None:
        app.config.update(
            test_config
        )

    Path(
        app.instance_path
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    db.init_app(app)

    from . import models  # noqa: F401
    from .auth import auth_bp
    from .routes import main_bp

    app.register_blueprint(
        main_bp
    )

    app.register_blueprint(
        auth_bp
    )

    return app