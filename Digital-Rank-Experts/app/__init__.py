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

    user.set_password(admin_password)

    db.session.add(user)
    db.session.commit()

    click.echo(
        f"Super administrator created: {admin_email}"
    )

else:

    # Update admin details.
    existing_user.full_name = admin_name
    existing_user.role_id = admin_role.id
    existing_user.is_superuser = True
    existing_user.is_active_account = True

    # IMPORTANT:
    # Reset the password from ADMIN_PASSWORD
    # every time the seed command runs.
    existing_user.set_password(admin_password)

    db.session.commit()

    click.echo(
        f"Admin user {admin_email} password reset successfully."
    )

click.echo(
    "Roles and permissions seeded successfully."
)
