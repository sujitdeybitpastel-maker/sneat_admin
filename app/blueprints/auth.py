from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User


bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    login_error = None
    identity = ""

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.email == identity) | (User.username == identity)
        ).first()

        if not user or not user.check_password(password):
            login_error = "Invalid username/email or password."
        elif user.status != User.STATUS_ACTIVE:
            login_error = "This account is inactive. Please contact the admin."
        else:
            login_user(user, remember=remember)
            return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html", login_error=login_error, identity=identity)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash(
            "Password reset flow is prepared. Connect your mail service to send reset links in production.",
            "info",
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
