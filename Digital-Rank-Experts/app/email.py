"""
Digital Rank Experts - Email
-----------------------------------
Outbound email helpers built on Flask-Mail. All emails are sent via a
threaded background call so the request/response cycle is never
blocked by SMTP latency.

Templates are HTML-ready (Jinja `render_template`) but fall back to a
simple plain-text body if a template has not been created yet, so this
module works today and is ready for the future `templates/email/`
directory without any backend changes.
"""

import logging
from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)


def _send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception:  # noqa: BLE001 - we want to log and never crash a request thread
            app.logger.exception("Failed to send email to %s", msg.recipients)


def send_email(subject, recipients, text_body, html_body=None, sender=None):
    """Generic email sender. Runs the actual SMTP call on a background thread."""
    app = current_app._get_current_object()
    msg = Message(
        subject=f"[{app.config['SITE_NAME']}] {subject}",
        sender=sender or app.config["MAIL_DEFAULT_SENDER"],
        recipients=recipients,
    )
    msg.body = text_body
    if html_body:
        msg.html = html_body

    Thread(target=_send_async_email, args=(app, msg)).start()


def send_contact_form_notification(contact_message):
    """Notify the admin inbox whenever a new contact form submission arrives."""
    app = current_app._get_current_object()
    subject = f"New Contact Form Submission: {contact_message.subject or 'General Inquiry'}"
    text_body = (
        f"Name: {contact_message.full_name}\n"
        f"Email: {contact_message.email}\n"
        f"Phone: {contact_message.phone or '-'}\n\n"
        f"Message:\n{contact_message.message}\n"
    )
    send_email(
        subject=subject,
        recipients=[app.config["ADMIN_NOTIFICATION_EMAIL"]],
        text_body=text_body,
    )


def send_contact_form_autoreply(contact_message):
    """Send a courtesy auto-reply confirming receipt of the contact form."""
    app = current_app._get_current_object()
    subject = "We received your message"
    text_body = (
        f"Hi {contact_message.full_name},\n\n"
        f"Thanks for reaching out to {app.config['COMPANY_NAME']}. "
        f"One of our team members will get back to you shortly.\n\n"
        f"Best regards,\n{app.config['COMPANY_NAME']}"
    )
    send_email(subject=subject, recipients=[contact_message.email], text_body=text_body)


def send_newsletter_confirmation(subscriber):
    """Send a confirmation email to a new newsletter subscriber."""
    app = current_app._get_current_object()
    subject = "Confirm your subscription"
    text_body = (
        f"Thanks for subscribing to the {app.config['COMPANY_NAME']} newsletter!\n\n"
        f"You'll now receive occasional updates on SEO and digital marketing."
    )
    send_email(subject=subject, recipients=[subscriber.email], text_body=text_body)


def send_password_reset_email(user, reset_url):
    """Send a password reset link to an admin user."""
    subject = "Password Reset Request"
    text_body = (
        f"Hi {user.full_name},\n\n"
        f"We received a request to reset your password. Click the link below "
        f"to choose a new password. This link will expire in 1 hour.\n\n"
        f"{reset_url}\n\n"
        f"If you did not request this, you can safely ignore this email."
    )
    send_email(subject=subject, recipients=[user.email], text_body=text_body)


def send_job_application_notification(application):
    """Notify the admin inbox of a new job application."""
    app = current_app._get_current_object()
    subject = f"New Job Application: {application.career.title}"
    text_body = (
        f"Position: {application.career.title}\n"
        f"Applicant: {application.full_name}\n"
        f"Email: {application.email}\n"
        f"Phone: {application.phone or '-'}\n"
        f"Portfolio: {application.portfolio_url or '-'}\n\n"
        f"Cover Letter:\n{application.cover_letter or '-'}\n"
    )
    send_email(
        subject=subject,
        recipients=[app.config["ADMIN_NOTIFICATION_EMAIL"]],
        text_body=text_body,
    )
