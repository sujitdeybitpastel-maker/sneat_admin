from __future__ import annotations

from io import BytesIO
import json

from flask import Blueprint, jsonify, render_template, request, send_file
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Product, ProductUpdate, TradeRecord, User
from app.services.excel import build_workbook
import logging

logger = logging.getLogger(__name__)
bp = Blueprint("products", __name__, url_prefix="/products")


def _validation_error(message: str, field_errors: dict[str, str] | None = None, status_code: int = 400):
    return jsonify({"message": message, "field_errors": field_errors or {}}), status_code


def _can_manage_main_products() -> bool:
    return current_user.role in {User.ROLE_ADMIN, User.ROLE_MANAGER}


def _can_manage_product_updates() -> bool:
    return current_user.role in {User.ROLE_ADMIN, User.ROLE_SUPERVISOR, User.ROLE_MANAGER}


def _sync_product_status(product: Product, next_effective_quantity: int | None = None) -> None:
    effective_quantity = product.effective_quantity if next_effective_quantity is None else max(next_effective_quantity, 0)
    if product.status == Product.STATUS_DELETED:
        return
    product.status = Product.STATUS_ACTIVE if effective_quantity > 0 else Product.STATUS_INACTIVE


def _validate_product_payload(payload: dict) -> dict[str, str]:
    field_errors: dict[str, str] = {}

    if not payload.get("sku", "").strip():
        field_errors["sku"] = "SKU is required."
    if len(payload.get("sku", "").strip()) < 4:
        field_errors["sku"] = "SKU must be at least 4 characters."
    if len(payload.get("name", "").strip()) < 3:
        field_errors["name"] = "Product name must be at least 3 characters."
    if len(payload.get("category", "").strip()) < 2:
        field_errors["category"] = "Category must be at least 2 characters."
    if len(payload.get("origin_country", "").strip()) < 2:
        field_errors["origin_country"] = "Origin country must be at least 2 characters."
    if len(payload.get("destination_country", "").strip()) < 2:
        field_errors["destination_country"] = "Destination country must be at least 2 characters."

    try:
        unit_price = float(payload.get("unit_price", 0))
        if unit_price <= 0:
            field_errors["unit_price"] = "Unit price must be greater than 0."
    except (TypeError, ValueError):
        field_errors["unit_price"] = "Unit price must be a valid number."

    try:
        quantity = int(payload.get("quantity", 0))
        if quantity < 0:
            field_errors["quantity"] = "Quantity must be a non-negative whole number."
    except (TypeError, ValueError):
        field_errors["quantity"] = "Quantity must be a non-negative whole number."

    return field_errors


def _product_from_payload(payload: dict, product: Product | None = None) -> Product:
    instance = product or Product(created_by_id=current_user.id, updated_by_id=current_user.id)
    instance.sku = payload.get("sku", "").strip()
    instance.name = payload.get("name", "").strip()
    instance.category = payload.get("category", "").strip()
    instance.unit_price = float(payload.get("unit_price", 0))
    instance.quantity = int(payload.get("quantity", 0))
    instance.origin_country = payload.get("origin_country", "").strip()
    instance.destination_country = payload.get("destination_country", "").strip()
    instance.updated_by_id = current_user.id
    _sync_product_status(instance, next_effective_quantity=instance.quantity + instance.supervisor_quantity_delta)
    return instance


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
def page():
    section = request.args.get("section", "main")
    if section not in {"main", "supervisor"}:
        section = "main"
    return render_template("products/index.html", active_product_section=section)


@bp.route("/api", methods=["GET"])
@login_required
def list_products():
    rows = [row.to_dict() for row in Product.query.order_by(Product.updated_at.desc(), Product.created_at.desc()).all()]
    return jsonify(rows)


@bp.route("/api", methods=["POST"])
@login_required
def create_product():
    try:
        if not _can_manage_main_products():
            return _validation_error("Only roles 2 and 4 can add products.", status_code=403)

        payload = request.get_json() or {}
        field_errors = _validate_product_payload(payload)
        if field_errors:
            return _validation_error("Please correct the highlighted fields.", field_errors)

        product = _product_from_payload(payload)
        if Product.query.filter_by(sku=product.sku).first():
            return _validation_error("Please correct the highlighted fields.", {"sku": "This SKU is already in use."})

        try:
            db.session.add(product)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return _validation_error("SKU must be unique.", {"sku": "SKU must be unique."})

        return jsonify(product.to_dict()), 201
    except Exception:
        logger.exception("Error in Create Product data:")


@bp.route("/api/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id: int):
    if not _can_manage_main_products():
        return _validation_error("Only roles Admin and Maneger can edit products.", status_code=403)

    payload = request.get_json() or {}
    field_errors = _validate_product_payload(payload)
    if field_errors:
        return _validation_error("Please correct the highlighted fields.", field_errors)

    product = Product.query.get_or_404(product_id)
    _product_from_payload(payload, product)

    with db.session.no_autoflush:
        existing = Product.query.filter(Product.sku == product.sku, Product.id != product.id).first()
        if existing:
            return _validation_error("Please correct the highlighted fields.", {"sku": "This SKU is already in use."})

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _validation_error("SKU must be unique.", {"sku": "SKU must be unique."})

    return jsonify(product.to_dict())


@bp.route("/api/<int:product_id>/status", methods=["PATCH"])
@login_required
def toggle_product_status(product_id: int):
    if not _can_manage_main_products():
        return _validation_error("Only roles 2 and 4 can change product status.", status_code=403)

    product = Product.query.get_or_404(product_id)
    target_status = Product.STATUS_INACTIVE if product.status == Product.STATUS_ACTIVE else Product.STATUS_ACTIVE
    if target_status == Product.STATUS_ACTIVE and product.effective_quantity <= 0:
        product.status = Product.STATUS_INACTIVE
    else:
        product.status = target_status
    product.updated_by_id = current_user.id
    db.session.commit()
    return jsonify(product.to_dict())


@bp.route("/api/supervisor/updates", methods=["GET"])
@login_required
def list_supervisor_updates():
    if not _can_manage_product_updates():
        return _validation_error("You do not have permission to view product updates.", status_code=403)

    rows = [row.to_dict() for row in ProductUpdate.query.order_by(ProductUpdate.created_at.desc()).all()]
    return jsonify(rows)


@bp.route("/api/supervisor/updates", methods=["POST"])
@login_required
def create_supervisor_update():
    if not _can_manage_product_updates():
        return _validation_error("You do not have permission to update product quantity here.", status_code=403)

    payload = request.get_json() or {}
    
    print("Received supervisor update payload:", payload)
    product_id = payload.get("product_id")
    remarks = str(payload.get("remarks", "")).strip()

    if not product_id:
        return _validation_error("Please select a product.", {"supervisor-product-id": "Please select a product."})

    product = Product.query.get_or_404(int(product_id))

    try:
        quantity_delta = int(payload.get("quantity_delta", 0))
    except (TypeError, ValueError):
        return _validation_error(
            "Please correct the highlighted fields.",
            {"supervisor-quantity-delta": "Quantity change must be a whole number."},
        )

    if quantity_delta == 0:
        return _validation_error(
            "Please correct the highlighted fields.",
            {"supervisor-quantity-delta": "Quantity change cannot be zero."},
        )

    
    next_effective_quantity = product.quantity + product.supervisor_quantity_delta + quantity_delta
    print(f"Calculated next effective quantity: {next_effective_quantity} (base: {product.quantity}, current delta: {product.supervisor_quantity_delta}, change: {quantity_delta})")
    update = ProductUpdate(
        product_id=product.id,
        updated_by_id=current_user.id,
        changes={
            "quantity_delta": quantity_delta,
            "result_quantity": max(next_effective_quantity, 0),
        },
        remarks=remarks or None,
    )

    product.updated_by_id = current_user.id
    _sync_product_status(product, next_effective_quantity=next_effective_quantity)

    db.session.add(update)
    db.session.commit()
    return jsonify(update.to_dict()), 201


@bp.route("/api/<int:product_id>/updates", methods=["GET"])
@login_required
def product_updates(product_id: int):
    product = Product.query.get_or_404(product_id)
    updates = ProductUpdate.query.filter_by(product_id=product.id).order_by(ProductUpdate.created_at.desc()).all()
    return jsonify(
        {
            "product": product.to_dict(),
            "updates": [update.to_dict() for update in updates],
        }
    )


@bp.route("/api/export", methods=["GET"])
@login_required
def export_products():
    selected_ids = _selected_ids()
    products_query = Product.query.order_by(Product.updated_at.desc(), Product.created_at.desc())
    updates_query = ProductUpdate.query.order_by(ProductUpdate.created_at.desc())

    if selected_ids:
        products_query = products_query.filter(Product.id.in_(selected_ids))
        updates_query = updates_query.filter(ProductUpdate.product_id.in_(selected_ids))

    product_rows = [
        [
            "ID",
            "SKU",
            "Product",
            "Category",
            "Unit Price",
            "Quantity",
            "Base Quantity",
            "Supervisor Quantity Delta",
            "Origin Country",
            "Destination Country",
            "Status",
            "Created By",
            "Updated By",
            "Created At",
            "Updated At",
        ]
    ]
    for product in products_query.all():
        data = product.to_dict()
        product_rows.append(
            [
                data["id"],
                data["sku"],
                data["name"],
                data["category"],
                data["unit_price"],
                data["quantity"],
                data["base_quantity"],
                data["supervisor_quantity_delta"],
                data["origin_country"],
                data["destination_country"],
                data["status"],
                data["created_by"],
                data["updated_by"],
                data["created_at"],
                data["updated_at"],
            ]
        )

    audit_rows = [
        [
            "Update ID",
            "Product ID",
            "Product SKU",
            "Product Name",
            "Action",
            "Role",
            "Quantity Delta",
            "Remarks",
            "Updated By",
            "Recorded At",
        ]
    ]
    for update in updates_query.all():
        data = update.to_dict()
        audit_rows.append(
            [
                data["id"],
                data["product_id"],
                data["product_sku"],
                data["product_name"],
                data["action"],
                data["role"],
                data["quantity_delta"],
                data["remarks"] or "-",
                data["updated_by"],
                data["created_at"],
            ]
        )

    breakdown_rows = [
        [
            "Update ID",
            "Product ID",
            "Product SKU",
            "Product Name",
            "Action",
            "Role",
            "Quantity Delta",
            "Result Quantity",
            "Remarks",
            "Updated By",
            "Recorded At",
            "Raw Changes JSON",
        ]
    ]
    for update in updates_query.all():
        data = update.to_dict()
        changes = data.get("changes") if isinstance(data.get("changes"), dict) else {}
        breakdown_rows.append(
            [
                data["id"],
                data["product_id"],
                data["product_sku"],
                data["product_name"],
                data["action"],
                data["role"],
                changes.get("quantity_delta", data["quantity_delta"]),
                changes.get("result_quantity", ""),
                data["remarks"] or "-",
                data["updated_by"],
                data["created_at"],
                json.dumps(changes, ensure_ascii=True) if changes else "{}",
            ]
        )

    workbook = build_workbook(
        [
            ("Products", product_rows),
            ("Product Audits", audit_rows),
            ("Product Update Breakdown", breakdown_rows),
        ]
    )
    return send_file(
        BytesIO(workbook),
        as_attachment=True,
        download_name="products_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route("/api/<int:product_id>/transactions", methods=["GET"])
@login_required
def product_transactions(product_id: int):
    product = Product.query.get_or_404(product_id)
    records = TradeRecord.query.filter_by(product_id=product.id).order_by(TradeRecord.recorded_on.desc()).all()
    return jsonify(
        {
            "product": product.to_dict(),
            "transactions": [record.to_dict() for record in records],
        }
    )
