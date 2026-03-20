from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        logger.warning("_load_dotenv() | .env file not found at %s", env_path)
        return

    logger.info("_load_dotenv() | Loading environment from %s", env_path)
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
            uri = database_url.replace("postgres://", "postgresql://", 1)
        else:
            uri = database_url
        logger.info("_build_database_uri() | Using DATABASE_URL (host masked)")
        return uri

    pg_host = os.getenv("POSTGRES_HOST", "").strip()
    if pg_host:
        user = quote_plus(os.getenv("POSTGRES_USER", "postgres"))
        password = quote_plus(os.getenv("POSTGRES_PASSWORD", "postgres"))
        port = os.getenv("POSTGRES_PORT", "5432").strip()
        database = quote_plus(os.getenv("POSTGRES_DB", "import_export_admin"))
        uri = f"postgresql+psycopg://{user}:{password}@{pg_host}:{port}/{database}"
        logger.info("_build_database_uri() | Built URI from POSTGRES_* vars | host=%s, db=%s", pg_host, database)
        return uri

    sqlite_path = (BASE_DIR / "instance" / "app.db").as_posix()
    logger.info("_build_database_uri() | Falling back to SQLite at %s", sqlite_path)
    return f"sqlite:///{sqlite_path}"


def _get_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "").strip()
    if not key or key == "replace-me" or key == "change-me-in-production":
        generated = secrets.token_hex(32)
        logger.warning(
            "_get_secret_key() | SECRET_KEY is weak or missing! "
            "Generated a random key for this session. Set a strong SECRET_KEY in .env for production."
        )
        return generated
    return key


class Config:
    SECRET_KEY = _get_secret_key()
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION_DAYS = int(os.getenv("REMEMBER_COOKIE_DURATION_DAYS", "14"))
    APP_NAME = os.getenv("APP_NAME", "SS Seafood")
