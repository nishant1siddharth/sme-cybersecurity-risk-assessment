import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask


BASE_DIR = Path(__file__).resolve().parent.parent

# Load values from .env when that file exists.
load_dotenv(BASE_DIR / ".env")


def create_app(test_config=None):
    """Create and configure the Phase 1 Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # No password or secret is hard-coded.
    # A value from SECRET_KEY is used when available.
    # Otherwise, a temporary random development key is generated.
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or os.urandom(32),
    )

    # Allow tests or future environments to override configuration.
    if test_config is not None:
        app.config.update(test_config)

    # Ensure the instance directory exists.
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Register application routes.
    from .routes import main_bp

    app.register_blueprint(main_bp)

    return app