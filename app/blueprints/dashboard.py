from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.services.dashboard import get_dashboard_payload


bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("dashboard/index.html")


@bp.route("/api/dashboard")
@login_required
def api_dashboard():
    return jsonify(
        get_dashboard_payload(
            start_date_value=request.args.get("start_date"),
            end_date_value=request.args.get("end_date"),
        )
    )
