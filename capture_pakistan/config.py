import os

from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

load_dotenv(
    PROJECT_ROOT / ".env"
)


def env_bool(
    name: str,
    default: bool = False,
) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


class Config:
    # ---------------------------------
    # Application environment
    # ---------------------------------

    APP_ENV = os.getenv(
        "APP_ENV",
        "development",
    ).strip().lower()

    IS_PRODUCTION = (
        APP_ENV == "production"
    )

    DEBUG = env_bool(
        "FLASK_DEBUG",
        False,
    )

    TESTING = False

    # ---------------------------------
    # Secret key
    # ---------------------------------

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "temporary-development-key-change-before-live",
    )

    # ---------------------------------
    # Database
    # ---------------------------------

    DB_USER = quote_plus(
        os.getenv(
            "DB_USER",
            "",
        )
    )

    DB_PASSWORD = quote_plus(
        os.getenv(
            "DB_PASSWORD",
            "",
        )
    )

    DB_HOST = os.getenv(
        "DB_HOST",
        "127.0.0.1",
    )

    DB_PORT = os.getenv(
        "DB_PORT",
        "3306",
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "",
    )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://"
        f"{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # ---------------------------------
    # Session and cookie security
    # ---------------------------------

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = env_bool(
        "SESSION_COOKIE_SECURE",
        IS_PRODUCTION,
    )

    REMEMBER_COOKIE_HTTPONLY = True

    REMEMBER_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_SECURE = env_bool(
        "REMEMBER_COOKIE_SECURE",
        IS_PRODUCTION,
    )

    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=2,
    )

    # ---------------------------------
    # CSRF protection
    # ---------------------------------

    WTF_CSRF_ENABLED = env_bool(
        "WTF_CSRF_ENABLED",
        True,
    )

    WTF_CSRF_TIME_LIMIT = 7200

    # ---------------------------------
    # Request and upload limits
    # ---------------------------------

    MAX_CONTENT_LENGTH = (
        40 * 1024 * 1024
    )

    MAX_FORM_MEMORY_SIZE = (
        1024 * 1024
    )

    MAX_FORM_PARTS = 200

    TOUR_GALLERY_MAX_IMAGES = 20

    TOUR_GALLERY_MAX_FILE_SIZE = (
        8 * 1024 * 1024
    )

    # ---------------------------------
    # Rate limiting
    # ---------------------------------

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )

    RATELIMIT_HEADERS_ENABLED = True

    # ---------------------------------
    # Security headers
    # ---------------------------------

    SECURITY_ENABLE_HSTS = env_bool(
        "SECURITY_ENABLE_HSTS",
        IS_PRODUCTION,
    )

    SECURITY_BEHIND_PROXY = env_bool(
        "SECURITY_BEHIND_PROXY",
        False,
    )

    TRUSTED_HOSTS = [
        host.strip()
        for host in os.getenv(
            "TRUSTED_HOSTS",
            "",
        ).split(",")
        if host.strip()
    ] or None

    PREFERRED_URL_SCHEME = (
        "https"
        if IS_PRODUCTION
        else "http"
    )

    # ---------------------------------
    # Website
    # ---------------------------------

    SITE_URL = os.getenv(
        "SITE_URL",
        "http://127.0.0.1:5001",
    )

    # ---------------------------------
    # Email
    # ---------------------------------

    MAIL_ENABLED = env_bool(
        "MAIL_ENABLED",
        False,
    )

    MAIL_SERVER = os.getenv(
        "MAIL_SERVER",
        "smtp.gmail.com",
    )

    MAIL_PORT = int(
        os.getenv(
            "MAIL_PORT",
            "587",
        )
    )

    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME",
        "",
    )

    MAIL_PASSWORD = os.getenv(
        "MAIL_PASSWORD",
        "",
    )

    MAIL_USE_TLS = env_bool(
        "MAIL_USE_TLS",
        True,
    )

    MAIL_USE_SSL = env_bool(
        "MAIL_USE_SSL",
        False,
    )

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        MAIL_USERNAME,
    )

    MAIL_SENDER_NAME = os.getenv(
        "MAIL_SENDER_NAME",
        "Capture Pakistan",
    )

    MAIL_TIMEOUT = int(
        os.getenv(
            "MAIL_TIMEOUT",
            "20",
        )
    )

    # ---------------------------------
    # Invoice
    # ---------------------------------

    INVOICE_COMPANY_NAME = os.getenv(
        "INVOICE_COMPANY_NAME",
        "Capture Pakistan",
    )

    INVOICE_COMPANY_EMAIL = os.getenv(
        "INVOICE_COMPANY_EMAIL",
        MAIL_DEFAULT_SENDER
        or "info@capturepakistan.com",
    )

    INVOICE_COMPANY_PHONE = os.getenv(
        "INVOICE_COMPANY_PHONE",
        "",
    )

    INVOICE_COMPANY_ADDRESS = os.getenv(
        "INVOICE_COMPANY_ADDRESS",
        "Pakistan",
    )

    INVOICE_CURRENCY = os.getenv(
        "INVOICE_CURRENCY",
        "PKR",
    )


def validate_production_config(app):
    """Fail fast when a production deployment is missing critical settings."""
    if not app.config.get("IS_PRODUCTION"):
        return

    problems = []
    secret_key = str(app.config.get("SECRET_KEY") or "").strip()

    if (
        len(secret_key) < 32
        or secret_key.startswith("temporary-development-key")
    ):
        problems.append("SECRET_KEY must be a strong unique value")

    for key in (
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
    ):
        if not str(app.config.get(key) or "").strip():
            problems.append(f"{key} is required")

    site_url = str(app.config.get("SITE_URL") or "").strip()
    if not site_url.startswith("https://"):
        problems.append("SITE_URL must use https://")

    if not app.config.get("TRUSTED_HOSTS"):
        problems.append("TRUSTED_HOSTS must list the live domains")

    for key in (
        "SESSION_COOKIE_SECURE",
        "REMEMBER_COOKIE_SECURE",
        "SECURITY_ENABLE_HSTS",
    ):
        if not app.config.get(key):
            problems.append(f"{key} must be true")

    if app.config.get("MAIL_ENABLED"):
        for key in (
            "MAIL_SERVER",
            "MAIL_USERNAME",
            "MAIL_PASSWORD",
        ):
            if not str(app.config.get(key) or "").strip():
                problems.append(f"{key} is required when email is enabled")

    if problems:
        raise RuntimeError(
            "Production configuration is incomplete: "
            + "; ".join(problems)
        )
