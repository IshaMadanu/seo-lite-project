from unittest.mock import MagicMock

import pytest

import dynamo
import app as app_module

TEST_EMAIL = "jane.doe@example.com"
TEST_PASSWORD = "password123"


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(dynamo, "create_tables", lambda resource=None: MagicMock())
    monkeypatch.setattr(dynamo, "create_user", lambda db, email, pswd, name=None: None)
    monkeypatch.setattr(dynamo, "seed_nonprofits", lambda db, data: None)
    monkeypatch.setattr(
        dynamo, "verify_user",
        lambda db, email, pswd: email == TEST_EMAIL and pswd == TEST_PASSWORD,
    )
    monkeypatch.setattr(dynamo, "get_user", lambda db, email: {"name": "Jane Doe"})
    monkeypatch.setattr(dynamo, "get_co2_saved", lambda db, email: 4.2)
    monkeypatch.setattr(dynamo, "get_interests", lambda db, email: [])
    monkeypatch.setattr(dynamo, "set_interests", lambda db, email, interests: None)
    monkeypatch.setattr(dynamo, "get_nonprofits_by_category", lambda db, category: [])
    monkeypatch.setattr(dynamo, "add_co2_saved", lambda db, email, amount: None)

    flask_app = app_module.create_app(resource=MagicMock())
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client):
    return client.post(
        "/login", data={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )


def test_login_page_renders_form(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b'name="email"' in resp.data
    assert b'name="password"' in resp.data


def test_successful_login_redirects_to_profile(client):
    resp = _login(client)
    assert resp.status_code == 302
    assert "/profile" in resp.headers["Location"]


def test_profile_requires_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"] or resp.headers["Location"] == "/"


def test_profile_renders_user_name_and_co2(client):
    _login(client)
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"Jane Doe" in resp.data
    assert b"4.20 kg" in resp.data


def test_recommendations_shows_empty_state_when_no_interests(client):
    _login(client)
    resp = client.get("/recommendations")
    assert resp.status_code == 200
    assert b"No preferences saved" in resp.data


def test_route_page_shows_placeholder_without_destination(client):
    _login(client)
    resp = client.get("/route")
    assert resp.status_code == 200
    assert b"No nonprofit selected" in resp.data