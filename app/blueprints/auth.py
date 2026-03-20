from __future__ import annotations

import logging

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    logger.info("login() called | method=%s", request.method)
    if current_user.is_authenticated:
        logger.info("login() | User already authenticated, redirecting to dashboard")
        return redirect(url_for("dashboard.index"))

    login_error = None
    identity = ""

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        req_hash = getattr(g, "req_hash", "--------")
        logger.info("login() | POST attempt | identity=%s, remember=%s, req_hash=%s", identity, remember, req_hash)

        user = User.query.filter(
            (User.email == identity) | (User.username == identity)
        ).first()

        if not user or not user.check_password(password):
            login_error = "Invalid username/email or password."
            logger.warning("login() | FAILED login attempt | identity=%s | req_hash=%s", identity, req_hash)
        elif user.status != User.STATUS_ACTIVE:
            login_error = "This account is inactive. Please contact the admin."
            logger.warning("login() | Inactive account login attempt | identity=%s, user_id=%s | req_hash=%s", identity, user.id, req_hash)
        else:
            login_user(user, remember=remember)
            logger.info("login() | SUCCESS | user_id=%s, username=%s | req_hash=%s", user.id, user.username, req_hash)
            return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html", login_error=login_error, identity=identity)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    logger.info("forgot_password() called | method=%s", request.method)
    if request.method == "POST":
        logger.info("forgot_password() | POST - password reset flow triggered")
        flash(
            "Password reset flow is prepared. Connect your mail service to send reset links in production.",
            "info",
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    user_id = current_user.id
    username = current_user.username
    req_hash = getattr(g, "req_hash", "--------")
    logout_user()
    logger.info("logout() | User logged out | user_id=%s, username=%s | req_hash=%s", user_id, username, req_hash)
    return redirect(url_for("auth.login"))
