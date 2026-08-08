"""
Digital Rank Experts - Utilities
-------------------------------------
Reusable helper functions used across routes, admin, and forms:
slug generation, file upload handling, Jinja filters, and misc helpers.
"""

import os
import re
import uuid
import unicodedata
from datetime import datetime

from flask import current_app
from werkzeug.utils import secure_filename


# ---------------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------------

def slugify(value):
    """Convert an arbitrary string into a URL-safe slug."""
    value = str(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value or uuid.uuid4().hex[:8]


def generate_unique_slug(model, value, slug_field="slug", instance_id=None):
    """
    Generate a slug for `value` that is unique for the given model.
    If a collision exists, append -2, -3, etc. Excludes `instance_id`
    from the collision check (useful when editing an existing record).
    """
    base_slug = slugify(value)
    slug = base_slug
    counter = 2

    query = model.query.filter(getattr(model, slug_field) == slug)
    if instance_id is not None:
        query = query.filter(model.id != instance_id)

    while query.first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
        query = model.query.filter(getattr(model, slug_field) == slug)
        if instance_id is not None:
            query = query.filter(model.id != instance_id)

    return slug


# ---------------------------------------------------------------------------
# File uploads
# ---------------------------------------------------------------------------

def _allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_uploaded_file(file_storage, subfolder="", allowed_extensions=None):
    """
    Safely persist an uploaded file under UPLOAD_FOLDER/subfolder using a
    randomized, collision-proof filename. Returns the relative path
    (relative to the static folder) to store in the database, or None if
    no file was provided or the extension was rejected.
    """
    if not file_storage or file_storage.filename == "":
        return None

    allowed_extensions = allowed_extensions or current_app.config["ALLOWED_IMAGE_EXTENSIONS"]

    original_name = secure_filename(file_storage.filename)
    if not _allowed_file(original_name, allowed_extensions):
        raise ValueError(f"File type not allowed: {original_name}")

    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    target_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(target_dir, exist_ok=True)

    absolute_path = os.path.join(target_dir, unique_name)
    file_storage.save(absolute_path)

    relative_path = os.path.join("uploads", subfolder, unique_name).replace("\\", "/")
    return relative_path


def delete_uploaded_file(relative_path):
    """Delete a previously uploaded file (relative to the static folder), if it exists."""
    if not relative_path:
        return
    static_folder = current_app.static_folder
    absolute_path = os.path.join(static_folder, relative_path)
    if os.path.isfile(absolute_path):
        os.remove(absolute_path)


# ---------------------------------------------------------------------------
# Jinja filters
# ---------------------------------------------------------------------------

def format_datetime(value, fmt="%B %d, %Y"):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.strftime(fmt)


def truncate_words(value, word_count=30):
    if not value:
        return ""
    words = value.split()
    if len(words) <= word_count:
        return value
    return " ".join(words[:word_count]) + "…"


def reading_time(value, words_per_minute=200):
    if not value:
        return 1
    word_count = len(value.split())
    minutes = max(1, round(word_count / words_per_minute))
    return minutes


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------

def paginate_query(query, page, per_page):
    """Thin wrapper around Flask-SQLAlchemy's paginate for consistent usage."""
    return query.paginate(page=page, per_page=per_page, error_out=False)


# ---------------------------------------------------------------------------
# Client info
# ---------------------------------------------------------------------------

def get_client_ip(request):
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr


def get_current_year():
    return datetime.utcnow().year
