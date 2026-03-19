from __future__ import annotations

from datetime import date, datetime
from typing import ClassVar

import re
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    ROLE_USER: ClassVar[str] = "1"
    ROLE_ADMIN: ClassVar[str] = "2"
    ROLE_SUPERVISOR: ClassVar[str] = "3"
    ROLE_MANAGER: ClassVar[str] = "4"

    STATUS_ACTIVE: ClassVar[str] = "1"
    STATUS_INACTIVE: ClassVar[str] = "0"
    STATUS_DELETED: ClassVar[str] = "5"

    ROLE_CHOICES: ClassVar[dict[str, str]] = {
        ROLE_USER: "User",
        ROLE_ADMIN: "Admin",
        ROLE_SUPERVISOR: "Supervisor",
        ROLE_MANAGER: "Manager",
    }
    STATUS_CHOICES: ClassVar[dict[str, str]] = {
        STATUS_ACTIVE: "Active",
        STATUS_INACTIVE: "Inactive",
        STATUS_DELETED: "Deleted",
    }

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(
        ENUM("1", "2", "3", "4", name="role_types", create_type=False),
        nullable=False,
        default="1",
    )
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(
        ENUM("1", "0", "5", name="status_types", create_type=False),
        nullable=False,
        default="1",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        return self.status == self.STATUS_ACTIVE

    @property
    def role_label(self) -> str:
        return self.ROLE_CHOICES.get(self.role, self.role)

    @property
    def status_label(self) -> str:
        return self.STATUS_CHOICES.get(self.status, self.status)

    @classmethod
    def is_valid_role(cls, value: str) -> bool:
        return value in cls.ROLE_CHOICES

    @classmethod
    def is_valid_email(cls, email: str) -> bool:
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, email):
            return False

        existing_user = cls.query.filter_by(email=email).first()
        if existing_user:
            return False

        return True

    @classmethod
    def is_valid_status(cls, value: str) -> bool:
        return value in cls.STATUS_CHOICES

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "role_label": self.role_label,
            "status": self.status,
            "status_label": self.status_label,
            "created_at": self.created_at.strftime("%d-%m-%Y"),
            "updated_at": self.updated_at.strftime("%d-%m-%Y") if self.updated_at else "-",
        }


class Product(TimestampMixin, db.Model):
    __tablename__ = "products"

    STATUS_ACTIVE: ClassVar[str] = "1"
    STATUS_INACTIVE: ClassVar[str] = "0"
    STATUS_DELETED: ClassVar[str] = "5"

    STATUS_CHOICES: ClassVar[dict[str, str]] = {
        STATUS_ACTIVE: "Active",
        STATUS_INACTIVE: "Inactive",
        STATUS_DELETED: "Deleted",
    }

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=False, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    origin_country = db.Column(db.String(80), nullable=False)
    destination_country = db.Column(db.String(80), nullable=False)
    created_by_id = db.Column(db.Integer, nullable=False)
    updated_by_id = db.Column(db.Integer, nullable=True)
    status = db.Column(
        ENUM("1", "0", "5", name="status_types", create_type=False),
        nullable=False,
        default="1",
    )

    @property
    def is_active(self) -> bool:
        return self.status == self.STATUS_ACTIVE

    @property
    def status_label(self) -> str:
        return self.STATUS_CHOICES.get(self.status, self.status)

    @property
    def supervisor_quantity_delta(self) -> int:
        total = 0
        for update in ProductUpdate.query.filter_by(product_id=self.id).all():
            if isinstance(update.changes, dict):
                total += int(update.changes.get("quantity_delta", 0) or 0)
        return total

    @property
    def effective_quantity(self) -> int:
        total = int(self.quantity or 0) + self.supervisor_quantity_delta
        return max(total, 0)

    @property
    def resolved_status(self) -> str:
        if self.status == self.STATUS_DELETED:
            return self.STATUS_CHOICES[self.STATUS_DELETED]
        if self.status == self.STATUS_INACTIVE or self.effective_quantity <= 0:
            return self.STATUS_CHOICES[self.STATUS_INACTIVE]
        return self.STATUS_CHOICES[self.STATUS_ACTIVE]

    def to_dict(self) -> dict:
        created_user = User.query.get(self.created_by_id) if self.created_by_id else None
        updated_user = User.query.get(self.updated_by_id) if self.updated_by_id else None
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "unit_price": float(self.unit_price),
            "quantity": self.effective_quantity,
            "base_quantity": int(self.quantity or 0),
            "supervisor_quantity_delta": self.supervisor_quantity_delta,
            "origin_country": self.origin_country,
            "destination_country": self.destination_country,
            "status": self.resolved_status,
            "created_at": self.created_at.strftime("%d-%m-%Y"),
            "updated_at": self.updated_at.strftime("%d-%m-%Y") if self.updated_at else "-",
            "created_by": created_user.full_name if created_user else "-",
            "updated_by": updated_user.full_name if updated_user else "-",
        }


class ProductUpdate(TimestampMixin, db.Model):
    __tablename__ = "product_updates"

    ACTION_QUANTITY_UPDATED: ClassVar[str] = "QUANTITY_UPDATED"
    ROLE_SUPERVISOR: ClassVar[str] = User.ROLE_SUPERVISOR

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    updated_by_id = db.Column(db.Integer, nullable=False)
    changes = db.Column(JSONB, nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    @property
    def action_label(self) -> str:
        return "Quantity Updated"

    def to_dict(self) -> dict:
        user = User.query.get(self.updated_by_id) if self.updated_by_id else None
        product = Product.query.get(self.product_id) if self.product_id else None
        quantity_delta = 0
        if isinstance(self.changes, dict):
            quantity_delta = int(self.changes.get("quantity_delta", 0) or 0)

        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": product.name if product else "-",
            "product_sku": product.sku if product else "-",
            "action": self.action_label,
            "role": User.ROLE_CHOICES.get(self.ROLE_SUPERVISOR, self.ROLE_SUPERVISOR),
            "quantity_delta": quantity_delta,
            "changes": self.changes,
            "remarks": self.remarks,
            "updated_by": user.full_name if user else "-",
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M"),
        }


class TradeRecord(TimestampMixin, db.Model):
    __tablename__ = "trade_records"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    record_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    recorded_on = db.Column(db.Date, nullable=False, default=date.today)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "record_type": self.record_type,
            "quantity": self.quantity,
            "amount": float(self.amount),
            "recorded_on": self.recorded_on.strftime("%d-%m-%Y"),
        }
