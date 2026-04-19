from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import db, bcrypt, limiter
from app.models import User, RefreshToken
from app.logging_config import get_logger

api_auth_bp = Blueprint("api_auth", __name__)
logger = get_logger(__name__)


class AuthSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=1, max=64))
    password = fields.Str(required=True, validate=validate.Length(min=8))


auth_schema = AuthSchema()


def _issue_tokens(user: User):
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    # Decode to get jti for storage
    from flask_jwt_extended import decode_token
    decoded = decode_token(refresh_token)
    jti = decoded["jti"]
    expires_at = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    token_record = RefreshToken(
        user_id=user.id,
        token_jti=jti,
        expires_at=expires_at,
    )
    db.session.add(token_record)
    db.session.commit()

    return access_token, refresh_token


@api_auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    try:
        data = auth_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    username = data["username"].strip()
    if not username:
        return jsonify({"error": "Username is required."}), 422

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "That username is already in use."}), 409

    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    user = User(username=username, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    logger.info("api_register_success", user_id=user.id)
    return jsonify({"user_id": user.id}), 201


@api_auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    try:
        data = auth_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    user = User.query.filter_by(username=data["username"].strip()).first()
    # Always run bcrypt check to prevent timing attacks
    if user and bcrypt.check_password_hash(user.password_hash, data["password"]):
        access_token, refresh_token = _issue_tokens(user)
        logger.info("api_login_success", user_id=user.id)
        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200

    logger.warning("api_login_failed", username=data.get("username"))
    # Generic error — never reveal which field is wrong
    return jsonify({"error": "Invalid username or password."}), 401


@api_auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    jwt_data = get_jwt()
    jti = jwt_data["jti"]

    token_record = RefreshToken.query.filter_by(token_jti=jti).first()
    if not token_record or token_record.revoked:
        return jsonify({"error": "Refresh token is invalid or has been revoked."}), 401

    # Rotate: revoke old, issue new
    token_record.revoked = True
    db.session.commit()

    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 401

    access_token, new_refresh_token = _issue_tokens(user)
    logger.info("api_token_refreshed", user_id=user_id)
    return jsonify({"access_token": access_token, "refresh_token": new_refresh_token}), 200


@api_auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    jti = get_jwt()["jti"]
    token_record = RefreshToken.query.filter_by(token_jti=jti).first()
    if token_record:
        token_record.revoked = True
        db.session.commit()

    user_id = get_jwt_identity()
    logger.info("api_logout", user_id=user_id)
    return jsonify({"message": "Logged out successfully."}), 200
