from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus


BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _build_database_uri() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    pg_host = os.getenv("POSTGRES_HOST", "").strip()
    if pg_host:
        user = quote_plus(os.getenv("POSTGRES_USER", "postgres"))
        password = quote_plus(os.getenv("POSTGRES_PASSWORD", "postgres"))
        port = os.getenv("POSTGRES_PORT", "5432").strip()
        database = quote_plus(os.getenv("POSTGRES_DB", "import_export_admin"))
        return f"postgresql+psycopg://{user}:{password}@{pg_host}:{port}/{database}"

    return f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION_DAYS = int(os.getenv("REMEMBER_COOKIE_DURATION_DAYS", "14"))
    APP_NAME = os.getenv("APP_NAME", "SS Seafood")
