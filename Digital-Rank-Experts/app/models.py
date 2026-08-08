"""
Digital Rank Experts - Database Models
------------------------------------------
All SQLAlchemy ORM models for the application. Designed to run on
SQLite in development and migrate cleanly to MySQL/PostgreSQL in
production (no SQLite-only column types are used).
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# ---------------------------------------------------------------------------
# Association tables
# ---------------------------------------------------------------------------

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)

blog_post_tags = db.Table(
    "blog_post_tags",
    db.Column("blog_post_id", db.Integer, db.ForeignKey("blog_posts.id"), primary_key=True),
    db.Column("blog_tag_id", db.Integer, db.ForeignKey("blog_tags.id"), primary_key=True),
)


class TimestampMixin:
    """Adds created_at / updated_at columns to any model."""

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# ---------------------------------------------------------------------------
# Auth: Users / Roles / Permissions
# ---------------------------------------------------------------------------

class Permission(db.Model, TimestampMixin):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    codename = db.Column(db.String(80), unique=True, nullable=False)  # e.g. "manage_blog"
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Permission {self.codename}>"


class Role(db.Model, TimestampMixin):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)  # e.g. "Super Admin"
    slug = db.Column(db.String(80), unique=True, nullable=False)  # e.g. "super-admin"
    description = db.Column(db.String(255))

    permissions = db.relationship(
        "Permission", secondary=role_permissions, backref=db.backref("roles", lazy="dynamic")
    )
    users = db.relationship("User", backref="role", lazy="dynamic")

    def has_permission(self, codename):
        return any(p.codename == codename for p in self.permissions)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)

    last_login_at = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(255))
    password_reset_expires_at = db.Column(db.DateTime)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self):
        # Overrides UserMixin.is_active to respect account status.
        return self.is_active_account

    def has_permission(self, codename):
        if self.is_superuser:
            return True
        return bool(self.role and self.role.has_permission(codename))

    def __repr__(self):
        return f"<User {self.email}>"


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

class Service(db.Model, TimestampMixin):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    short_description = db.Column(db.String(255))
    description = db.Column(db.Text)
    icon = db.Column(db.String(120))
    featured_image = db.Column(db.String(255))

    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)

    meta_title = db.Column(db.String(70))
    meta_description = db.Column(db.String(160))
    meta_keywords = db.Column(db.String(255))

    def __repr__(self):
        return f"<Service {self.title}>"


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

class Portfolio(db.Model, TimestampMixin):
    __tablename__ = "portfolio_items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    client_name = db.Column(db.String(150))
    category = db.Column(db.String(100))
    summary = db.Column(db.String(255))
    description = db.Column(db.Text)
    featured_image = db.Column(db.String(255))
    project_url = db.Column(db.String(255))

    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    completed_on = db.Column(db.Date)

    meta_title = db.Column(db.String(70))
    meta_description = db.Column(db.String(160))

    def __repr__(self):
        return f"<Portfolio {self.title}>"


# ---------------------------------------------------------------------------
# Testimonials
# ---------------------------------------------------------------------------

class Testimonial(db.Model, TimestampMixin):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(120), nullable=False)
    client_company = db.Column(db.String(150))
    client_photo = db.Column(db.String(255))
    rating = db.Column(db.Integer, default=5, nullable=False)
    message = db.Column(db.Text, nullable=False)

    is_published = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<Testimonial {self.client_name}>"


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class ContactMessage(db.Model, TimestampMixin):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)

    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))

    is_read = db.Column(db.Boolean, default=False, nullable=False)
    is_replied = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<ContactMessage {self.email}>"


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------

class BlogCategory(db.Model, TimestampMixin):
    __tablename__ = "blog_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))

    posts = db.relationship("BlogPost", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<BlogCategory {self.name}>"


class BlogTag(db.Model, TimestampMixin):
    __tablename__ = "blog_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<BlogTag {self.name}>"


class BlogPost(db.Model, TimestampMixin):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.String(300))
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(255))

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.relationship("User", backref="blog_posts")

    category_id = db.Column(db.Integer, db.ForeignKey("blog_categories.id"))
    tags = db.relationship("BlogTag", secondary=blog_post_tags, backref=db.backref("posts", lazy="dynamic"))

    is_published = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime)
    views_count = db.Column(db.Integer, default=0, nullable=False)

    meta_title = db.Column(db.String(70))
    meta_description = db.Column(db.String(160))
    meta_keywords = db.Column(db.String(255))

    def __repr__(self):
        return f"<BlogPost {self.title}>"


# ---------------------------------------------------------------------------
# SEO / Website Settings
# ---------------------------------------------------------------------------

class SEOSetting(db.Model, TimestampMixin):
    """
    Per-page SEO overrides, keyed by a unique page identifier
    (e.g. 'home', 'about', 'services'). Falls back to WebsiteSetting
    defaults when no row exists for a given page.
    """

    __tablename__ = "seo_settings"

    id = db.Column(db.Integer, primary_key=True)
    page_identifier = db.Column(db.String(100), unique=True, nullable=False, index=True)

    meta_title = db.Column(db.String(70))
    meta_description = db.Column(db.String(160))
    meta_keywords = db.Column(db.String(255))
    canonical_url = db.Column(db.String(255))
    og_image = db.Column(db.String(255))
    structured_data_json = db.Column(db.Text)  # raw JSON-LD override

    def __repr__(self):
        return f"<SEOSetting {self.page_identifier}>"


class WebsiteSetting(db.Model, TimestampMixin):
    """Singleton-style global site configuration, editable from the admin."""

    __tablename__ = "website_settings"

    id = db.Column(db.Integer, primary_key=True)

    site_name = db.Column(db.String(150), default="Digital Rank Experts")
    site_tagline = db.Column(db.String(255))
    logo = db.Column(db.String(255))
    favicon = db.Column(db.String(255))

    default_meta_title = db.Column(db.String(70))
    default_meta_description = db.Column(db.String(160))
    default_meta_keywords = db.Column(db.String(255))
    default_og_image = db.Column(db.String(255))

    company_name = db.Column(db.String(150), default="Digital Rank Experts")
    owner_name = db.Column(db.String(150), default="Sohail Ahmad")
    phone = db.Column(db.String(30), default="+92 3297 562092")
    email = db.Column(db.String(120))
    address = db.Column(db.String(255), default="Johar Town, Lahore, Pakistan")
    google_business_url = db.Column(db.String(255), default="https://maps.app.goo.gl/uuH6fPQYDqHBzFHE6")

    google_analytics_id = db.Column(db.String(50))
    google_tag_manager_id = db.Column(db.String(50))
    google_site_verification = db.Column(db.String(120))

    maintenance_mode = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<WebsiteSetting {self.site_name}>"


class SocialLink(db.Model, TimestampMixin):
    __tablename__ = "social_links"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(60), nullable=False)  # e.g. "Facebook"
    icon_class = db.Column(db.String(80))                # e.g. "fab fa-facebook-f"
    url = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<SocialLink {self.platform}>"


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterSubscriber(db.Model, TimestampMixin):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    is_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    unsubscribe_token = db.Column(db.String(255))

    def __repr__(self):
        return f"<NewsletterSubscriber {self.email}>"


# ---------------------------------------------------------------------------
# FAQs
# ---------------------------------------------------------------------------

class FAQ(db.Model, TimestampMixin):
    __tablename__ = "faqs"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<FAQ {self.question[:40]}>"


# ---------------------------------------------------------------------------
# Team
# ---------------------------------------------------------------------------

class TeamMember(db.Model, TimestampMixin):
    __tablename__ = "team_members"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    designation = db.Column(db.String(120))
    bio = db.Column(db.Text)
    photo = db.Column(db.String(255))

    linkedin_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    email = db.Column(db.String(120))

    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<TeamMember {self.full_name}>"


# ---------------------------------------------------------------------------
# Careers
# ---------------------------------------------------------------------------

class Career(db.Model, TimestampMixin):
    __tablename__ = "careers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100))
    location = db.Column(db.String(150), default="Johar Town, Lahore, Pakistan")
    employment_type = db.Column(db.String(50))  # Full-time, Part-time, Remote, Contract
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)

    is_open = db.Column(db.Boolean, default=True, nullable=False)
    application_deadline = db.Column(db.Date)

    applications = db.relationship("JobApplication", backref="career", lazy="dynamic")

    def __repr__(self):
        return f"<Career {self.title}>"


class JobApplication(db.Model, TimestampMixin):
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey("careers.id"), nullable=False)

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    cover_letter = db.Column(db.Text)
    resume_file = db.Column(db.String(255), nullable=False)
    portfolio_url = db.Column(db.String(255))

    status = db.Column(db.String(30), default="submitted", nullable=False)
    # submitted -> reviewing -> shortlisted -> interviewed -> hired / rejected

    def __repr__(self):
        return f"<JobApplication {self.full_name} -> {self.career_id}>"
