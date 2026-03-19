from __future__ import annotations

from pathlib import Path

from flask import Flask, redirect, request, send_from_directory, url_for

from app.blueprints.auth import bp as auth_bp
from app.blueprints.dashboard import bp as dashboard_bp
from app.blueprints.products import bp as products_bp
from app.blueprints.users import bp as users_bp
from app.extensions import db, login_manager
from app.models import User
from app.services.seed import seed_database
from config import Config


ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    app.instance_path = str(ROOT_DIR / "instance")
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_helpers():
        return {
            "asset_url": lambda filename: url_for("assets_files", filename=filename),
            "app_name": app.config["APP_NAME"],
            "current_theme_mode": request.cookies.get("theme_mode", "system"),
        }

    @app.route("/assets/<path:filename>")
    def assets_files(filename: str):
        return send_from_directory(ASSETS_DIR, filename)

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/home")
    def home():
        return redirect(url_for("dashboard.index"))

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(users_bp)

    with app.app_context():
        db.create_all()
        seed_database()

    return app
