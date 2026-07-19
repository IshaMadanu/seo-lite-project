import boto3
import pytest
from moto import mock_aws

import app as app_module


@pytest.fixture
def client():
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        app = app_module.create_app(resource)
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client


def login(client, email="jane.doe@example.com", password="password123"):
    return client.post(
        "/login", data={"email": email, "password": password}
    )


def test_login_page_renders(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Log in" in resp.data


def test_login_success_redirects_to_profile(client):
    resp = login(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_login_wrong_password(client):
    resp = login(client, password="nope")
    assert resp.status_code == 200
    assert b"Invalid login" in resp.data


def test_login_unknown_user(client):
    resp = login(client, email="nobody@example.com")
    assert b"Invalid login" in resp.data


def test_protected_pages_redirect_when_logged_out(client):
    for page in ("/profile", "/recommendations", "/route"):
        resp = client.get(page)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/login")


def test_profile_shows_user_from_db(client):
    login(client)
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"Jane Doe" in resp.data
    assert b"jane.doe@example.com" in resp.data


def test_save_preferences_persists_and_prechecks(client):
    login(client)
    resp = client.post(
        "/profile", data={"interest": ["animals", "education"]}
    )
    assert resp.status_code == 200
    assert b"Preferences saved." in resp.data

    html = client.get("/profile").get_data(as_text=True)
    assert 'value="animals"\n               checked' in html
    assert 'value="education"\n               checked' in html
    assert 'value="environment"\n               checked' not in html


def test_save_preferences_ignores_unknown_values(client):
    login(client)
    client.post("/profile", data={"interest": ["animals", "hacking"]})
    html = client.get("/recommendations").get_data(as_text=True)
    assert "animals" in html
    assert "hacking" not in html


def test_recommendations_reflect_saved_interests(client):
    login(client)
    client.post("/profile", data={"interest": ["environment"]})
    resp = client.get("/recommendations")
    assert b"Matches: environment" in resp.data
    assert b"Matches: animals" not in resp.data


def test_recommendations_empty_state(client):
    login(client)
    resp = client.get("/recommendations")
    assert b"No preferences saved yet" in resp.data


def test_logout_clears_session(client):
    login(client)
    client.get("/logout")
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_preferences_are_per_user(client):
    login(client)
    client.post("/profile", data={"interest": ["animals"]})
    client.get("/logout")

    app_module.dynamo.create_user(
        client.application.config["DYNAMO"],
        "sam@example.com", "pw2", name="Sam",
    )
    login(client, email="sam@example.com", password="pw2")
    resp = client.get("/recommendations")
    assert b"Matches: animals" not in resp.data
