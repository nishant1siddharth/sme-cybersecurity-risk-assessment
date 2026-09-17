from flask import Blueprint, jsonify, render_template


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def home():
    """Render the project foundation home page."""
    return render_template("home.html")


@main_bp.get("/health")
def health_check():
    """Return a machine-readable health check."""
    return jsonify(
        {
            "status": "ok",
            "project": "Cybersecurity Risk Assessment Framework",
        }
    )