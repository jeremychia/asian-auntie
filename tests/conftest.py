import os
import pytest

os.environ["TESTING"] = "1"
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key-for-testing-only!!")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-bytes-min!!")
os.environ.setdefault("WTF_CSRF_ENABLED", "False")
# Must be set before create_app() so the SQLAlchemy engine is built with the
# in-memory URI. Updating app.config after the engine is created has no effect.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db as _db, limiter


@pytest.fixture(scope="session")
def app():
    _app = create_app()
    _app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        # StaticPool makes all connections (test session + Flask requests) share
        # the single in-memory database so test-committed changes are visible
        # inside request handlers without a separate connection.
        SQLALCHEMY_ENGINE_OPTIONS={
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
    )
    limiter.enabled = False
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    # Push a fresh inner app context so each test gets its own Flask g.
    # Without this, Flask's g (which stores g._login_user) is shared across
    # all requests within the outer session-scope app context, causing
    # stale login state to bleed between tests.
    ctx = app.app_context()
    ctx.push()
    yield _db
    _db.session.rollback()
    ctx.pop()


@pytest.fixture
def user(db):
    from app.models import User, Item, RefreshToken
    from app.extensions import bcrypt

    # Clean up any leftover state from a previous failed test
    existing = User.query.filter_by(username="testuser").first()
    if existing:
        from app.models import RecipeEngagement

        RefreshToken.query.filter_by(user_id=existing.id).delete()
        Item.query.filter_by(user_id=existing.id).delete()
        RecipeEngagement.query.filter_by(user_id=existing.id).delete()
        db.session.delete(existing)
        db.session.commit()

    u = User(
        username="testuser",
        password_hash=bcrypt.generate_password_hash("password123").decode(),
        onboarding_done=True,
    )
    db.session.add(u)
    db.session.commit()
    yield u
    try:
        u_fresh = db.session.get(User, u.id)
        if u_fresh:
            from app.models import RecipeEngagement

            RefreshToken.query.filter_by(user_id=u_fresh.id).delete()
            Item.query.filter_by(user_id=u_fresh.id).delete()
            RecipeEngagement.query.filter_by(user_id=u_fresh.id).delete()
            db.session.delete(u_fresh)
            db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def auth_client(client, user):
    client.post(
        "/login",
        data={"username": "testuser", "password": "password123"},
        follow_redirects=True,
    )
    yield client
