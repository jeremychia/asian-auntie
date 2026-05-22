import logging
import os
import secrets
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

    # Database — rewrite postgres(ql):// to use psycopg3 dialect; Neon/Render
    # supply postgresql:// which SQLAlchemy maps to psycopg2 by default
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Rate limiting
    RATELIMIT_DEFAULT = "1000 per day;500 per hour"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # File uploads — local fallback used when GCS_BUCKET_NAME is not set
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max upload

    # Google Cloud Storage (production photo storage)
    GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "")
    # Service account key JSON string; leave unset to use Application Default Credentials
    GCS_CREDENTIALS_JSON = os.environ.get("GCS_CREDENTIALS_JSON", "")

    # CORS — comma-separated origins from env, fallback to localhost
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5000").split(
        ","
    )

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # Web Push (VAPID) — generate your own keys with py_vapid for production
    VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
    VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "admin@asian-auntie.app")

    # Open Food Facts contribution (optional — only needed to contribute data back)
    OFF_USERNAME = os.environ.get("OFF_USERNAME", "")
    OFF_PASSWORD = os.environ.get("OFF_PASSWORD", "")
    OFF_API_URL = os.environ.get("OFF_API_URL", "https://world.openfoodfacts.org")

    # Session cookies — Secure flag is added by ProductionConfig only (requires HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def validate(cls):
        critical = ["FLASK_SECRET_KEY", "JWT_SECRET_KEY"]
        missing_critical = [k for k in critical if not os.environ.get(k)]
        if missing_critical:
            raise RuntimeError(
                f"Missing required env vars for production: {missing_critical}"
            )

        optional = {
            "VAPID_PRIVATE_KEY": "web push notifications",
            "VAPID_PUBLIC_KEY": "web push notifications",
        }
        _logger = logging.getLogger(__name__)
        for key, service in optional.items():
            if not os.environ.get(key):
                _logger.warning("%s is not set — %s will be unavailable", key, service)


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "production")
    cfg = config_by_name.get(env)
    if cfg is None:
        raise RuntimeError(
            f"Unknown FLASK_ENV={env!r}. Must be one of: {list(config_by_name)}"
        )
    if hasattr(cfg, "validate"):
        cfg.validate()
    return cfg
