import os
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Database — rewrite postgres(ql):// to use psycopg3 dialect; Neon/Render
    # supply postgresql:// which SQLAlchemy maps to psycopg2 by default
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
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
    VAPID_PRIVATE_KEY = os.environ.get(
        "VAPID_PRIVATE_KEY",
        "-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgZxc1+xhanvM0lNTT\nUEsuid/qEtNYikJvykLdFHVxV0mhRANCAAR5j+/eL/K2r0x+eBbQ6fd6MemCUlLb\nuOJPxE18VSHpa+9cQcOaa7b++Ed+ijufyB1d+tSsardyGPiNgIs//lr4\n-----END PRIVATE KEY-----\n",
    )
    VAPID_PUBLIC_KEY = os.environ.get(
        "VAPID_PUBLIC_KEY",
        "BHmP794v8ravTH54FtDp93ox6YJSUtu44k_ETXxVIelr71xBw5prtv74R36KO5_IHV361Kxqt3IY-I2Aiz_-Wvg",
    )
    VAPID_CLAIMS_EMAIL = os.environ.get("VAPID_CLAIMS_EMAIL", "admin@asian-auntie.app")

    # Open Food Facts contribution (optional — only needed to contribute data back)
    OFF_USERNAME = os.environ.get("OFF_USERNAME", "")
    OFF_PASSWORD = os.environ.get("OFF_PASSWORD", "")
    OFF_API_URL = os.environ.get("OFF_API_URL", "https://world.openfoodfacts.org")

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # Enforce secure cookies in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
