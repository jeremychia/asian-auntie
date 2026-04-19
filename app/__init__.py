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

    # Ensure upload and instance folders exist
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
        duration_ms = round((time.monotonic() - g.start_time) * 1000, 1)
        user_id = current_user.id if current_user.is_authenticated else None
        logger.info(
            "request",
            status=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id,
        )
        return response

    # Serve uploaded files
    from flask import send_from_directory
    from flask_login import login_required

    @app.route("/uploads/<path:filename>")
    @login_required
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.perishables.routes import perishables_bp
    from app.api.auth import api_auth_bp
    from app.api.items import api_items_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(perishables_bp)
    app.register_blueprint(api_auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(api_items_bp, url_prefix="/api/v1")

    return app


import structlog  # noqa: E402 — needed after configure_logging
