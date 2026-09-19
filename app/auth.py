import secrets
from functools import wraps
from hmac import compare_digest

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from .extensions import db
from .models import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
)


def get_csrf_token():
    """Return the current session CSRF token, creating one when needed."""
    token = session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token

    return token


def validate_csrf_token(form_token):
    """Validate a CSRF token supplied by a form."""
    session_token = session.get("csrf_token")

    if not session_token or not form_token:
        return False

    return compare_digest(
        session_token,
        form_token,
    )


def login_required(view):
    """Allow access only to authenticated users."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view


def role_required(required_role):
    """Allow access only to authenticated users with a required role."""

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = g.get("user")

            if user is None:
                return redirect(url_for("auth.login"))

            if user.role != required_role:
                return render_template(
                    "error.html",
                    title="Access denied",
                    message=(
                        "You do not have permission to access this page."
                    ),
                    status_code=403,
                ), 403

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


@auth_bp.before_app_request
def load_logged_in_user():
    """Load the logged-in user from the session before each request."""
    user_id = session.get("user_id")

    g.user = None

    if user_id is not None:
        user = db.session.get(User, user_id)

        if user is None:
            session.clear()
        else:
            g.user = user


@auth_bp.app_context_processor
def inject_auth_context():
    """Make authentication data and CSRF helper available to templates."""
    return {
        "current_user": g.get("user"),
        "csrf_token": get_csrf_token,
    }


@auth_bp.route("/login", methods=("GET", "POST"))
def login():
    """Authenticate a user and create a secure Flask session."""
    error = None

    if request.method == "POST":

        if not validate_csrf_token(
            request.form.get("csrf_token")
        ):
            return render_template(
                "login.html",
                error="Invalid request. Please try again.",
            ), 400

        username = request.form.get(
            "username",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        if not username:
            error = "Username is required."

        elif not password:
            error = "Password is required."

        else:
            user = db.session.execute(
                db.select(User).where(
                    User.username == username
                )
            ).scalar_one_or_none()

            password_is_valid = False

            if user is not None and user.password_hash:
                password_is_valid = check_password_hash(
                    user.password_hash,
                    password,
                )
            else:
                # Perform a harmless hash verification even when
                # the username does not exist, reducing obvious
                # username-enumeration differences.
                check_password_hash(
                    "scrypt:32768:8:1$invalidsalt$invalidhash",
                    password,
                )

            if not user or not user.password_hash or not password_is_valid:
                error = "Invalid username or password."

            else:
                # Clear any previous session state before creating
                # the authenticated session.
                session.clear()

                session.permanent = True

                session["user_id"] = user.id

                flash(
                    "Login successful.",
                    "success",
                )

                return redirect(
                    url_for("auth.protected")
                )

    return render_template(
        "login.html",
        error=error,
    )


@auth_bp.post("/logout")
@login_required
def logout():
    """Log the current user out and destroy the session."""
    if not validate_csrf_token(
        request.form.get("csrf_token")
    ):
        return render_template(
            "error.html",
            title="Invalid request",
            message="Your request could not be verified.",
            status_code=400,
        ), 400

    session.clear()

    flash(
        "You have been logged out.",
        "success",
    )

    return redirect(
        url_for("auth.login")
    )


@auth_bp.get("/protected")
@login_required
def protected():
    """Simple authenticated page used to verify Phase 3."""
    return render_template(
        "protected.html"
    )


@auth_bp.get("/admin")
@role_required("admin")
def admin_only():
    """Simple admin-only page used to verify authorization."""
    return render_template(
        "admin_only.html"
    )