"""
Digital Rank Experts - Configuration
----------------------------------------
Environment-driven configuration classes. Secrets and environment
specific values are read from environment variables (see .env.example)
and never hard-coded.
"""

import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _bool_env(key, default="False"):
    return os.environ.get(key, default).strip().lower() in ("true", "1", "yes", "on")


class Config:
    """Base configuration shared across all environments."""

    # --- Core Flask ---------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # --- Database -------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "digital_rank_experts.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Uploads ---------------------------------------------------------
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(basedir, "static", "uploads"))
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 10)) * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx"}

    # --- Session / Cookies -----------------------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True

    # --- Mail -------------------------------------------------------------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _bool_env("MAIL_USE_TLS", "True")
    MAIL_USE_SSL = _bool_env("MAIL_USE_SSL", "False")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@digitalrankexperts.com")
    ADMIN_NOTIFICATION_EMAIL = os.environ.get("ADMIN_NOTIFICATION_EMAIL", "info@digitalrankexperts.com")

    # --- Rate limiting ------------------------------------------------------
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_HEADERS_ENABLED = True

    # --- Caching --------------------------------------------------------------
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))

    # --- Pagination -------------------------------------------------------------
    POSTS_PER_PAGE = 9
    PORTFOLIO_PER_PAGE = 9
    ADMIN_ITEMS_PER_PAGE = 20

    # --- Site / SEO defaults ------------------------------------------------------
    SITE_NAME = "Digital Rank Experts"
    SITE_URL = os.environ.get("SITE_URL", "https://digitalrankexperts.com")
    COMPANY_NAME = "Digital Rank Experts"
    OWNER_NAME = "Sohail Ahmad"
    COMPANY_PHONE = "+92 3297 562092"
    COMPANY_ADDRESS = "Johar Town, Lahore, Pakistan"
    GOOGLE_BUSINESS_URL = "https://maps.app.goo.gl/uuH6fPQYDqHBzFHE6"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        # In production, fail fast if a real secret key was not supplied.
        if app.config["SECRET_KEY"] == "change-this-secret-key-in-production":
            app.logger.warning(
                "SECURITY WARNING: default SECRET_KEY is in use. "
                "Set the SECRET_KEY environment variable before deploying."
            )


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
