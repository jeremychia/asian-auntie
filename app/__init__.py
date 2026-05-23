import os
import time
from flask import Flask, g, request
from flask_login import current_user

from config import get_config
from app.extensions import db, login_manager, bcrypt, jwt, limiter, cors, migrate, csrf
from app.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


def create_app():
    configure_logging()

    root = os.path.dirname(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(root, "templates"),
        static_folder=os.path.join(root, "static"),
        instance_relative_config=True,
    )
    app.config.from_object(get_config())

    # Create local upload folder only when GCS is not configured
    if not app.config.get("GCS_BUCKET_NAME"):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app, resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGINS"]}}
    )
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Flask-Login config
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for

        next_url = request.args.get("next") or request.referrer
        if next_url:
            return redirect(url_for("auth.login", next=next_url))
        return redirect(url_for("auth.login"))

    # JWT token revocation check
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # Access tokens expire naturally (15 min) and are not stored in the DB.
        # Only refresh tokens need server-side revocation checking.
        if jwt_payload.get("type") != "refresh":
            return False
        from app.models import RefreshToken

        jti = jwt_payload.get("jti")
        token = db.session.query(RefreshToken).filter_by(token_jti=jti).first()
        if token is None:
            return True  # Unknown refresh token — treat as revoked
        return token.revoked

    # Request logging
    @app.before_request
    def before_request():
        g.start_time = time.monotonic()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.path,
        )

    @app.after_request
    def after_request(response):
        duration_ms = None
        if hasattr(g, "start_time"):
            duration_ms = round((time.monotonic() - g.start_time) * 1000, 1)
        user_id = current_user.id if current_user.is_authenticated else None
        logger.info(
            "request",
            status=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(self)"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "img-src 'self' https://storage.googleapis.com data:; "
            "connect-src 'self'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "frame-ancestors 'none';"
        )
        if not app.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    from flask import abort, send_from_directory
    from flask_login import login_required

    @app.route("/photo/<int:photo_id>")
    @login_required
    def serve_photo(photo_id):
        from app.models import ItemPhoto

        photo = db.session.get(ItemPhoto, photo_id)
        if not photo or photo.item.user_id != current_user.id:
            abort(403)

        bucket_name = app.config.get("GCS_BUCKET_NAME")
        if bucket_name:
            from flask import Response
            from app.storage import download_photo

            # New-style: photo_path is the object name.
            # Legacy: photo_path was the full public URL — extract object name.
            path = photo.photo_path
            prefix = f"https://storage.googleapis.com/{bucket_name}/"
            if path.startswith(prefix):
                path = path[len(prefix) :]
            if not path.startswith("https://"):
                try:
                    data = download_photo(
                        path,
                        bucket_name,
                        app.config.get("GCS_CREDENTIALS_JSON"),
                    )
                    resp = Response(data, content_type="image/jpeg")
                    resp.headers["Cache-Control"] = "private, max-age=604800"
                    return resp
                except Exception:
                    pass  # fall through to local file serving

        # External URLs stored as fallback when barcode-image download failed at
        # add-time (e.g. images.openfoodfacts.org).  Proxy them so the browser
        # never sees the origin URL, keeping auth intact.
        _ALLOWED_PHOTO_HOSTS = (
            "images.openfoodfacts.org",
            "images.openfoodfacts.net",
            "static.openfoodfacts.org",
        )
        if photo.photo_path.startswith("https://"):
            from urllib.parse import urlparse as _urlparse
            import urllib.request as _urlrequest
            from flask import Response

            parsed = _urlparse(photo.photo_path)
            if parsed.scheme != "https" or parsed.netloc not in _ALLOWED_PHOTO_HOSTS:
                abort(404)
            try:
                req = _urlrequest.Request(
                    photo.photo_path,
                    headers={"User-Agent": "AsianAuntie/1.0 (jeremyjchia@gmail.com)"},
                )
                with _urlrequest.urlopen(req, timeout=10) as r:
                    data = r.read()
                    ct = r.headers.get("Content-Type", "image/jpeg")
                flask_resp = Response(data, content_type=ct)
                flask_resp.headers["Cache-Control"] = "private, max-age=604800"
                return flask_resp
            except Exception:
                abort(404)

        resp = send_from_directory(app.config["UPLOAD_FOLDER"], photo.photo_path)
        resp.headers["Cache-Control"] = "private, max-age=604800"
        return resp

    # Serves photos during the confirm step (before the item is saved to DB).
    # Supports both local-disk and GCS storage to match _save_photo_bytes.
    @app.route("/uploads/<path:filename>")
    @login_required
    def uploaded_file(filename):
        from flask import Response

        expected_prefix = f"users/{current_user.id}/"
        if not filename.startswith(expected_prefix):
            abort(403)

        bucket_name = app.config.get("GCS_BUCKET_NAME")
        if bucket_name:
            from app.storage import download_photo

            try:
                data = download_photo(
                    filename,
                    bucket_name,
                    app.config.get("GCS_CREDENTIALS_JSON") or None,
                )
                resp = Response(data, content_type="image/jpeg")
                resp.headers["Cache-Control"] = "private, max-age=604800"
                return resp
            except Exception:
                abort(404)

        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Register blueprints
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.perishables.routes import perishables_bp
    from app.recipes.routes import recipes_bp
    from app.api.auth import api_auth_bp
    from app.api.items import api_items_bp
    from app.notifications import notifications_bp
    from app.onboarding import onboarding_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(perishables_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(api_auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(api_items_bp, url_prefix="/api/v1")
    app.register_blueprint(notifications_bp)
    app.register_blueprint(onboarding_bp)

    @app.context_processor
    def inject_vapid_public_key():
        return {"vapid_public_key": app.config.get("VAPID_PUBLIC_KEY", "")}

    _css_path = os.path.join(root, "static", "style.css")

    @app.context_processor
    def inject_css_version():
        return {"css_version": int(os.path.getmtime(_css_path))}

    # Start notification scheduler (skip in testing / flask db commands)
    if not app.config.get("TESTING") and os.environ.get("FLASK_RUN_MAIN") != "false":
        from app.notifications.scheduler import start_scheduler

        start_scheduler(app)

    return app


import structlog  # noqa: E402 — needed after configure_logging
