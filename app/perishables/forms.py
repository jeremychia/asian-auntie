from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, SubmitField, HiddenField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, ValidationError

PANTRY_ITEMS = [
    "Fish sauce",
    "Light soy sauce",
    "Dark soy sauce",
    "Oyster sauce",
    "Hoisin sauce",
    "Sweet soy sauce",
    "Kecap manis",
    "Sesame oil",
    "Chilli oil",
    "Coconut milk",
    "Coconut cream",
    "Rice vinegar",
    "Black vinegar",
    "Chinkiang vinegar",
    "Mirin",
    "Sake",
    "Shaoxing wine",
    "Miso paste",
    "White miso",
    "Red miso",
    "Gochujang",
    "Doenjang",
    "Sambal oelek",
    "Sriracha",
    "XO sauce",
    "Doubanjiang",
    "Chilli bean paste",
    "Black bean sauce",
    "Char siu sauce",
    "Plum sauce",
    "Sweet chilli sauce",
    "Teriyaki sauce",
    "Ponzu",
    "Maggi seasoning",
    "Shrimp paste",
    "Belacan",
    "Tamarind paste",
    "Laksa paste",
    "Pad Thai sauce",
    "Coconut sugar",
    "Palm sugar",
    "Rock sugar",
    "Condensed milk",
    "Evaporated milk",
    "Pandan extract",
    "Gochugaru",
    "Five spice powder",
    "Curry powder",
    "Turmeric powder",
    "White pepper",
    "Sichuan peppercorn",
    "Star anise",
    "Dried chillies",
    "Chilli flakes",
    "Togarashi",
    "Lemongrass paste",
    "Galangal powder",
    "Dashi powder",
    "Agar agar",
    "Jasmine rice",
    "Glutinous rice",
    "Brown rice",
    "Rice flour",
    "Tapioca starch",
    "Cornstarch",
    "Potato starch",
    "Panko breadcrumbs",
    "Rice noodles",
    "Glass noodles",
    "Egg noodles",
    "Udon noodles",
    "Soba noodles",
    "Instant noodles",
    "Wonton wrappers",
    "Spring roll wrappers",
    "Dumpling wrappers",
    "Silken tofu",
    "Firm tofu",
    "Tofu puffs",
    "Dried shiitake mushrooms",
    "Wood ear mushrooms",
    "Dried shrimp",
    "Dried scallops",
    "Fermented black beans",
    "Lily buds",
    "Bean curd skin",
    "Dried red dates",
    "Kombu",
    "Nori",
    "Wakame",
    "Bonito flakes",
    "Dashi stock",
    "Fish balls",
    "Fish cakes",
    "Lap cheong",
    "Water chestnuts",
    "Bamboo shoots",
    "Baby corn",
    "Sesame seeds",
    "Black sesame seeds",
]

LOCATIONS = [
    ("", "Not specified"),
    ("fridge", "Fridge"),
    ("freezer", "Freezer"),
    ("pantry", "Pantry"),
    ("cupboard", "Cupboard"),
    ("counter", "Counter"),
]

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
    location = SelectField("Location", choices=LOCATIONS, default="")
    expiry_date = DateField("Expiry date", validators=[DataRequired()])
    photo = FileField(
        "Photo (optional)", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"])]
    )
    standard_name = HiddenField()  # canonical pantry name for recipe matching
    barcode = HiddenField()
    photo_paths_json = (
        HiddenField()
    )  # JSON: [{"path": "...", "type": "appearance"}, ...]
    confidence_score = HiddenField()
    cache_hit = HiddenField()
    source = HiddenField()  # "barcode", "photo", or "manual"
    submit = SubmitField("Save item")

    def validate_expiry_date(self, field):
        today = date.today()
        if field.data < today:
            raise ValidationError("That date has already passed.")
        max_date = today.replace(year=today.year + 5)
        if field.data > max_date:
            raise ValidationError(
                "Expiry date cannot be more than 5 years in the future."
            )
