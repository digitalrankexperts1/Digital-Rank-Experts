"""
Digital Rank Experts - Decorators
---------------------------------------
Custom view decorators for role-based access control and permission
checks, layered on top of Flask-Login's authentication.
"""

from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(codename):
    """Restrict a view to users whose role grants the given permission codename."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            # Superusers have access to all permission-protected pages
            if current_user.is_superuser:
                return view_func(*args, **kwargs)

            if not current_user.has_permission(codename):
                flash("You do not have permission to access that page.", "danger")
                abort(403)

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def superuser_required(view_func):
    """Restrict a view to superusers only."""

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_superuser:
            flash("This action requires super administrator privileges.", "danger")
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped_view


def role_required(*role_slugs):
    """Restrict a view to users whose role slug is in role_slugs (superusers always pass)."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.is_superuser:
                return view_func(*args, **kwargs)
            if not current_user.role or current_user.role.slug not in role_slugs:
                flash("You do not have permission to access that page.", "danger")
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
