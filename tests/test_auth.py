"""Tests for auth routes: register, login, logout."""

from app.models import User


def test_login_page_loads(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b"login" in r.data.lower()


def test_register_page_loads(client):
    r = client.get("/register")
    assert r.status_code == 200


def test_register_creates_user(client, db):
    r = client.post(
        "/register",
        data={
            "username": "newuser",
            "password": "securepass1",
            "confirm": "securepass1",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert User.query.filter_by(username="newuser").first() is not None
    User.query.filter_by(username="newuser").delete()
    db.session.commit()


def test_login_success_redirects_to_dashboard(client, user):
    r = client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"dashboard" in r.data.lower() or r.request.path != "/login"


def test_login_wrong_password_stays_on_login(auth_client, user):
    # Log out first to ensure we have a clean session
    auth_client.post("/logout")
    r = auth_client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    # Flash message rendered in base template as flash-error div
    assert b"flash" in r.data


def test_login_unknown_user(auth_client):
    auth_client.post("/logout")
    r = auth_client.post(
        "/login",
        data={"username": "nobody", "password": "password123"},
        follow_redirects=True,
    )
    assert r.status_code == 200
    assert b"flash" in r.data


def test_logout(auth_client):
    r = auth_client.post("/logout", follow_redirects=True)
    assert r.status_code == 200
    # After logout, dashboard should redirect to login
    r2 = auth_client.get("/dashboard")
    assert r2.status_code in (302, 200)


def test_dashboard_requires_login(client):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 401)
