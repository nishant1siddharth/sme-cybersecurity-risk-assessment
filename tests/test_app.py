from app import create_app


def test_home_page_loads():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Project foundation is running." in response.data


def test_health_endpoint():
    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    assert response.get_json() == {
        "status": "ok",
        "project": "Cybersecurity Risk Assessment Framework",
    }