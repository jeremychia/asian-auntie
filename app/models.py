from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Notification preferences
    # cooking_days: JSON list of weekday ints (0=Mon … 6=Sun), null = use 3-day fallback
    cooking_days = db.Column(db.Text, nullable=True)
    push_subscription = db.Column(db.Text, nullable=True)  # Web Push subscription JSON
    notifications_enabled = db.Column(db.Boolean, nullable=False, default=False)

    # Onboarding / user profile
    # location: short region code — MY, SG, TH, VN, ID, PH, CN, GB, EU, AU, US, OTHER
    location = db.Column(db.String(16), nullable=True)
    # cuisine_prefs: JSON list of cuisine names e.g. ["Malaysian", "Thai"]
    cuisine_prefs = db.Column(db.Text, nullable=True)
    # household_size: "solo", "2-3", "4-5", "6+"
    household_size = db.Column(db.String(16), nullable=True)
    # gdpr_consent + consent_date: explicit consent record for EU/UK users;
    # set for all users when they complete onboarding (True = agreed)
    gdpr_consent = db.Column(db.Boolean, nullable=True)
    consent_date = db.Column(db.DateTime, nullable=True)
    onboarding_done = db.Column(db.Boolean, nullable=False, default=False)
    # Cuisines outside our current corpus that users want to cook — user research signal
    other_cuisine_requests = db.Column(db.Text, nullable=True)  # JSON list of strings

    items = db.relationship("Item", back_populates="user", lazy="dynamic")
    refresh_tokens = db.relationship(
        "RefreshToken", back_populates="user", lazy="dynamic"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    name = db.Column(db.String(256), nullable=False)
    item_type = db.Column(
        db.String(32),
        nullable=False,
        default="unknown",
        # Valid values: sauce, oil, spice, condiment, produce, dried,
        #               tofu, seafood, dairy, other, unknown
    )
    expiry_date = db.Column(db.Date, nullable=False)

    # Recognition metadata
    confidence_score = db.Column(db.Float, nullable=True)
    cache_hit = db.Column(db.Boolean, nullable=True)

    date_added = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Soft delete — set on removal, null while in inventory
    removed_at = db.Column(db.DateTime, nullable=True)
    removal_reason = db.Column(
        db.String(32), nullable=True
    )  # "used", "discarded", "unwanted"

    user = db.relationship("User", back_populates="items")
    photos = db.relationship(
        "ItemPhoto",
        back_populates="item",
        order_by="ItemPhoto.display_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def is_active(self):
        return self.removed_at is None

    @property
    def has_photo(self):
        return bool(self.photos)

    @property
    def display_photo(self):
        """Best photo for display — prefer appearance type over barcode/label."""
        appearance = [p for p in self.photos if p.photo_type == "appearance"]
        if appearance:
            return appearance[0]
        return self.photos[0] if self.photos else None

    def __repr__(self):
        return f"<Item {self.name} expires={self.expiry_date}>"


class ItemPhoto(db.Model):
    __tablename__ = "item_photos"

    VALID_TYPES = {"barcode", "appearance", "label", "other"}

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("items.id"), nullable=False, index=True
    )
    photo_path = db.Column(db.String(512), nullable=False)
    photo_type = db.Column(db.String(32), nullable=False, default="appearance")
    display_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    item = db.relationship("Item", back_populates="photos")

    def __repr__(self):
        return f"<ItemPhoto {self.photo_type} {self.photo_path[:32]}>"


class RecognitionCache(db.Model):
    __tablename__ = "recognition_cache"

    id = db.Column(db.Integer, primary_key=True)
    image_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    result_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<RecognitionCache {self.image_hash[:16]}>"


class RecipeEngagement(db.Model):
    __tablename__ = "recipe_engagements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    recipe_id = db.Column(db.String(64), nullable=False, index=True)
    feedback = db.Column(db.String(32), nullable=True)  # "yes_made", "not_for_me"
    skip_reason = db.Column(
        db.String(64), nullable=True
    )  # "too_complex", "missing_key_ingredient", "not_my_taste"
    engaged_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship(
        "User", backref=db.backref("recipe_engagements", lazy="dynamic")
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "recipe_id", name="uq_recipe_engagement"),
    )

    def __repr__(self):
        return f"<RecipeEngagement user={self.user_id} recipe={self.recipe_id} feedback={self.feedback}>"


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    token_jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    issued_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken jti={self.token_jti} revoked={self.revoked}>"
