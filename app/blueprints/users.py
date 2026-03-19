from __future__ import annotations

from functools import wraps
from io import BytesIO

from flask import Blueprint, abort, jsonify, make_response, render_template, request, send_file
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.services.excel import build_workbook


bp = Blueprint("users", __name__, url_prefix="/users")


def _validation_error(message: str, field_errors: dict[str, str] | None = None, status_code: int = 400):
    return jsonify({"message": message, "field_errors": field_errors or {}}), status_code


def _validate_password_change(
    user: User,
    current_password: str,
    new_password: str,
    confirm_password: str,
) -> dict[str, str]:
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

    return field_errors


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user.role != User.ROLE_ADMIN:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _user_from_payload(user: User | None = None) -> User:
    payload = request.get_json() or {}
    instance = user or User()
    instance.full_name = payload["full_name"].strip()
    instance.username = payload["username"].strip()
    instance.email = payload["email"].strip().lower()
    instance.role = str(payload["role"]).strip()
    instance.status = str(payload["status"]).strip()

    if not User.is_valid_role(instance.role):
        raise ValueError(("Please choose a valid role.", {"role": "Please choose a valid role."}))
    if not User.is_valid_status(instance.status):
        raise ValueError(("Please choose a valid status.", {"status": "Please choose a valid status."}))

    if payload.get("password"):
        instance.set_password(payload["password"])
    elif user is None:
        instance.set_password("ChangeMe123")
    return instance


def _validate_user_uniqueness(user: User, existing_user_id: int | None = None) -> dict[str, str]:
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
    return values


@bp.route("")
@login_required
@admin_required
def page():
    return render_template(
        "users/index.html",
        role_choices=User.ROLE_CHOICES,
        status_choices=User.STATUS_CHOICES,
    )


@bp.route("/profile")
@login_required
def profile():
    return render_template("users/profile.html")


@bp.route("/api", methods=["GET"])
@login_required
@admin_required
def list_users():
    search = request.args.get("search", "").strip().lower()
    rows = [user.to_dict() for user in User.query.order_by(User.created_at.desc()).all()]
    if search:
        rows = [row for row in rows if search in " ".join(str(v).lower() for v in row.values())]
    return jsonify(rows)


@bp.route("/api", methods=["POST"])
@login_required
@admin_required
def create_user():
    try:
        user = _user_from_payload()
    except ValueError as error:
        message, field_errors = error.args[0] if error.args else ("Invalid data.", {})
        return _validation_error(message, field_errors)

    field_errors = _validate_user_uniqueness(user)
    if field_errors:
        return _validation_error("Please correct the highlighted fields.", field_errors)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _validation_error(
            "Username and email must be unique.",
            {"username": "Username must be unique.", "email": "Email must be unique."},
        )
    return jsonify(user.to_dict()), 201


@bp.route("/api/<int:user_id>", methods=["PUT"])
@login_required
@admin_required
def update_user(user_id: int):
    user = User.query.get_or_404(user_id)
    try:
        _user_from_payload(user)
    except ValueError as error:
        message, field_errors = error.args[0] if error.args else ("Invalid data.", {})
        return _validation_error(message, field_errors)

    field_errors = _validate_user_uniqueness(user, existing_user_id=user.id)
    if field_errors:
        return _validation_error("Please correct the highlighted fields.", field_errors)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _validation_error(
            "Username and email must be unique.",
            {"username": "Username must be unique.", "email": "Email must be unique."},
        )
    return jsonify(user.to_dict())


@bp.route("/api/<int:user_id>/status", methods=["PATCH"])
@login_required
@admin_required
def toggle_user_status(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({"message": "You cannot deactivate the current admin session."}), 400
    user.status = User.STATUS_INACTIVE if user.status == User.STATUS_ACTIVE else User.STATUS_ACTIVE
    db.session.commit()
    return jsonify(user.to_dict())


@bp.route("/api/export", methods=["GET"])
@login_required
@admin_required
def export_users():
    selected_ids = _selected_ids()
    query = User.query.order_by(User.created_at.desc())
    if selected_ids:
        query = query.filter(User.id.in_(selected_ids))

    rows = [
        [
            "ID",
            "Full Name",
            "Username",
            "Email",
            "Role",
            "Status",
            "Created At",
            "Updated At",
        ]
    ]

    for user in query.all():
        rows.append(
            [
                user.id,
                user.full_name,
                user.username,
                user.email,
                user.role_label,
                user.status_label,
                user.created_at.strftime("%d %b %Y"),
                user.updated_at.strftime("%d %b %Y") if user.updated_at else "-",
            ]
        )

    workbook = build_workbook([("Users", rows)])
    return send_file(
        BytesIO(workbook),
        as_attachment=True,
        download_name="users_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    return jsonify(current_user.to_dict())


@bp.route("/api/profile", methods=["PATCH"])
@login_required
def update_profile():
    payload = request.get_json() or {}
    current_user.full_name = payload["full_name"].strip()
    current_user.username = payload["username"].strip()
    current_user.email = payload["email"].strip().lower()

    field_errors = _validate_user_uniqueness(current_user, existing_user_id=current_user.id)
    if field_errors:
        return _validation_error("Please correct the highlighted fields.", field_errors)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _validation_error(
            "Username and email must be unique.",
            {"username": "Username must be unique.", "email": "Email must be unique."},
        )
    return jsonify(current_user.to_dict())


@bp.route("/api/profile/password", methods=["PATCH"])
@login_required
def update_password():
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
    return jsonify({"message": "Password updated successfully."})


@bp.route("/theme", methods=["POST"])
@login_required
def set_theme():
    payload = request.get_json() or {}
    theme_mode = payload.get("theme_mode", "system")
    if theme_mode not in {"light", "dark", "system"}:
        return jsonify({"message": "Unsupported theme mode."}), 400

    response = make_response(jsonify({"theme_mode": theme_mode}))
    response.set_cookie("theme_mode", theme_mode, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response
