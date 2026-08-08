"""
Digital Rank Experts - Application Entry Point
------------------------------------------------------
Run with:  python app.py            (development server)
Or with:   flask run                (uses FLASK_APP=app.py)
Or in production behind a WSGI server, e.g.:
           gunicorn "app:create_app()"
"""

import os
import click

from app import create_app
from app.extensions import db

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    """Enables `flask shell` to auto-import models/db for quick debugging."""
    from app import models

    return {"db": db, "models": models}


@app.cli.command("seed-roles")
def seed_roles():
    """
    Seed the default Role/Permission set and a super administrator account.
    Reads the initial admin credentials from environment variables:
        ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME
    """
    from app.models import Role, Permission, User

    permission_defs = [
        ("manage_services", "Manage Services"),
        ("manage_portfolio", "Manage Portfolio"),
        ("manage_testimonials", "Manage Testimonials"),
        ("manage_messages", "Manage Contact Messages"),
        ("manage_blog", "Manage Blog"),
        ("manage_faqs", "Manage FAQs"),
        ("manage_team", "Manage Team"),
        ("manage_careers", "Manage Careers"),
        ("manage_settings", "Manage Website Settings"),
    ]

    permissions = {}
    for codename, name in permission_defs:
        perm = Permission.query.filter_by(codename=codename).first()
        if perm is None:
            perm = Permission(codename=codename, name=name)
            db.session.add(perm)
        permissions[codename] = perm

    db.session.flush()

    admin_role = Role.query.filter_by(slug="administrator").first()
    if admin_role is None:
        admin_role = Role(name="Administrator", slug="administrator", description="Full content management access.")
        db.session.add(admin_role)

    admin_role.permissions = list(permissions.values())
    db.session.commit()

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@digitalrankexperts.com")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    admin_name = os.environ.get("ADMIN_NAME", "Sohail Ahmad")

    if not admin_password:
        click.echo("ADMIN_PASSWORD environment variable not set — skipping admin user creation.")
        return

    existing_user = User.query.filter_by(email=admin_email).first()
    if existing_user is None:
        user = User(
            full_name=admin_name,
            email=admin_email,
            role_id=admin_role.id,
            is_superuser=True,
            is_active_account=True,
        )
        user.set_password(admin_password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Super administrator created: {admin_email}")
    else:
        click.echo(f"Admin user {admin_email} already exists — skipped.")

    click.echo("Roles and permissions seeded successfully.")


if __name__ == "__main__":
    debug_mode = app.config.get("DEBUG", False)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
