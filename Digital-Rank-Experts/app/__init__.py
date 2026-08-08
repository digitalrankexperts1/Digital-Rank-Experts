"""
Digital Rank Experts - Application Factory
---------------------------------------------
Builds and configures the Flask application instance using the
Application Factory pattern. Registers extensions, blueprints,
error handlers, context processors, and logging.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask

from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf, mail, limiter, cache


def create_app(config_name=None):
    """
    Application factory.

    Args:
        config_name (str): One of 'development', 'production', 'testing'.
                            Falls back to the FLASK_ENV environment variable,
                            and finally to 'development'.

    Returns:
        Flask: A fully configured Flask application instance.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../static",
        template_folder="../templates",
    )

    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Ensure instance / upload / log directories exist before anything
    # tries to write to them (SQLite file, logs, uploaded files).
    _ensure_directories(app)

    # Bind extensions to the application instance.
    _register_extensions(app)

    # Register blueprints (route groups).
    _register_blueprints(app)

    # Register global error handlers.
    _register_error_handlers(app)

    # Register Jinja context processors (site settings, social links, etc).
    _register_context_processors(app)

    # Register CLI-friendly / template-friendly Jinja filters.
    _register_template_filters(app)

    # Configure production-grade logging.
    _configure_logging(app)

    return app


def _ensure_directories(app):
    for path in (
        app.instance_path,
        app.config.get("UPLOAD_FOLDER"),
        os.path.join(app.root_path, "..", "logs"),
    ):
        if path:
            os.makedirs(path, exist_ok=True)


def _register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")


def _register_error_handlers(app):
    from app.errors import register_error_handlers

    register_error_handlers(app)


def _register_context_processors(app):
    from app.context_processors import register_context_processors

    register_context_processors(app)


def _register_template_filters(app):
    from app.utils import format_datetime, truncate_words, reading_time

    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["truncate_words"] = truncate_words
    app.jinja_env.filters["reading_time"] = reading_time


def _configure_logging(app):
    if app.config.get("TESTING"):
        return

    log_dir = os.path.join(app.root_path, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_level = logging.DEBUG if app.debug else logging.INFO

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "digital_rank_experts.log"),
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=10,
    )
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s "
        "[in %(pathname)s:%(lineno)d]"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    app.logger.info("Digital Rank Experts startup")

    # Silence overly verbose third-party loggers in production.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
