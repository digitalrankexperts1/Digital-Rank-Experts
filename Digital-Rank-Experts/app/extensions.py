"""
Digital Rank Experts - Flask Extensions
-----------------------------------------
Centralized instantiation of all Flask extensions.

This module exists to avoid circular imports between the application
factory (app/__init__.py) and the rest of the application modules
(models, routes, admin, auth, etc). Every extension is instantiated
here WITHOUT an application instance and is later bound to the Flask
app inside the application factory via `extension.init_app(app)`.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# Database ORM
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# Authentication / session management
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access the admin dashboard."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"

# CSRF protection for all forms
csrf = CSRFProtect()

# Outbound email (contact form, newsletter, password reset)
mail = Mail()

# Rate limiting to protect public forms and auth endpoints from abuse
limiter = Limiter(key_func=get_remote_address)

# Simple in-memory / configurable cache layer
cache = Cache()
