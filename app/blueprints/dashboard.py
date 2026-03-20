from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, render_template, request
from flask_login import login_required

from app.services.dashboard import get_dashboard_payload

logger = logging.getLogger(__name__)

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    logger.info("index() | Dashboard page requested")
    return render_template("dashboard/index.html")


@bp.route("/api/dashboard")
@login_required
def api_dashboard():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    logger.info("api_dashboard() | Fetching dashboard data | start_date=%s, end_date=%s", start_date, end_date)
    try:
        payload = get_dashboard_payload(
            start_date_value=start_date,
            end_date_value=end_date,
        )
        logger.info("api_dashboard() | Dashboard data built successfully | metrics_keys=%s", list(payload.get("metrics", {}).keys()))
        return jsonify(payload)
    except Exception:
        logger.exception("api_dashboard() | ERROR building dashboard payload")
        return jsonify({"message": "Failed to load dashboard data.", "req_hash": getattr(g, "req_hash", "--------")}), 500
