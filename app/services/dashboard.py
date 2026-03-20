from __future__ import annotations

import logging
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func

from app.models import Product, TradeRecord, User

logger = logging.getLogger(__name__)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
        logger.debug("_parse_date() | Parsed '%s' -> %s", value, parsed)
        return parsed
    except ValueError:
        logger.warning("_parse_date() | Invalid date format: '%s'", value)
        return None


def _series_key(record_type: str) -> str:
    return f"{record_type}s" if record_type != "sale" else "sales"


def _zeroed_series() -> dict:
    return {"imports": 0.0, "exports": 0.0, "sales": 0.0}


def _month_labels(start_date: date, end_date: date) -> list[str]:
    labels = []
    cursor = date(start_date.year, start_date.month, 1)
    while cursor <= end_date:
        labels.append(cursor.strftime("%b %Y"))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    logger.debug("_month_labels() | Generated %d labels from %s to %s", len(labels), start_date, end_date)
    return labels


def _period_series(rows: list[TradeRecord], start_date: date, end_date: date) -> dict:
    logger.debug("_period_series() | Processing %d records", len(rows))
    labels = _month_labels(start_date, end_date)
    monthly = {label: _zeroed_series() for label in labels}

    for row in rows:
        month_label = row.recorded_on.strftime("%b %Y")
        monthly.setdefault(month_label, _zeroed_series())
        monthly[month_label][_series_key(row.record_type)] += float(row.amount)

    return {
        "categories": labels,
        "imports": [monthly[label]["imports"] for label in labels],
        "exports": [monthly[label]["exports"] for label in labels],
        "sales": [monthly[label]["sales"] for label in labels],
    }


def _comparison_series(end_date: date) -> dict:
    logger.debug("_comparison_series() | Building comparison for end_date=%s", end_date)
    labels = []
    current = []
    previous = []

    for offset in range(5, -1, -1):
        month = end_date.month - offset
        year = end_date.year
        while month <= 0:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1

        start_of_month = date(year, month, 1)
        end_of_month = date(year, month, monthrange(year, month)[1])
        prior_year_month = date(year - 1, month, 1)
        prior_year_end = date(year - 1, month, monthrange(year - 1, month)[1])

        current_total = (
            TradeRecord.query.with_entities(func.coalesce(func.sum(TradeRecord.amount), 0))
            .filter(TradeRecord.recorded_on >= start_of_month, TradeRecord.recorded_on <= end_of_month)
            .scalar()
        )
        previous_total = (
            TradeRecord.query.with_entities(func.coalesce(func.sum(TradeRecord.amount), 0))
            .filter(TradeRecord.recorded_on >= prior_year_month, TradeRecord.recorded_on <= prior_year_end)
            .scalar()
        )

        labels.append(start_of_month.strftime("%b"))
        current.append(float(current_total or Decimal("0")))
        previous.append(float(previous_total or Decimal("0")))

    logger.debug("_comparison_series() | Built %d comparison data points", len(labels))
    return {
        "categories": labels,
        "current_period": current,
        "previous_year": previous,
    }


def get_dashboard_payload(start_date_value: str | None = None, end_date_value: str | None = None) -> dict:
    logger.info("get_dashboard_payload() | start=%s, end=%s", start_date_value, end_date_value)

    records_query = TradeRecord.query.order_by(TradeRecord.recorded_on.asc())
    all_dates = [row[0] for row in TradeRecord.query.with_entities(TradeRecord.recorded_on).all()]
    default_start = min(all_dates) if all_dates else date.today().replace(day=1)
    default_end = max(all_dates) if all_dates else date.today()

    start_date = _parse_date(start_date_value) or default_start
    end_date = _parse_date(end_date_value) or default_end
    if start_date > end_date:
        start_date, end_date = end_date, start_date
        logger.warning("get_dashboard_payload() | start > end, swapped: start=%s, end=%s", start_date, end_date)

    filtered_records = (
        records_query.filter(TradeRecord.recorded_on >= start_date, TradeRecord.recorded_on <= end_date).all()
    )
    logger.info("get_dashboard_payload() | Filtered %d trade records", len(filtered_records))

    totals = _zeroed_series()
    transaction_count = len(filtered_records)
    markets = set()

    for row in filtered_records:
        totals[_series_key(row.record_type)] += float(row.amount)
        markets.add(row.product.destination_country)
        markets.add(row.product.origin_country)

    categories = defaultdict(int)
    for row in Product.query.all():
        categories[row.category] += row.quantity

    total_trade = totals["imports"] + totals["exports"] + totals["sales"]
    average_ticket = total_trade / transaction_count if transaction_count else 0

    logger.info(
        "get_dashboard_payload() | Metrics: imports=%.2f, exports=%.2f, sales=%.2f, transactions=%d, markets=%d",
        totals["imports"], totals["exports"], totals["sales"], transaction_count, len(markets),
    )

    return {
        "metrics": {
            "imports": totals["imports"],
            "exports": totals["exports"],
            "sales": totals["sales"],
            "products": Product.query.count(),
            "users": User.query.count(),
            "active_products": Product.query.filter_by(status=Product.STATUS_ACTIVE).count(),
            "transactions": transaction_count,
            "inventory_units": sum(categories.values()),
            "market_coverage": len(markets),
            "average_ticket": average_ticket,
        },
        "filters": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "available_start_date": default_start.isoformat(),
            "available_end_date": default_end.isoformat(),
        },
        "revenue_series": _period_series(filtered_records, start_date, end_date),
        "comparison_series": _comparison_series(end_date),
        "category_breakdown": {
            "labels": list(categories.keys()),
            "series": list(categories.values()),
        },
        "recent_activity": [
            {
                "product": trade.product.name,
                "type": trade.record_type.title(),
                "amount": float(trade.amount),
                "quantity": trade.quantity,
                "date": trade.recorded_on.strftime("%d %b %Y"),
            }
            for trade in sorted(filtered_records, key=lambda item: item.recorded_on, reverse=True)[:6]
        ],
    }
