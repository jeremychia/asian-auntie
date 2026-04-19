from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, SubmitField, HiddenField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, ValidationError

ITEM_TYPES = [
    ("unknown", "Unknown"),
    ("sauce", "Sauce"),
    ("oil", "Oil"),
    ("spice", "Spice"),
    ("condiment", "Condiment"),
    ("produce", "Produce"),
    ("dried", "Dried goods"),
    ("tofu", "Tofu"),
    ("seafood", "Seafood"),
    ("dairy", "Dairy"),
    ("other", "Other"),
]


class AddItemForm(FlaskForm):
    name = StringField("Item name", validators=[DataRequired(), Length(min=1, max=256)])
    item_type = SelectField("Type", choices=ITEM_TYPES, default="unknown")
    expiry_date = DateField("Expiry date", validators=[DataRequired()])
    photo = FileField(
        "Photo (optional)", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"])]
    )
    photo_paths_json = (
        HiddenField()
    )  # JSON: [{"path": "...", "type": "appearance"}, ...]
    confidence_score = HiddenField()
    cache_hit = HiddenField()
    submit = SubmitField("Save item")

    def validate_expiry_date(self, field):
        today = date.today()
        if field.data < today:
            raise ValidationError("That date has already passed.")
        max_date = today.replace(year=today.year + 2)
        if field.data > max_date:
            raise ValidationError(
                "Expiry date cannot be more than 2 years in the future."
            )
