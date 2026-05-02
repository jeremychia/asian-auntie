from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, SubmitField, HiddenField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, ValidationError

PANTRY_ITEMS = [
    "Agar agar",
    "Baby corn",
    "Bamboo shoots",
    "Bean curd skin",
    "Belacan",
    "Black bean sauce",
    "Black sesame seeds",
    "Black vinegar",
    "Bonito flakes",
    "Brown rice",
    "Char siu sauce",
    "Chilli bean paste",
    "Chilli flakes",
    "Chilli oil",
    "Chinkiang vinegar",
    "Coconut cream",
    "Coconut milk",
    "Coconut sugar",
    "Desiccated coconut",
    "Grated coconut",
    "Toasted coconut",
    "Condensed milk",
    "Cornstarch",
    "Curry powder",
    "Dark soy sauce",
    "Dashi powder",
    "Dashi stock",
    "Doenjang",
    "Doubanjiang",
    "Dried chillies",
    "Dried red dates",
    "Dried scallops",
    "Dried shiitake mushrooms",
    "Dried shrimp",
    "Dumpling wrappers",
    "Egg noodles",
    "Evaporated milk",
    "Fermented black beans",
    "Firm tofu",
    "Fish balls",
    "Fish cakes",
    "Fish sauce",
    "Five spice powder",
    "Galangal powder",
    "Glass noodles",
    "Glutinous rice",
    "Gochugaru",
    "Gochujang",
    "Hoisin sauce",
    "Instant noodles",
    "Jasmine rice",
    "Kecap manis",
    "Kombu",
    "Laksa paste",
    "Lap cheong",
    "Lemongrass paste",
    "Light soy sauce",
    "Lily buds",
    "Maggi seasoning",
    "Mirin",
    "Miso paste",
    "Nori",
    "Oyster sauce",
    "Pad Thai sauce",
    "Palm sugar",
    "Pandan extract",
    "Panko breadcrumbs",
    "Plum sauce",
    "Ponzu",
    "Potato starch",
    "Red miso",
    "Rice flour",
    "Rice noodles",
    "Rice vinegar",
    "Rock sugar",
    "Sake",
    "Sambal oelek",
    "Sesame oil",
    "Sesame seeds",
    "Shaoxing wine",
    "Shrimp paste",
    "Sichuan peppercorn",
    "Silken tofu",
    "Soba noodles",
    "Spring roll wrappers",
    "Sriracha",
    "Star anise",
    "Sweet chilli sauce",
    "Sweet soy sauce",
    "Tamarind paste",
    "Tapioca starch",
    "Teriyaki sauce",
    "Tofu puffs",
    "Togarashi",
    "Turmeric powder",
    "Udon noodles",
    "Wakame",
    "Water chestnuts",
    "White miso",
    "White pepper",
    "Wonton wrappers",
    "Wood ear mushrooms",
    "XO sauce",
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
    standard_name = StringField(
        "Standard ingredient name", validators=[Length(max=256)]
    )
    item_type = SelectField("Type", choices=ITEM_TYPES, default="unknown")
    location = StringField("Location", validators=[Length(max=32)])
    expiry_date = DateField("Expiry date", validators=[DataRequired()])
    photo = FileField(
        "Photo (optional)", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"])]
    )
    barcode = StringField("Barcode (optional)", validators=[Length(max=64)])
    photo_paths_json = (
        HiddenField()
    )  # JSON: [{"path": "...", "type": "appearance"}, ...]
    confidence_score = HiddenField()
    cache_hit = HiddenField()
    source = HiddenField()  # "barcode", "photo", or "manual"

    # Product detail fields — passed through hidden fields from barcode lookup
    brands = HiddenField()
    quantity = HiddenField()
    ingredients_text = HiddenField()
    labels_tags = HiddenField()  # JSON list
    product_data_source = HiddenField()  # "off" or "ocr"
    off_nutriscore_grade = HiddenField()
    off_nutriscore_score = HiddenField()
    off_nova_group = HiddenField()
    off_ecoscore_grade = HiddenField()
    off_ecoscore_score = HiddenField()
    off_categories_tags = HiddenField()  # JSON list
    off_allergens_tags = HiddenField()  # JSON list
    off_packaging_tags = HiddenField()  # JSON list
    off_data_quality_tags = HiddenField()  # JSON list

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
