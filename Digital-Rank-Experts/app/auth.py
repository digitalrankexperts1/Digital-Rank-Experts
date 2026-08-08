"""
Digital Rank Experts - Authentication Blueprint
------------------------------------------------------
Handles admin login, logout, and the forgot/reset password flow.
Uses Werkzeug's secure password hashing (via the User model) and
time-limited signed tokens for password resets.
"""

from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.extensions import db, limiter
from app.forms import LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.models import User
from app.email import send_password_reset_email

auth_bp = Blueprint("auth", __name__)


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        if not user.is_active_account:
            flash(
                "Your account has been deactivated. Contact a super administrator.",
                "danger"
            )
            return render_template("login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        current_app.logger.info("User %s logged in", user.email)

        next_page = request.args.get("next")

        if not next_page or not next_page.startswith("/"):
            next_page = url_for("admin.dashboard")

        return redirect(next_page)

    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    current_app.logger.info("User %s logged out", current_user.email)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user:
            serializer = _get_serializer()
            token = serializer.dumps(user.email, salt="password-reset")
            user.password_reset_token = token
            user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_password_reset_email(user, reset_url)

        # Always show the same message to avoid leaking which emails exist.
        flash("If that email exists in our system, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    serializer = _get_serializer()
    try:
        email = serializer.loads(token, salt="password-reset", max_age=3600)
    except SignatureExpired:
        flash("That password reset link has expired. Please request a new one.", "warning")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("That password reset link is invalid.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email, password_reset_token=token).first()
    if user is None:
        flash("That password reset link is invalid or has already been used.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        db.session.commit()
        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
