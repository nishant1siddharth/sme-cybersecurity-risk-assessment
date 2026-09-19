import re

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "phase-3-test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "DATABASE_PATH": ":memory:",
            "SESSION_COOKIE_SECURE": False,
        }
    )

    with application.app_context():

        db.create_all()

        assessor = User(
            username="test_assessor",
            password_hash=generate_password_hash(
                "CorrectPassword123!"
            ),
            role="assessor",
        )

        admin = User(
            username="test_admin",
            password_hash=generate_password_hash(
                "AdminPassword123!"
            ),
            role="admin",
        )

        db.session.add_all(
            [
                assessor,
                admin,
            ]
        )

        db.session.commit()

        yield application

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def extract_csrf_token(response):
    """Extract the hidden CSRF token from an HTML response."""
    match = re.search(
        rb'name="csrf_token"\s+value="([^"]+)"',
        response.data,
    )

    assert match is not None

    return match.group(1).decode()


def login(client, username, password):
    """Log in through the actual login form."""
    response = client.get("/auth/login")

    token = extract_csrf_token(response)

    return client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": token,
        },
        follow_redirects=False,
    )


def test_valid_login_creates_session_and_allows_protected_route(client):
    response = login(
        client,
        "test_assessor",
        "CorrectPassword123!",
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/protected"
    )

    with client.session_transaction() as session:
        assert session["user_id"] is not None

    protected_response = client.get(
        "/auth/protected"
    )

    assert protected_response.status_code == 200
    assert b"Authentication successful" in protected_response.data
    assert b"test_assessor" in protected_response.data


def test_wrong_password_fails_with_generic_error(client):
    response = login(
        client,
        "test_assessor",
        "WrongPassword123!",
    )

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_nonexistent_username_fails_with_generic_error(client):
    response = login(
        client,
        "does_not_exist",
        "AnyPassword123!",
    )

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data


def test_empty_username_is_rejected(client):
    response = client.get("/auth/login")

    token = extract_csrf_token(response)

    login_response = client.post(
        "/auth/login",
        data={
            "username": "",
            "password": "AnyPassword123!",
            "csrf_token": token,
        },
    )

    assert login_response.status_code == 200
    assert b"Username is required." in login_response.data


def test_empty_password_is_rejected(client):
    response = client.get("/auth/login")

    token = extract_csrf_token(response)

    login_response = client.post(
        "/auth/login",
        data={
            "username": "test_assessor",
            "password": "",
            "csrf_token": token,
        },
    )

    assert login_response.status_code == 200
    assert b"Password is required." in login_response.data


def test_unauthenticated_user_is_redirected_from_protected_route(client):
    response = client.get(
        "/auth/protected"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/login"
    )


def test_logout_clears_session_and_blocks_protected_route(client):
    login_response = login(
        client,
        "test_assessor",
        "CorrectPassword123!",
    )

    assert login_response.status_code == 302

    protected_response = client.get(
        "/auth/protected"
    )

    csrf_token = extract_csrf_token(
        protected_response
    )

    logout_response = client.post(
        "/auth/logout",
        data={
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert logout_response.status_code == 302
    assert logout_response.headers["Location"].endswith(
        "/auth/login"
    )

    with client.session_transaction() as session:
        assert "user_id" not in session

    blocked_response = client.get(
        "/auth/protected"
    )

    assert blocked_response.status_code == 302
    assert blocked_response.headers["Location"].endswith(
        "/auth/login"
    )


def test_assessor_cannot_access_admin_route(client):
    response = login(
        client,
        "test_assessor",
        "CorrectPassword123!",
    )

    assert response.status_code == 302

    admin_response = client.get(
        "/auth/admin"
    )

    assert admin_response.status_code == 403
    assert b"Access denied" in admin_response.data


def test_admin_can_access_admin_route(client):
    response = login(
        client,
        "test_admin",
        "AdminPassword123!",
    )

    assert response.status_code == 302

    admin_response = client.get(
        "/auth/admin"
    )

    assert admin_response.status_code == 200
    assert b"Administrator-only area" in admin_response.data


def test_missing_csrf_token_rejects_login(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "test_assessor",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 400
    assert b"Invalid request" in response.data