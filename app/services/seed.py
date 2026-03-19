from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models import Product, ProductUpdate, TradeRecord, User


def seed_database() -> None:
    if User.query.first():
        return

    admin = User(
        full_name="Aarav Sharma",
        username="admin",
        email="admin@example.com",
        role=User.ROLE_ADMIN,
        status=User.STATUS_ACTIVE,
    )
    admin.set_password("admin123")

    operator = User(
        full_name="Maya Patel",
        username="maya",
        email="maya@example.com",
        role=User.ROLE_USER,
        status=User.STATUS_ACTIVE,
    )
    operator.set_password("user123")

    viewer = User(
        full_name="Rohan Gupta",
        username="rohan",
        email="rohan@example.com",
        role=User.ROLE_SUPERVISOR,
        status=User.STATUS_ACTIVE,
    )
    viewer.set_password("user123")

    manager = User(
        full_name="Ishita Verma",
        username="ishita",
        email="ishita@example.com",
        role=User.ROLE_MANAGER,
        status=User.STATUS_ACTIVE,
    )
    manager.set_password("manager123")

    db.session.add_all([admin, operator, viewer, manager])
    db.session.flush()

    products = [
        Product(
            sku="IMP-1001",
            name="Industrial Bearings",
            category="Mechanical",
            unit_price=125.50,
            quantity=240,
            origin_country="Germany",
            destination_country="India",
            status=Product.STATUS_ACTIVE,
            created_by_id=admin.id,
            updated_by_id=admin.id,
        ),
        Product(
            sku="EXP-2004",
            name="Organic Cotton Rolls",
            category="Textile",
            unit_price=84.25,
            quantity=510,
            origin_country="India",
            destination_country="UAE",
            status=Product.STATUS_ACTIVE,
            created_by_id=operator.id,
            updated_by_id=operator.id,
        ),
        Product(
            sku="SAL-3109",
            name="Solar Controller Kit",
            category="Electronics",
            unit_price=210.00,
            quantity=95,
            origin_country="China",
            destination_country="Kenya",
            status=Product.STATUS_INACTIVE,
            created_by_id=admin.id,
            updated_by_id=operator.id,
        ),
    ]
    db.session.add_all(products)
    db.session.flush()

    db.session.add_all(
        [
            ProductUpdate(
                product_id=products[0].id,
                updated_by_id=viewer.id,
                changes={"quantity_delta": -25, "result_quantity": 215},
                remarks="Supervisor stock correction",
            ),
            ProductUpdate(
                product_id=products[2].id,
                updated_by_id=viewer.id,
                changes={"quantity_delta": -95, "result_quantity": 0},
                remarks="All remaining units marked unavailable",
            ),
        ]
    )

    trade_rows = [
        (products[0], "import", 25, 3137.50, date(2026, 1, 15)),
        (products[0], "sale", 14, 1757.00, date(2026, 1, 28)),
        (products[1], "export", 60, 5055.00, date(2026, 2, 12)),
        (products[1], "sale", 22, 1853.50, date(2026, 2, 25)),
        (products[2], "import", 18, 3780.00, date(2026, 3, 2)),
        (products[2], "sale", 9, 1890.00, date(2026, 3, 11)),
        (products[1], "export", 44, 3707.00, date(2026, 3, 14)),
    ]

    for product, record_type, quantity, amount, recorded_on in trade_rows:
        db.session.add(
            TradeRecord(
                product_id=product.id,
                record_type=record_type,
                quantity=quantity,
                amount=amount,
                recorded_on=recorded_on,
            )
        )

    db.session.commit()
