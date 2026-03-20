from __future__ import annotations

import logging
from functools import wraps
from io import BytesIO

from flask import Blueprint, abort, g, jsonify, make_response, render_template, request, send_file
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.services.excel import build_workbook

logger = logging.getLogger(__name__)

bp = Blueprint("users", __name__, url_prefix="/users")


def _get_hash() -> str:
    return getattr(g, "req_hash", "--------")


def _validation_error(message: str, field_errors: dict[str, str] | None = None, status_code: int = 400):
    req_hash = _get_hash()
    logger.warning("Validation error | message=%s | field_errors=%s | status=%d | req_hash=%s", message, field_errors, status_code, req_hash)
    return jsonify({"message": message, "field_errors": field_errors or {}, "req_hash": req_hash}), status_code


def _validate_password_change(
    user: User,
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> dict[str, str]:
    logger.debug("_validate_password_change() | user_id=%s", user.id)
    field_errors: dict[str, str] = {}

    if not current_password:
        field_errors["current-password"] = "Current password is required."
    elif not user.check_password(current_password):
        field_errors["current-password"] = "Current password is incorrect."

    if not new_password:
        field_errors["new-password"] = "New password is required."
    elif len(new_password) < 8:
        field_errors["new-password"] = "New password must be at least 8 characters."
    elif current_password and current_password == new_password:
        field_errors["new-password"] = "New password must be different from the current password."

    if not confirm_password:
        field_errors["confirm-password"] = "Please retype the new password."
    elif new_password != confirm_password:
        field_errors["confirm-password"] = "Password confirmation does not match."

    if field_errors:
        logger.warning("_validate_password_change() | Validation failed | errors=%s", list(field_errors.keys()))
    else:
        logger.debug("_validate_password_change() | Validation passed")
    return field_errors


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.role != User.ROLE_ADMIN:
            logger.warning("admin_required() | Access denied | user_id=%s, role=%s, endpoint=%s", current_user.id, current_user.role, request.endpoint)
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _user_from_payload(user: User | None = None) -> User:
    payload = request.get_json() or {}
    logger.debug("_user_from_payload() | is_update=%s | payload_keys=%s", user is not None, list(payload.keys()))
    instance = user or User()

    full_name = payload.get("full_name", "")
    username = payload.get("username", "")
    email = payload.get("email", "")
    role = payload.get("role", "")
    status = payload.get("status", "")

    if not full_name or not username or not email or not role or not status:
        raise ValueError(("All fields are required.", {"full_name": "This field is required."}))

    instance.full_name = str(full_name).strip()
    instance.username = str(username).strip()
    instance.email = str(email).strip().lower()
    instance.role = str(role).strip()
    instance.status = str(status).strip()

    if not User.is_valid_role(instance.role):
        raise ValueError(("Please choose a valid role.", {"role": "Please choose a valid role."}))
    if not User.is_valid_status(instance.status):
        raise ValueError(("Please choose a valid status.", {"status": "Please choose a valid status."}))

    if payload.get("password"):
        instance.set_password(payload["password"])
    elif user is None:
        instance.set_password("ChangeMe123")

    logger.debug("_user_from_payload() | Built user | username=%s, email=%s", instance.username, instance.email)
    return instance


def _validate_user_uniqueness(user: User, existing_user_id: int | None = None) -> dict[str, str]:
    logger.debug("_validate_user_uniqueness() | username=%s, email=%s, existing_id=%s", user.username, user.email, existing_user_id)
    field_errors: dict[str, str] = {}

    username_query = User.query.filter(User.username == user.username)
    email_query = User.query.filter(User.email == user.email)
    if existing_user_id is not None:
        username_query = username_query.filter(User.id != existing_user_id)
        email_query = email_query.filter(User.id != existing_user_id)

    if username_query.first():
        field_errors["username"] = "This username is already in use."
    if email_query.first():
        field_errors["email"] = "This email is already in use."

    if field_errors:
        logger.warning("_validate_user_uniqueness() | Duplicates found | errors=%s", field_errors)
    return field_errors


def _selected_ids() -> list[int]:
    raw_ids = request.args.get("ids", "").strip()
    if not raw_ids:
        return []
    values: list[int] = []
    for part in raw_ids.split(","):
        part = part.strip()
        if part.isdigit():
            values.append(int(part))
    logger.debug("_selected_ids() | parsed ids=%s", values)
    return values


@bp.route("")
@login_required
@admin_required
def page():
    logger.info("page() | Users page requested | user_id=%s", current_user.id)
    return render_template(
        "users/index.html",
        role_choices=User.ROLE_CHOICES,
        status_choices=User.STATUS_CHOICES,
    )


@bp.route("/profile")
@login_required
def profile():
    logger.info("profile() | Profile page requested | user_id=%s", current_user.id)
    return render_template("users/profile.html")


@bp.route("/api", methods=["GET"])
@login_required
@admin_required
def list_users():
    search = request.args.get("search", "").strip().lower()
    logger.info("list_users() | search=%s | user_id=%s", search or "(none)", current_user.id)
    try:
        rows = [user.to_dict() for user in User.query.order_by(User.created_at.desc()).all()]
        if search:
            rows = [row for row in rows if search in " ".join(str(v).lower() for v in row.values())]
        logger.info("list_users() | Returned %d users", len(rows))
        return jsonify(rows)
    except Exception:
        logger.exception("list_users() | ERROR")
        return jsonify({"message": "Failed to fetch users.", "req_hash": _get_hash()}), 500


@bp.route("/api", methods=["POST"])
@login_required
@admin_required
def create_user():
    logger.info("create_user() | Creating new user | admin_id=%s", current_user.id)
    try:
        user = _user_from_payload()
    except ValueError as error:
        message, field_errors = error.args[0] if error.args else ("Invalid data.", {})
        logger.warning("create_user() | Validation error | message=%s", message)
        return _validation_error(message, field_errors)

    field_errors = _validate_user_uniqueness(user)
    if field_errors:
        return _validation_error("Please correct the highlighted fields.", field_errors)
    try:
        db.session.add(user)
        db.session.commit()
        logger.info("create_user() | SUCCESS | user_id=%s, username=%s", user.id, user.username)
    except IntegrityError:
        db.session.rollback()
        logger.warning("create_user() | IntegrityError | username=%s, email=%s", user.username, user.email)
        return _validation_error(
            "Username and email must be unique.",
            {"username": "Username must be unique.", "email": "Email must be unique."},
        )
    return jsonify(user.to_dict()), 201


@bp.route("/api/<int:user_id>", methods=["PUT"])
@login_required
@admin_required
def update_user(user_id: int):
    logger.info("update_user() | user_id=%d | admin_id=%s", user_id, current_user.id)
    user = User.query.get_or_404(user_id)
    try:
        _user_from_payload(user)
    except ValueError as error:
        message, field_errors = error.args[0] if error.args else ("Invalid data.", {})
        logger.warning("update_user() | Validation error | user_id=%d | message=%s", user_id, message)
        return _validation_error(message, field_errors)

    field_errors = _validate_user_uniqueness(user, existing_user_id=user.id)
    if field_errors:
        return _validation_error("Please correct the highlighted fields.", field_errors)
    try:
        db.session.commit()
        logger.info("update_user() | SUCCESS | user_id=%d, username=%s", user.id, user.username)
    except IntegrityError:
        db.session.rollback()
        logger.warning("update_user() | IntegrityError | user_id=%d", user_id)
        return _validation_error(
            "Username and email must be unique.",
            {"username": "Username must be unique.", "email": "Email must be unique."},
        )
    return jsonify(user.to_dict())


@bp.route("/api/<int:user_id>/status", methods=["PATCH"])
@login_required
@admin_required
def toggle_user_status(user_id: int):
    logger.info("toggle_user_status() | user_id=%d | admin_id=%s", user_id, current_user.id)
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            logger.warning("toggle_user_status() | Admin tried to deactivate self | user_id=%d", user_id)
            return jsonify({"message": "You cannot deactivate the current admin session.", "req_hash": _get_hash()}), 400
        old_status = user.status
        user.status = User.STATUS_INACTIVE if user.status == User.STATUS_ACTIVE else User.STATUS_ACTIVE
        db.session.commit()
        logger.info("toggle_user_status() | SUCCESS | user_id=%d | status: %s -> %s", user_id, old_status, user.status)
        return jsonify(user.to_dict())
    except Exception:
        db.session.rollback()
        logger.exception("toggle_user_status() | ERROR | user_id=%d", user_id)
        return jsonify({"message": "Failed to toggle user status.", "req_hash": _get_hash()}), 500


@bp.route("/api/export", methods=["GET"])
@login_required
@admin_required
def export_users():
    logger.info("export_users() | admin_id=%s", current_user.id)
    try:
        selected_ids = _selected_ids()
        query = User.query.order_by(User.created_at.desc())
        if selected_ids:
            query = query.filter(User.id.in_(selected_ids))

        rows = [["ID", "Full Name", "Username", "Email", "Role", "Status", "Created At", "Updated At"]]
        for user in query.all():
            rows.append([
                user.id, user.full_name, user.username, user.email,
                user.role_label, user.status_label,
                user.created_at.strftime("%d %b %Y"),
                user.updated_at.strftime("%d %b %Y") if user.updated_at else "-",
            ])

        workbook = build_workbook([("Users", rows)])
        logger.info("export_users() | SUCCESS | exported %d users", len(rows) - 1)
        return send_file(
            BytesIO(workbook),
            as_attachment=True,
            download_name="users_export.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        logger.exception("export_users() | ERROR during export")
        return jsonify({"message": "Failed to export users.", "req_hash": _get_hash()}), 500


@bp.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    logger.info("get_profile() | user_id=%s", current_user.id)
    return jsonify(current_user.to_dict())


@bp.route("/api/profile", methods=["PATCH"])
@login_required
def update_profile():
    logger.info("update_profile() | user_id=%s", current_user.id)
    try:
        payload = request.get_json() or {}

        full_name = payload.get("full_name", "")
        username = payload.get("username", "")
        email = payload.get("email", "")

        if not full_name or not username or not email:
            return _validation_error("All profile fields are required.")

        current_user.full_name = str(full_name).strip()
        current_user.username = str(username).strip()
        current_user.email = str(email).strip().lower()

        field_errors = _validate_user_uniqueness(current_user, existing_user_id=current_user.id)
        if field_errors:
            return _validation_error("Please correct the highlighted fields.", field_errors)

        try:
            db.session.commit()
            logger.info("update_profile() | SUCCESS | user_id=%s", current_user.id)
        except IntegrityError:
            db.session.rollback()
            logger.warning("update_profile() | IntegrityError | user_id=%s", current_user.id)
            return _validation_error(
                "Username and email must be unique.",
                {"username": "Username must be unique.", "email": "Email must be unique."},
            )
        return jsonify(current_user.to_dict())
    except Exception:
        db.session.rollback()
        logger.exception("update_profile() | ERROR | user_id=%s", current_user.id)
        return jsonify({"message": "Failed to update profile.", "req_hash": _get_hash()}), 500


@bp.route("/api/profile/password", methods=["PATCH"])
@login_required
def update_password():
    logger.info("update_password() | user_id=%s", current_user.id)
    try:
        payload = request.get_json() or {}
        current_password = payload.get("current_password", "")
        new_password = payload.get("new_password", "")
        confirm_password = payload.get("confirm_password", "")

        field_errors = _validate_password_change(
            current_user,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )
        if field_errors:
            return _validation_error("Please correct the highlighted password fields.", field_errors)

        current_user.set_password(new_password)
        db.session.commit()
        logger.info("update_password() | SUCCESS | user_id=%s", current_user.id)
        return jsonify({"message": "Password updated successfully."})
    except Exception:
        db.session.rollback()
        logger.exception("update_password() | ERROR | user_id=%s", current_user.id)
        return jsonify({"message": "Failed to update password.", "req_hash": _get_hash()}), 500


@bp.route("/theme", methods=["POST"])
@login_required
def set_theme():
    logger.info("set_theme() | user_id=%s", current_user.id)
    payload = request.get_json() or {}
    theme_mode = payload.get("theme_mode", "system")
    if theme_mode not in {"light", "dark", "system"}:
        logger.warning("set_theme() | Invalid theme_mode=%s", theme_mode)
        return jsonify({"message": "Unsupported theme mode.", "req_hash": _get_hash()}), 400

    response = make_response(jsonify({"theme_mode": theme_mode}))
    response.set_cookie("theme_mode", theme_mode, max_age=60 * 60 * 24 * 365, samesite="Lax")
    logger.info("set_theme() | SUCCESS | theme_mode=%s", theme_mode)
    return response
