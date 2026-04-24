from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, bcrypt
from app.models import User
from app.auth.forms import LoginForm, RegisterForm
from app.logging_config import get_logger

auth_bp = Blueprint("auth", __name__)
logger = get_logger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("perishables.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            logger.info("login_success", user_id=user.id)
            if not user.onboarding_done:
                return redirect(url_for("onboarding.index"))
            next_page = request.args.get("next")
            return redirect(next_page or url_for("perishables.dashboard"))
        else:
            # Generic error — never reveal which field is wrong
            logger.warning("login_failed", username=form.username.data)
            flash("Invalid username or password.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("perishables.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password_hash = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(username=username, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        logger.info("register_success", user_id=user.id)
        return redirect(url_for("onboarding.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logger.info("logout", user_id=current_user.id)
    logout_user()
    return redirect(url_for("auth.landing"))
