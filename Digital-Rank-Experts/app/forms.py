"""
Digital Rank Experts - Forms
---------------------------------
Flask-WTF form definitions for public-facing forms (contact, newsletter,
job applications, login) and admin CRUD forms.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    PasswordField,
    BooleanField,
    IntegerField,
    SelectField,
    DateField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    URL,
    EqualTo,
    NumberRange,
)


# ---------------------------------------------------------------------------
# Public forms
# ---------------------------------------------------------------------------

class ContactForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    subject = StringField("Subject", validators=[Optional(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=5000)])
    submit = SubmitField("Send Message")


class NewsletterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("Subscribe")


class JobApplicationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    portfolio_url = StringField("Portfolio URL", validators=[Optional(), URL(), Length(max=255)])
    cover_letter = TextAreaField("Cover Letter", validators=[Optional(), Length(max=5000)])
    resume_file = FileField(
        "Resume (PDF or DOCX)",
        validators=[DataRequired(), FileAllowed(["pdf", "doc", "docx"], "PDF or DOCX only!")],
    )
    submit = SubmitField("Apply Now")


# ---------------------------------------------------------------------------
# Auth forms
# ---------------------------------------------------------------------------

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Reset Password")


# ---------------------------------------------------------------------------
# Admin CRUD forms
# ---------------------------------------------------------------------------

class ServiceForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    short_description = StringField("Short Description", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Full Description", validators=[Optional()])
    icon = StringField("Icon Class", validators=[Optional(), Length(max=120)])
    featured_image = FileField("Featured Image", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "webp", "svg"])])
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published", default=True)
    display_order = IntegerField("Display Order", validators=[Optional(), NumberRange(min=0)], default=0)
    meta_title = StringField("Meta Title", validators=[Optional(), Length(max=70)])
    meta_description = StringField("Meta Description", validators=[Optional(), Length(max=160)])
    meta_keywords = StringField("Meta Keywords", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Service")


class PortfolioForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    client_name = StringField("Client Name", validators=[Optional(), Length(max=150)])
    category = StringField("Category", validators=[Optional(), Length(max=100)])
    summary = StringField("Summary", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Description", validators=[Optional()])
    featured_image = FileField("Featured Image", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "webp", "svg"])])
    project_url = StringField("Project URL", validators=[Optional(), URL(), Length(max=255)])
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published", default=True)
    display_order = IntegerField("Display Order", validators=[Optional(), NumberRange(min=0)], default=0)
    completed_on = DateField("Completed On", validators=[Optional()])
    submit = SubmitField("Save Project")


class TestimonialForm(FlaskForm):
    client_name = StringField("Client Name", validators=[DataRequired(), Length(max=120)])
    client_company = StringField("Client Company", validators=[Optional(), Length(max=150)])
    client_photo = FileField("Client Photo", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"])])
    rating = IntegerField("Rating", validators=[DataRequired(), NumberRange(min=1, max=5)], default=5)
    message = TextAreaField("Testimonial", validators=[DataRequired(), Length(max=2000)])
    is_published = BooleanField("Published", default=True)
    display_order = IntegerField("Display Order", validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField("Save Testimonial")


class BlogCategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Category")


class BlogPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    excerpt = StringField("Excerpt", validators=[Optional(), Length(max=300)])
    content = TextAreaField("Content", validators=[DataRequired()])
    featured_image = FileField("Featured Image", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "webp", "svg"])])
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    tags = StringField("Tags (comma separated)", validators=[Optional(), Length(max=500)])
    is_published = BooleanField("Published")
    meta_title = StringField("Meta Title", validators=[Optional(), Length(max=70)])
    meta_description = StringField("Meta Description", validators=[Optional(), Length(max=160)])
    meta_keywords = StringField("Meta Keywords", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Post")


class FAQForm(FlaskForm):
    question = StringField("Question", validators=[DataRequired(), Length(max=255)])
    answer = TextAreaField("Answer", validators=[DataRequired()])
    category = StringField("Category", validators=[Optional(), Length(max=100)])
    display_order = IntegerField("Display Order", validators=[Optional(), NumberRange(min=0)], default=0)
    is_published = BooleanField("Published", default=True)
    submit = SubmitField("Save FAQ")


class TeamMemberForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    designation = StringField("Designation", validators=[Optional(), Length(max=120)])
    bio = TextAreaField("Bio", validators=[Optional()])
    photo = FileField("Photo", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"])])
    linkedin_url = StringField("LinkedIn URL", validators=[Optional(), URL(), Length(max=255)])
    twitter_url = StringField("Twitter URL", validators=[Optional(), URL(), Length(max=255)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    display_order = IntegerField("Display Order", validators=[Optional(), NumberRange(min=0)], default=0)
    is_published = BooleanField("Published", default=True)
    submit = SubmitField("Save Team Member")


class CareerForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired(), Length(max=150)])
    department = StringField("Department", validators=[Optional(), Length(max=100)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    employment_type = SelectField(
        "Employment Type",
        choices=[("Full-time", "Full-time"), ("Part-time", "Part-time"), ("Remote", "Remote"), ("Contract", "Contract")],
        validators=[DataRequired()],
    )
    description = TextAreaField("Description", validators=[DataRequired()])
    requirements = TextAreaField("Requirements", validators=[Optional()])
    is_open = BooleanField("Open for Applications", default=True)
    application_deadline = DateField("Application Deadline", validators=[Optional()])
    submit = SubmitField("Save Job Posting")


class WebsiteSettingForm(FlaskForm):
    site_name = StringField("Site Name", validators=[DataRequired(), Length(max=150)])
    site_tagline = StringField("Tagline", validators=[Optional(), Length(max=255)])
    logo = FileField("Logo", validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "svg", "webp"])])
    favicon = FileField("Favicon", validators=[Optional(), FileAllowed(["png", "ico", "svg"])])
    default_meta_title = StringField("Default Meta Title", validators=[Optional(), Length(max=70)])
    default_meta_description = StringField("Default Meta Description", validators=[Optional(), Length(max=160)])
    default_meta_keywords = StringField("Default Meta Keywords", validators=[Optional(), Length(max=255)])
    company_name = StringField("Company Name", validators=[Optional(), Length(max=150)])
    owner_name = StringField("Owner Name", validators=[Optional(), Length(max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    google_business_url = StringField("Google Business Profile URL", validators=[Optional(), URL(), Length(max=255)])
    google_analytics_id = StringField("Google Analytics ID", validators=[Optional(), Length(max=50)])
    google_tag_manager_id = StringField("Google Tag Manager ID", validators=[Optional(), Length(max=50)])
    google_site_verification = StringField("Google Site Verification", validators=[Optional(), Length(max=120)])
    maintenance_mode = BooleanField("Maintenance Mode")
    submit = SubmitField("Save Settings")


class SocialLinkForm(FlaskForm):
    platform = StringField("Platform", validators=[DataRequired(), Length(max=60)])
    icon_class = StringField("Icon Class", validators=[Optional(), Length(max=80)])
    url = StringField("URL", validators=[DataRequired(), URL(), Length(max=255)])
    display_order = IntegerField("Display Order", validators=[Optional(), NumberRange(min=0)], default=0)
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Social Link")
