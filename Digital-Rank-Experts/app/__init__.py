"""
Builds and configures the Flask application instance using the
Application Factory pattern.

Registers:
- Extensions
- Blueprints
- Error handlers
- Context processors
- Jinja filters
- CLI commands
- Production logging
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask

from config import config_by_name
from app.extensions import (
    db,
    migrate,
    login_manager,
    csrf,
    mail,
    limiter,
    cache,
)


def create_app(config_name=None):
    """
    Application factory.

    Args:
        config_name (str): One of:
            development, production, testing

    Returns:
        Flask: Configured Flask application.
    """

    if config_name is None:
        config_name = os.environ.get(
            "FLASK_ENV",
            "production"
        )

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="../static",
        template_folder="../templates",
    )

    app.config.from_object(
        config_by_name.get(
            config_name,
            config_by_name["development"]
        )
    )

    # Create required directories.
    _ensure_directories(app)

    # Initialize Flask extensions.
    _register_extensions(app)

    # Register CLI commands.
    _register_cli_commands(app)

    # Register application blueprints.
    _register_blueprints(app)

    # Register error handlers.
    _register_error_handlers(app)

    # Register context processors.
    _register_context_processors(app)

    # Register Jinja filters.
    _register_template_filters(app)

    # Configure logging.
    _configure_logging(app)

    return app


def _ensure_directories(app):
    """
    Ensure required directories exist.
    """

    directories = [
        app.instance_path,
        app.config.get("UPLOAD_FOLDER"),
        os.path.join(
            app.root_path,
            "..",
            "logs"
        ),
    ]

    for path in directories:
        if path:
            os.makedirs(
                path,
                exist_ok=True
            )


def _register_extensions(app):
    """
    Initialize Flask extensions.
    """

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
        try:
            return db.session.get(
                User,
                int(user_id)
            )
        except (ValueError, TypeError):
            return None


def _register_cli_commands(app):
    """
    Register custom Flask CLI commands.
    """

    @app.cli.command("seed-roles")
    def seed_roles():
        """
        Create/update roles and permissions and create
        the initial super administrator.
        """

        import click
        from app.models import (
            Role,
            Permission,
            User,
        )

        permission_defs = [
            (
                "manage_services",
                "Manage Services"
            ),
            (
                "manage_portfolio",
                "Manage Portfolio"
            ),
            (
                "manage_testimonials",
                "Manage Testimonials"
            ),
            (
                "manage_messages",
                "Manage Contact Messages"
            ),
            (
                "manage_blog",
                "Manage Blog"
            ),
            (
                "manage_faqs",
                "Manage FAQs"
            ),
            (
                "manage_team",
                "Manage Team"
            ),
            (
                "manage_careers",
                "Manage Careers"
            ),
            (
                "manage_settings",
                "Manage Website Settings"
            ),
        ]

        permissions = {}

        # Create missing permissions.
        for codename, name in permission_defs:

            permission = Permission.query.filter_by(
                codename=codename
            ).first()

            if permission is None:
                permission = Permission(
                    codename=codename,
                    name=name
                )

                db.session.add(permission)

            permissions[codename] = permission

        db.session.flush()

        # Find or create administrator role.
        admin_role = Role.query.filter_by(
            slug="administrator"
        ).first()

        if admin_role is None:
            admin_role = Role(
                name="Administrator",
                slug="administrator",
                description=(
                    "Full content management access."
                ),
            )

            db.session.add(admin_role)
            db.session.flush()

        # Assign all permissions.
        admin_role.permissions = list(
            permissions.values()
        )

        db.session.commit()

        # Read admin credentials from Render environment.
        admin_email = os.environ.get(
            "ADMIN_EMAIL",
            "admin@digitalrankexperts.com"
        )

        admin_password = os.environ.get(
            "ADMIN_PASSWORD"
        )

        admin_name = os.environ.get(
            "ADMIN_NAME",
            "Sohail Ahmad"
        )

        # Password is required for creating admin.
        if not admin_password:
            click.echo(
                "ERROR: ADMIN_PASSWORD environment variable "
                "is not set."
            )
            return

        # Check whether admin already exists.
        existing_user = User.query.filter_by(
            email=admin_email
        ).first()

        if existing_user is None:

            user = User(
                full_name=admin_name,
                email=admin_email,
                role_id=admin_role.id,
                is_superuser=True,
                is_active_account=True,
            )

            user.set_password(
                admin_password
            )

            db.session.add(user)
            db.session.commit()

            click.echo(
                f"Super administrator created: "
                f"{admin_email}"
            )

        else:

            # Make sure existing admin has admin privileges.
            existing_user.role_id = admin_role.id
            existing_user.is_superuser = True
            existing_user.is_active_account = True

            db.session.commit()

            click.echo(
                f"Admin user {admin_email} already exists."
            )

        click.echo(
            "Roles and permissions seeded successfully."
        )


def _register_blueprints(app):
    """
    Register application blueprints.
    """

    from app.routes import main_bp
    from app.auth import auth_bp
    from app.admin import admin_bp

    app.register_blueprint(
        main_bp
    )

    app.register_blueprint(
        auth_bp,
        url_prefix="/auth"
    )

    app.register_blueprint(
        admin_bp,
        url_prefix="/admin"
    )


def _register_error_handlers(app):
    """
    Register global error handlers.
    """

    from app.errors import register_error_handlers

    register_error_handlers(app)


def _register_context_processors(app):
    """
    Register global Jinja context processors.
    """

    from app.context_processors import (
        register_context_processors
    )

    register_context_processors(app)


def _register_template_filters(app):
    """
    Register custom Jinja filters.
    """

    from app.utils import (
        format_datetime,
        truncate_words,
        reading_time,
    )

    app.jinja_env.filters[
        "format_datetime"
    ] = format_datetime

    app.jinja_env.filters[
        "truncate_words"
    ] = truncate_words

    app.jinja_env.filters[
        "reading_time"
    ] = reading_time


def _configure_logging(app):
    """
    Configure production logging.
    """

    if app.config.get("TESTING"):
        return

    log_dir = os.path.join(
        app.root_path,
        "..",
        "logs"
    )

    os.makedirs(
        log_dir,
        exist_ok=True
    )

    log_level = (
        logging.DEBUG
        if app.debug
        else logging.INFO
    )

    log_file = os.path.join(
        log_dir,
        "digital_rank_experts.log"
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
    )

    formatter = logging.Formatter(
        "%(asctime)s "
        "%(levelname)s "
        "[%(name)s] "
        "%(message)s "
        "[in %(pathname)s:%(lineno)d]"
    )

    file_handler.setFormatter(
        formatter
    )

    file_handler.setLevel(
        log_level
    )

    app.logger.addHandler(
        file_handler
    )

    app.logger.setLevel(
        log_level
    )

    app.logger.info(
        "Digital Rank Experts startup"
    )

    # Reduce Werkzeug noise in production.
    logging.getLogger(
        "werkzeug"
    ).setLevel(
        logging.WARNING
    )
