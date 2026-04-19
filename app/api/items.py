from datetime import date, datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, validates, ValidationError

from app.extensions import db
from app.models import Item, User
from app.recognition.service import recognize_item
from app.logging_config import get_logger

api_items_bp = Blueprint("api_items", __name__)
logger = get_logger(__name__)

VALID_ITEM_TYPES = {
    "sauce",
    "oil",
    "spice",
    "condiment",
    "produce",
    "dried",
    "tofu",
    "seafood",
    "dairy",
    "other",
    "unknown",
}


class ItemCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=256))
    expiry_date = fields.Date(required=True)
    item_type = fields.Str(load_default="unknown")

    @validates("item_type")
    def validate_item_type(self, value):
        if value not in VALID_ITEM_TYPES:
            raise ValidationError(
                f"item_type must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}"
            )

    @validates("expiry_date")
    def validate_expiry_date(self, value):
        today = date.today()
        if value < today:
            raise ValidationError("Expiry date cannot be in the past.")
        max_date = today.replace(year=today.year + 2)
        if value > max_date:
            raise ValidationError(
                "Expiry date cannot be more than 2 years in the future."
            )


class ItemUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=256))
    expiry_date = fields.Date()
    item_type = fields.Str()

    @validates("item_type")
    def validate_item_type(self, value):
        if value not in VALID_ITEM_TYPES:
            raise ValidationError(
                f"item_type must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}"
            )


item_create_schema = ItemCreateSchema()
item_update_schema = ItemUpdateSchema()


def _item_to_dict(item: Item) -> dict:
    display = item.display_photo
    return {
        "id": item.id,
        "name": item.name,
        "item_type": item.item_type,
        "expiry_date": item.expiry_date.isoformat(),
        "has_photo": item.has_photo,
        "photo_url": f"/uploads/{display.photo_path}" if display else None,
        "photos": [
            {"url": f"/uploads/{p.photo_path}", "type": p.photo_type}
            for p in item.photos
        ],
        "confidence_score": item.confidence_score,
        "date_added": item.date_added.isoformat(),
    }


def _get_current_user() -> User:
    return db.session.get(User, int(get_jwt_identity()))


@api_items_bp.route("/items", methods=["GET"])
@jwt_required()
def list_items():
    user = _get_current_user()
    items = (
        Item.query.filter_by(user_id=user.id)
        .filter(Item.removed_at.is_(None))
        .order_by(Item.expiry_date.asc())
        .all()
    )
    return jsonify({"items": [_item_to_dict(i) for i in items]}), 200


@api_items_bp.route("/items", methods=["POST"])
@jwt_required()
def create_item():
    user = _get_current_user()

    try:
        data = item_create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    item = Item(
        user_id=user.id,
        name=data["name"].strip(),
        item_type=data["item_type"],
        expiry_date=data["expiry_date"],
    )
    db.session.add(item)
    db.session.commit()

    logger.info(
        "api_item_created", user_id=user.id, item_id=item.id, item_name=item.name
    )
    return jsonify(_item_to_dict(item)), 201


@api_items_bp.route("/items/<int:item_id>", methods=["GET"])
@jwt_required()
def get_item(item_id):
    user = _get_current_user()
    item = (
        Item.query.filter_by(id=item_id, user_id=user.id)
        .filter(Item.removed_at.is_(None))
        .first()
    )
    if not item:
        return jsonify({"error": "Not found."}), 404
    return jsonify(_item_to_dict(item)), 200


@api_items_bp.route("/items/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update_item(item_id):
    user = _get_current_user()
    item = (
        Item.query.filter_by(id=item_id, user_id=user.id)
        .filter(Item.removed_at.is_(None))
        .first()
    )
    if not item:
        return jsonify({"error": "Not found."}), 404

    try:
        data = item_update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    if "name" in data:
        item.name = data["name"].strip()
    if "expiry_date" in data:
        item.expiry_date = data["expiry_date"]
    if "item_type" in data:
        item.item_type = data["item_type"]

    db.session.commit()
    logger.info("api_item_updated", user_id=user.id, item_id=item.id)
    return jsonify(_item_to_dict(item)), 200


@api_items_bp.route("/items/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_item(item_id):
    user = _get_current_user()
    item = (
        Item.query.filter_by(id=item_id, user_id=user.id)
        .filter(Item.removed_at.is_(None))
        .first()
    )
    if not item:
        return jsonify({"error": "Not found."}), 404

    item.removed_at = datetime.now(timezone.utc)
    item.removal_reason = (
        request.get_json(silent=True, force=True).get("reason", "used")
        if request.data
        else "used"
    )
    db.session.commit()

    logger.info(
        "api_item_deleted", user_id=user.id, item_id=item.id, reason=item.removal_reason
    )
    return jsonify({"message": "Item removed."}), 200


@api_items_bp.route("/items/recognize", methods=["POST"])
@jwt_required()
def recognize():
    if "photo" not in request.files:
        return jsonify({"error": "No photo provided."}), 422

    photo = request.files["photo"]
    image_bytes = photo.read()
    if not image_bytes:
        return jsonify({"error": "Photo is empty."}), 422

    result = recognize_item(image_bytes)
    logger.info(
        "api_recognize",
        user_id=get_jwt_identity(),
        confidence=result.confidence,
        cache_hit=result.cache_hit,
        item_name=result.name,
    )
    return (
        jsonify(
            {
                "name": result.name,
                "item_type": result.item_type,
                "confidence": result.confidence,
                "shelf_life_days": result.shelf_life_days,
                "printed_expiry_date": (
                    result.printed_expiry_date.isoformat()
                    if result.printed_expiry_date
                    else None
                ),
                "cache_hit": result.cache_hit,
            }
        ),
        200,
    )
