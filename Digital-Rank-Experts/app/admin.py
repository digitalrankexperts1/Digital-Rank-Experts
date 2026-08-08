"""
Backend for the admin dashboard.

Provides CRUD operations for content models, search, pagination,
filtering, and flash-message feedback.
"""

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db, cache
from app.decorators import permission_required
from app.utils import (
    save_uploaded_file,
    delete_uploaded_file,
    generate_unique_slug,
)
from app.context_processors import (
    _get_cached_site_settings,
    _get_cached_social_links,
)
from app.forms import (
    ServiceForm,
    PortfolioForm,
    TestimonialForm,
    BlogCategoryForm,
    BlogPostForm,
    FAQForm,
    TeamMemberForm,
    CareerForm,
    WebsiteSettingForm,
    SocialLinkForm,
)
from app.models import (
    Service,
    Portfolio,
    Testimonial,
    ContactMessage,
    BlogCategory,
    BlogTag,
    BlogPost,
    FAQ,
    TeamMember,
    Career,
    JobApplication,
    WebsiteSetting,
    SocialLink,
    NewsletterSubscriber,
)


# ============================================================
# ADMIN BLUEPRINT
# ============================================================

admin_bp = Blueprint("admin", __name__)


# ============================================================
# ADMIN LOGIN PROTECTION
# ============================================================

@admin_bp.before_request
@login_required
def require_login():
    """Every admin route requires an authenticated session."""
    pass


# ============================================================
# SEO
# ============================================================

@admin_bp.route("/seo")
@permission_required("manage_settings")
def admin_seo():
    return render_template("admin/seo.html")


# ============================================================
# DASHBOARD
# ============================================================

@admin_bp.route("/")
@admin_bp.route("/dashboard")
def dashboard():

    stats = {
        "services_count": Service.query.count(),
        "portfolio_count": Portfolio.query.count(),
        "blog_posts_count": BlogPost.query.count(),
        "unread_messages_count": ContactMessage.query.filter_by(
            is_read=False
        ).count(),
        "open_careers_count": Career.query.filter_by(
            is_open=True
        ).count(),
        "pending_applications_count": JobApplication.query.filter_by(
            status="submitted"
        ).count(),
        "newsletter_subscribers_count": NewsletterSubscriber.query.filter_by(
            is_active=True
        ).count(),
    }

    recent_messages = (
        ContactMessage.query
        .order_by(ContactMessage.created_at.desc())
        .limit(5)
        .all()
    )

    recent_applications = (
        JobApplication.query
        .order_by(JobApplication.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_messages=recent_messages,
        recent_applications=recent_applications,
    )


# ============================================================
# GENERIC HELPERS
# ============================================================

def _search_filter(query, model, search_term, columns):
    """
    Apply a case-insensitive search across multiple model columns.
    """

    if not search_term:
        return query

    like_term = f"%{search_term}%"

    conditions = [
        getattr(model, column).ilike(like_term)
        for column in columns
    ]

    return query.filter(or_(*conditions))


def _paginated(query):
    """Return a paginated SQLAlchemy query."""

    page = request.args.get("page", 1, type=int)

    per_page = current_app.config.get(
        "ADMIN_ITEMS_PER_PAGE",
        10,
    )

    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )


# ============================================================
# SERVICES
# ============================================================

@admin_bp.route("/services")
@permission_required("manage_services")
def services_list():

    search = request.args.get("q", "").strip()

    query = (
        Service.query
        .order_by(
            Service.display_order.asc(),
            Service.created_at.desc(),
        )
    )

    query = _search_filter(
        query,
        Service,
        search,
        ["title", "short_description"],
    )

    pagination = _paginated(query)

    return render_template(
        "admin/services/list.html",
        pagination=pagination,
        search=search,
    )


@admin_bp.route("/services/create", methods=["GET", "POST"])
@permission_required("manage_services")
def service_create():

    form = ServiceForm()

    if form.validate_on_submit():

        service = Service(
            title=form.title.data,
            slug=generate_unique_slug(
                Service,
                form.title.data,
            ),
            short_description=form.short_description.data,
            description=form.description.data,
            icon=form.icon.data,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
            display_order=form.display_order.data or 0,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
            meta_keywords=form.meta_keywords.data,
        )

        if form.featured_image.data:
            service.featured_image = save_uploaded_file(
                form.featured_image.data,
                subfolder="services",
            )

        db.session.add(service)
        db.session.commit()

        cache.delete_memoized(
            _get_cached_site_settings
        )

        flash(
            "Service created successfully.",
            "success",
        )

        return redirect(
            url_for("admin.services_list")
        )

    return render_template(
        "admin/services/form.html",
        form=form,
        service=None,
    )


@admin_bp.route(
    "/services/<int:service_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_services")
def service_edit(service_id):

    service = Service.query.get_or_404(service_id)

    form = ServiceForm(obj=service)

    if form.validate_on_submit():

        if service.title != form.title.data:
            service.slug = generate_unique_slug(
                Service,
                form.title.data,
                instance_id=service.id,
            )

        service.title = form.title.data
        service.short_description = form.short_description.data
        service.description = form.description.data
        service.icon = form.icon.data
        service.is_featured = form.is_featured.data
        service.is_published = form.is_published.data
        service.display_order = form.display_order.data or 0
        service.meta_title = form.meta_title.data
        service.meta_description = form.meta_description.data
        service.meta_keywords = form.meta_keywords.data

        if form.featured_image.data:

            delete_uploaded_file(
                service.featured_image
            )

            service.featured_image = save_uploaded_file(
                form.featured_image.data,
                subfolder="services",
            )

        db.session.commit()

        cache.delete_memoized(
            _get_cached_site_settings
        )

        flash(
            "Service updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.services_list")
        )

    return render_template(
        "admin/services/form.html",
        form=form,
        service=service,
    )


@admin_bp.route(
    "/services/<int:service_id>/delete",
    methods=["POST"],
)
@permission_required("manage_services")
def service_delete(service_id):

    service = Service.query.get_or_404(service_id)

    delete_uploaded_file(
        service.featured_image
    )

    db.session.delete(service)
    db.session.commit()

    cache.delete_memoized(
        _get_cached_site_settings
    )

    flash(
        "Service deleted.",
        "info",
    )

    return redirect(
        url_for("admin.services_list")
    )


# ============================================================
# PORTFOLIO
# ============================================================

@admin_bp.route("/portfolio")
@permission_required("manage_portfolio")
def portfolio_list():

    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = (
        Portfolio.query
        .order_by(
            Portfolio.display_order.asc(),
            Portfolio.created_at.desc(),
        )
    )

    query = _search_filter(
        query,
        Portfolio,
        search,
        [
            "title",
            "client_name",
            "summary",
        ],
    )

    if category:
        query = query.filter(
            Portfolio.category == category
        )

    pagination = _paginated(query)

    return render_template(
        "admin/portfolio/list.html",
        pagination=pagination,
        search=search,
        category=category,
    )


@admin_bp.route(
    "/portfolio/create",
    methods=["GET", "POST"],
)
@permission_required("manage_portfolio")
def portfolio_create():

    form = PortfolioForm()

    if form.validate_on_submit():

        item = Portfolio(
            title=form.title.data,
            slug=generate_unique_slug(
                Portfolio,
                form.title.data,
            ),
            client_name=form.client_name.data,
            category=form.category.data,
            summary=form.summary.data,
            description=form.description.data,
            project_url=form.project_url.data,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
            display_order=form.display_order.data or 0,
            completed_on=form.completed_on.data,
        )

        if form.featured_image.data:

            item.featured_image = save_uploaded_file(
                form.featured_image.data,
                subfolder="portfolio",
            )

        db.session.add(item)
        db.session.commit()

        flash(
            "Portfolio item created successfully.",
            "success",
        )

        return redirect(
            url_for("admin.portfolio_list")
        )

    return render_template(
        "admin/portfolio/form.html",
        form=form,
        item=None,
    )


@admin_bp.route(
    "/portfolio/<int:item_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_portfolio")
def portfolio_edit(item_id):

    item = Portfolio.query.get_or_404(item_id)

    form = PortfolioForm(obj=item)

    if form.validate_on_submit():

        if item.title != form.title.data:

            item.slug = generate_unique_slug(
                Portfolio,
                form.title.data,
                instance_id=item.id,
            )

        item.title = form.title.data
        item.client_name = form.client_name.data
        item.category = form.category.data
        item.summary = form.summary.data
        item.description = form.description.data
        item.project_url = form.project_url.data
        item.is_featured = form.is_featured.data
        item.is_published = form.is_published.data
        item.display_order = form.display_order.data or 0
        item.completed_on = form.completed_on.data

        if form.featured_image.data:

            delete_uploaded_file(
                item.featured_image
            )

            item.featured_image = save_uploaded_file(
                form.featured_image.data,
                subfolder="portfolio",
            )

        db.session.commit()

        flash(
            "Portfolio item updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.portfolio_list")
        )

    return render_template(
        "admin/portfolio/form.html",
        form=form,
        item=item,
    )


@admin_bp.route(
    "/portfolio/<int:item_id>/delete",
    methods=["POST"],
)
@permission_required("manage_portfolio")
def portfolio_delete(item_id):

    item = Portfolio.query.get_or_404(item_id)

    delete_uploaded_file(
        item.featured_image
    )

    db.session.delete(item)
    db.session.commit()

    flash(
        "Portfolio item deleted.",
        "info",
    )

    return redirect(
        url_for("admin.portfolio_list")
    )


# ============================================================
# TESTIMONIALS
# ============================================================

@admin_bp.route("/testimonials")
@permission_required("manage_testimonials")
def testimonials_list():

    search = request.args.get("q", "").strip()

    query = (
        Testimonial.query
        .order_by(
            Testimonial.display_order.asc(),
            Testimonial.created_at.desc(),
        )
    )

    query = _search_filter(
        query,
        Testimonial,
        search,
        [
            "client_name",
            "client_company",
        ],
    )

    pagination = _paginated(query)

    return render_template(
        "admin/testimonials/list.html",
        pagination=pagination,
        search=search,
    )


@admin_bp.route(
    "/testimonials/create",
    methods=["GET", "POST"],
)
@permission_required("manage_testimonials")
def testimonial_create():

    form = TestimonialForm()

    if form.validate_on_submit():

        testimonial = Testimonial(
            client_name=form.client_name.data,
            client_company=form.client_company.data,
            rating=form.rating.data,
            message=form.message.data,
            is_published=form.is_published.data,
            display_order=form.display_order.data or 0,
        )

        if form.client_photo.data:

            testimonial.client_photo = save_uploaded_file(
                form.client_photo.data,
                subfolder="testimonials",
            )

        db.session.add(testimonial)
        db.session.commit()

        flash(
            "Testimonial created successfully.",
            "success",
        )

        return redirect(
            url_for("admin.testimonials_list")
        )

    return render_template(
        "admin/testimonials/form.html",
        form=form,
        testimonial=None,
    )


@admin_bp.route(
    "/testimonials/<int:testimonial_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_testimonials")
def testimonial_edit(testimonial_id):

    testimonial = Testimonial.query.get_or_404(
        testimonial_id
    )

    form = TestimonialForm(
        obj=testimonial
    )

    if form.validate_on_submit():

        testimonial.client_name = form.client_name.data
        testimonial.client_company = form.client_company.data
        testimonial.rating = form.rating.data
        testimonial.message = form.message.data
        testimonial.is_published = form.is_published.data
        testimonial.display_order = (
            form.display_order.data or 0
        )

        if form.client_photo.data:

            delete_uploaded_file(
                testimonial.client_photo
            )

            testimonial.client_photo = save_uploaded_file(
                form.client_photo.data,
                subfolder="testimonials",
            )

        db.session.commit()

        flash(
            "Testimonial updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.testimonials_list")
        )

    return render_template(
        "admin/testimonials/form.html",
        form=form,
        testimonial=testimonial,
    )


@admin_bp.route(
    "/testimonials/<int:testimonial_id>/delete",
    methods=["POST"],
)
@permission_required("manage_testimonials")
def testimonial_delete(testimonial_id):

    testimonial = Testimonial.query.get_or_404(
        testimonial_id
    )

    delete_uploaded_file(
        testimonial.client_photo
    )

    db.session.delete(testimonial)
    db.session.commit()

    flash(
        "Testimonial deleted.",
        "info",
    )

    return redirect(
        url_for("admin.testimonials_list")
    )


# ============================================================
# CONTACT MESSAGES
# ============================================================

@admin_bp.route("/messages")
@permission_required("manage_messages")
def messages_list():

    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    query = (
        ContactMessage.query
        .order_by(
            ContactMessage.created_at.desc()
        )
    )

    query = _search_filter(
        query,
        ContactMessage,
        search,
        [
            "full_name",
            "email",
            "subject",
        ],
    )

    if status == "read":
        query = query.filter_by(
            is_read=True
        )

    elif status == "unread":
        query = query.filter_by(
            is_read=False
        )

    pagination = _paginated(query)

    return render_template(
        "admin/messages/list.html",
        pagination=pagination,
        search=search,
        status=status,
    )


@admin_bp.route(
    "/messages/<int:message_id>"
)
@permission_required("manage_messages")
def message_detail(message_id):

    message = ContactMessage.query.get_or_404(
        message_id
    )

    if not message.is_read:

        message.is_read = True

        db.session.commit()

    return render_template(
        "admin/messages/detail.html",
        message=message,
    )


@admin_bp.route(
    "/messages/<int:message_id>/delete",
    methods=["POST"],
)
@permission_required("manage_messages")
def message_delete(message_id):

    message = ContactMessage.query.get_or_404(
        message_id
    )

    db.session.delete(message)
    db.session.commit()

    flash(
        "Message deleted.",
        "info",
    )

    return redirect(
        url_for("admin.messages_list")
    )


# ============================================================
# BLOG CATEGORIES
# ============================================================

@admin_bp.route("/blog/categories")
@permission_required("manage_blog")
def blog_categories_list():

    categories = (
        BlogCategory.query
        .order_by(
            BlogCategory.name.asc()
        )
        .all()
    )

    return render_template(
        "admin/blog/categories_list.html",
        categories=categories,
    )


@admin_bp.route(
    "/blog/categories/create",
    methods=["GET", "POST"],
)
@permission_required("manage_blog")
def blog_category_create():

    form = BlogCategoryForm()

    if form.validate_on_submit():

        category = BlogCategory(
            name=form.name.data,
            slug=generate_unique_slug(
                BlogCategory,
                form.name.data,
            ),
            description=form.description.data,
        )

        db.session.add(category)
        db.session.commit()

        flash(
            "Blog category created.",
            "success",
        )

        return redirect(
            url_for("admin.blog_categories_list")
        )

    return render_template(
        "admin/blog/category_form.html",
        form=form,
        category=None,
    )


@admin_bp.route(
    "/blog/categories/<int:category_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_blog")
def blog_category_edit(category_id):

    category = BlogCategory.query.get_or_404(
        category_id
    )

    form = BlogCategoryForm(
        obj=category
    )

    if form.validate_on_submit():

        if category.name != form.name.data:

            category.slug = generate_unique_slug(
                BlogCategory,
                form.name.data,
                instance_id=category.id,
            )

        category.name = form.name.data
        category.description = form.description.data

        db.session.commit()

        flash(
            "Blog category updated.",
            "success",
        )

        return redirect(
            url_for("admin.blog_categories_list")
        )

    return render_template(
        "admin/blog/category_form.html",
        form=form,
        category=category,
    )


@admin_bp.route(
    "/blog/categories/<int:category_id>/delete",
    methods=["POST"],
)
@permission_required("manage_blog")
def blog_category_delete(category_id):

    category = BlogCategory.query.get_or_404(
        category_id
    )

    db.session.delete(category)
    db.session.commit()

    flash(
        "Blog category deleted.",
        "info",
    )

    return redirect(
        url_for("admin.blog_categories_list")
    )


# ============================================================
# BLOG POSTS
# ============================================================

@admin_bp.route("/blog/posts")
@permission_required("manage_blog")
def blog_posts_list():

    search = request.args.get("q", "").strip()

    query = (
        BlogPost.query
        .order_by(
            BlogPost.created_at.desc()
        )
    )

    query = _search_filter(
        query,
        BlogPost,
        search,
        [
            "title",
            "excerpt",
        ],
    )

    pagination = _paginated(query)

    return render_template(
        "admin/blog/posts_list.html",
        pagination=pagination,
        search=search,
    )


def _sync_tags(post, tags_csv):
    """Synchronize blog post tags."""

    post.tags = []

    if not tags_csv:
        return

    for raw_name in tags_csv.split(","):

        name = raw_name.strip()

        if not name:
            continue

        tag = (
            BlogTag.query
            .filter_by(name=name)
            .first()
        )

        if tag is None:

            tag = BlogTag(
                name=name,
                slug=generate_unique_slug(
                    BlogTag,
                    name,
                ),
            )

            db.session.add(tag)

        post.tags.append(tag)


@admin_bp.route(
    "/blog/posts/create",
    methods=["GET", "POST"],
)
@permission_required("manage_blog")
def blog_post_create():

    form = BlogPostForm()

    form.category_id.choices = [
        (0, "— No Category —")
    ] + [
        (category.id, category.name)
        for category in (
            BlogCategory.query
            .order_by(
                BlogCategory.name.asc()
            )
            .all()
        )
    ]

    if form.validate_on_submit():

        post = BlogPost(
            title=form.title.data,
            slug=generate_unique_slug(
                BlogPost,
                form.title.data,
            ),
            excerpt=form.excerpt.data,
            content=form.content.data,
            author_id=current_user.id,
            category_id=form.category_id.data or None,
            is_published=form.is_published.data,
            published_at=(
                datetime.utcnow()
                if form.is_published.data
                else None
            ),
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
            meta_keywords=form.meta_keywords.data,
        )

        if form.featured_image.data:

            post.featured_image = save_uploaded_file(
                form.featured_image.data,
                subfolder="blog",
            )

        _sync_tags(
            post,
            form.tags.data,
        )

        db.session.add(post)
        db.session.commit()

        flash(
            "Blog post created successfully.",
            "success",
        )

        return redirect(
            url_for("admin.blog_posts_list")
        )

    return render_template(
        "admin/blog/post_form.html",
        form=form,
        post=None,
    )


@admin_bp.route(
    "/blog/posts/<int:post_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_blog")
def blog_post_edit(post_id):

    post = BlogPost.query.get_or_404(
        post_id
    )

    form = BlogPostForm(
        obj=post
    )

    form.category_id.choices = [
        (0, "— No Category —")
    ] + [
        (category.id, category.name)
        for category in (
            BlogCategory.query
            .order_by(
                BlogCategory.name.asc()
            )
            .all()
        )
    ]

    if request.method == "GET":

        form.tags.data = ", ".join(
            tag.name
            for tag in post.tags
        )

        form.category_id.data = (
            post.category_id or 0
        )

    if form.validate_on_submit():

        if post.title != form.title.data:

            post.slug = generate_unique_slug(
                BlogPost,
                form.title.data,
                instance_id=post.id,
            )

        post.title = form.title.data
        post.excerpt = form.excerpt.data
        post.content = form.content.data
        post.category_id = (
            form.category_id.data or None
        )

        if (
            form.is_published.data
            and not post.is_published
        ):
            post.published_at = datetime.utcnow()

        post.is_published = (
            form.is_published.data
        )

        post.meta_title = form.meta_title.data
        post.meta_description = (
            form.meta_description.data
        )
        post.meta_keywords = (
            form.meta_keywords.data
        )

        if form.featured_image.data:

            delete_uploaded_file(
                post.featured_image
            )

            post.featured_image = save_uploaded_file(
                form.featured_image.data,
                subfolder="blog",
            )

        _sync_tags(
            post,
            form.tags.data,
        )

        db.session.commit()

        flash(
            "Blog post updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.blog_posts_list")
        )

    return render_template(
        "admin/blog/post_form.html",
        form=form,
        post=post,
    )


@admin_bp.route(
    "/blog/posts/<int:post_id>/delete",
    methods=["POST"],
)
@permission_required("manage_blog")
def blog_post_delete(post_id):

    post = BlogPost.query.get_or_404(
        post_id
    )

    delete_uploaded_file(
        post.featured_image
    )

    db.session.delete(post)
    db.session.commit()

    flash(
        "Blog post deleted.",
        "info",
    )

    return redirect(
        url_for("admin.blog_posts_list")
    )


# ============================================================
# FAQS
# ============================================================

@admin_bp.route("/faqs")
@permission_required("manage_faqs")
def faqs_list():

    search = request.args.get("q", "").strip()

    query = (
        FAQ.query
        .order_by(
            FAQ.display_order.asc()
        )
    )

    query = _search_filter(
        query,
        FAQ,
        search,
        [
            "question",
            "category",
        ],
    )

    pagination = _paginated(query)

    return render_template(
        "admin/faqs/list.html",
        pagination=pagination,
        search=search,
    )


@admin_bp.route(
    "/faqs/create",
    methods=["GET", "POST"],
)
@permission_required("manage_faqs")
def faq_create():

    form = FAQForm()

    if form.validate_on_submit():

        faq = FAQ(
            question=form.question.data,
            answer=form.answer.data,
            category=form.category.data,
            display_order=form.display_order.data or 0,
            is_published=form.is_published.data,
        )

        db.session.add(faq)
        db.session.commit()

        flash(
            "FAQ created successfully.",
            "success",
        )

        return redirect(
            url_for("admin.faqs_list")
        )

    return render_template(
        "admin/faqs/form.html",
        form=form,
        faq=None,
    )


@admin_bp.route(
    "/faqs/<int:faq_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_faqs")
def faq_edit(faq_id):

    faq = FAQ.query.get_or_404(
        faq_id
    )

    form = FAQForm(
        obj=faq
    )

    if form.validate_on_submit():

        faq.question = form.question.data
        faq.answer = form.answer.data
        faq.category = form.category.data
        faq.display_order = (
            form.display_order.data or 0
        )
        faq.is_published = (
            form.is_published.data
        )

        db.session.commit()

        flash(
            "FAQ updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.faqs_list")
        )

    return render_template(
        "admin/faqs/form.html",
        form=form,
        faq=faq,
    )


@admin_bp.route(
    "/faqs/<int:faq_id>/delete",
    methods=["POST"],
)
@permission_required("manage_faqs")
def faq_delete(faq_id):

    faq = FAQ.query.get_or_404(
        faq_id
    )

    db.session.delete(faq)
    db.session.commit()

    flash(
        "FAQ deleted.",
        "info",
    )

    return redirect(
        url_for("admin.faqs_list")
    )


# ============================================================
# TEAM MEMBERS
# ============================================================

@admin_bp.route("/team")
@permission_required("manage_team")
def team_list():

    search = request.args.get("q", "").strip()

    query = (
        TeamMember.query
        .order_by(
            TeamMember.display_order.asc()
        )
    )

    query = _search_filter(
        query,
        TeamMember,
        search,
        [
            "full_name",
            "designation",
        ],
    )

    pagination = _paginated(query)

    return render_template(
        "admin/team/list.html",
        pagination=pagination,
        search=search,
    )


@admin_bp.route(
    "/team/create",
    methods=["GET", "POST"],
)
@permission_required("manage_team")
def team_member_create():

    form = TeamMemberForm()

    if form.validate_on_submit():

        member = TeamMember(
            full_name=form.full_name.data,
            designation=form.designation.data,
            bio=form.bio.data,
            linkedin_url=form.linkedin_url.data,
            twitter_url=form.twitter_url.data,
            email=form.email.data,
            display_order=form.display_order.data or 0,
            is_published=form.is_published.data,
        )

        if form.photo.data:

            member.photo = save_uploaded_file(
                form.photo.data,
                subfolder="team",
            )

        db.session.add(member)
        db.session.commit()

        flash(
            "Team member added successfully.",
            "success",
        )

        return redirect(
            url_for("admin.team_list")
        )

    return render_template(
        "admin/team/form.html",
        form=form,
        member=None,
    )


@admin_bp.route(
    "/team/<int:member_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_team")
def team_member_edit(member_id):

    member = TeamMember.query.get_or_404(
        member_id
    )

    form = TeamMemberForm(
        obj=member
    )

    if form.validate_on_submit():

        member.full_name = form.full_name.data
        member.designation = form.designation.data
        member.bio = form.bio.data
        member.linkedin_url = form.linkedin_url.data
        member.twitter_url = form.twitter_url.data
        member.email = form.email.data
        member.display_order = (
            form.display_order.data or 0
        )
        member.is_published = (
            form.is_published.data
        )

        if form.photo.data:

            delete_uploaded_file(
                member.photo
            )

            member.photo = save_uploaded_file(
                form.photo.data,
                subfolder="team",
            )

        db.session.commit()

        flash(
            "Team member updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.team_list")
        )

    return render_template(
        "admin/team/form.html",
        form=form,
        member=member,
    )


@admin_bp.route(
    "/team/<int:member_id>/delete",
    methods=["POST"],
)
@permission_required("manage_team")
def team_member_delete(member_id):

    member = TeamMember.query.get_or_404(
        member_id
    )

    delete_uploaded_file(
        member.photo
    )

    db.session.delete(member)
    db.session.commit()

    flash(
        "Team member removed.",
        "info",
    )

    return redirect(
        url_for("admin.team_list")
    )


# ============================================================
# CAREERS
# ============================================================

@admin_bp.route("/careers")
@permission_required("manage_careers")
def careers_list():

    search = request.args.get("q", "").strip()

    query = (
        Career.query
        .order_by(
            Career.created_at.desc()
        )
    )

    query = _search_filter(
        query,
        Career,
        search,
        [
            "title",
            "department",
        ],
    )

    pagination = _paginated(query)

    return render_template(
        "admin/careers/list.html",
        pagination=pagination,
        search=search,
    )


@admin_bp.route(
    "/careers/create",
    methods=["GET", "POST"],
)
@permission_required("manage_careers")
def career_create():

    form = CareerForm()

    if form.validate_on_submit():

        career = Career(
            title=form.title.data,
            slug=generate_unique_slug(
                Career,
                form.title.data,
            ),
            department=form.department.data,
            location=form.location.data,
            employment_type=form.employment_type.data,
            description=form.description.data,
            requirements=form.requirements.data,
            is_open=form.is_open.data,
            application_deadline=form.application_deadline.data,
        )

        db.session.add(career)
        db.session.commit()

        flash(
            "Job posting created successfully.",
            "success",
        )

        return redirect(
            url_for("admin.careers_list")
        )

    return render_template(
        "admin/careers/form.html",
        form=form,
        career=None,
    )


@admin_bp.route(
    "/careers/<int:career_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_careers")
def career_edit(career_id):

    career = Career.query.get_or_404(
        career_id
    )

    form = CareerForm(
        obj=career
    )

    if form.validate_on_submit():

        if career.title != form.title.data:

            career.slug = generate_unique_slug(
                Career,
                form.title.data,
                instance_id=career.id,
            )

        career.title = form.title.data
        career.department = form.department.data
        career.location = form.location.data
        career.employment_type = (
            form.employment_type.data
        )
        career.description = (
            form.description.data
        )
        career.requirements = (
            form.requirements.data
        )
        career.is_open = form.is_open.data
        career.application_deadline = (
            form.application_deadline.data
        )

        db.session.commit()

        flash(
            "Job posting updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.careers_list")
        )

    return render_template(
        "admin/careers/form.html",
        form=form,
        career=career,
    )


@admin_bp.route(
    "/careers/<int:career_id>/delete",
    methods=["POST"],
)
@permission_required("manage_careers")
def career_delete(career_id):

    career = Career.query.get_or_404(
        career_id
    )

    db.session.delete(career)
    db.session.commit()

    flash(
        "Job posting deleted.",
        "info",
    )

    return redirect(
        url_for("admin.careers_list")
    )


# ============================================================
# JOB APPLICATIONS
# ============================================================

@admin_bp.route("/careers/applications")
@permission_required("manage_careers")
def job_applications_list():

    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    query = (
        JobApplication.query
        .order_by(
            JobApplication.created_at.desc()
        )
    )

    query = _search_filter(
        query,
        JobApplication,
        search,
        [
            "full_name",
            "email",
        ],
    )

    if status:
        query = query.filter_by(
            status=status
        )

    pagination = _paginated(query)

    return render_template(
        "admin/careers/applications_list.html",
        pagination=pagination,
        search=search,
        status=status,
    )


@admin_bp.route(
    "/careers/applications/<int:application_id>"
)
@permission_required("manage_careers")
def job_application_detail(application_id):

    application = JobApplication.query.get_or_404(
        application_id
    )

    return render_template(
        "admin/careers/application_detail.html",
        application=application,
    )


@admin_bp.route(
    "/careers/applications/<int:application_id>/status",
    methods=["POST"],
)
@permission_required("manage_careers")
def job_application_update_status(
    application_id
):

    application = JobApplication.query.get_or_404(
        application_id
    )

    new_status = request.form.get(
        "status"
    )

    valid_statuses = {
        "submitted",
        "reviewing",
        "shortlisted",
        "interviewed",
        "hired",
        "rejected",
    }

    if new_status in valid_statuses:

        application.status = new_status

        db.session.commit()

        flash(
            "Application status updated.",
            "success",
        )

    else:

        flash(
            "Invalid status.",
            "danger",
        )

    return redirect(
        url_for(
            "admin.job_application_detail",
            application_id=application.id,
        )
    )


# ============================================================
# WEBSITE SETTINGS
# ============================================================

@admin_bp.route(
    "/settings",
    methods=["GET", "POST"],
)
@permission_required("manage_settings")
def website_settings():

    settings = WebsiteSetting.query.first()

    if settings is None:

        settings = WebsiteSetting()

        db.session.add(settings)
        db.session.commit()

    form = WebsiteSettingForm(
        obj=settings
    )

    if form.validate_on_submit():

        settings.site_name = form.site_name.data
        settings.site_tagline = form.site_tagline.data
        settings.default_meta_title = (
            form.default_meta_title.data
        )
        settings.default_meta_description = (
            form.default_meta_description.data
        )
        settings.default_meta_keywords = (
            form.default_meta_keywords.data
        )
        settings.company_name = (
            form.company_name.data
        )
        settings.owner_name = (
            form.owner_name.data
        )
        settings.phone = form.phone.data
        settings.email = form.email.data
        settings.address = form.address.data
        settings.google_business_url = (
            form.google_business_url.data
        )
        settings.google_analytics_id = (
            form.google_analytics_id.data
        )
        settings.google_tag_manager_id = (
            form.google_tag_manager_id.data
        )
        settings.google_site_verification = (
            form.google_site_verification.data
        )
        settings.maintenance_mode = (
            form.maintenance_mode.data
        )

        if form.logo.data:

            delete_uploaded_file(
                settings.logo
            )

            settings.logo = save_uploaded_file(
                form.logo.data,
                subfolder="branding",
            )

        if form.favicon.data:

            delete_uploaded_file(
                settings.favicon
            )

            settings.favicon = save_uploaded_file(
                form.favicon.data,
                subfolder="branding",
                allowed_extensions={
                    "png",
                    "ico",
                    "svg",
                },
            )

        db.session.commit()

        cache.delete_memoized(
            _get_cached_site_settings
        )

        flash(
            "Website settings updated successfully.",
            "success",
        )

        return redirect(
            url_for("admin.website_settings")
        )

    return render_template(
        "admin/settings/website.html",
        form=form,
        settings=settings,
    )


# ============================================================
# SOCIAL LINKS
# ============================================================

@admin_bp.route(
    "/settings/social-links"
)
@permission_required("manage_settings")
def social_links_list():

    links = (
        SocialLink.query
        .order_by(
            SocialLink.display_order.asc()
        )
        .all()
    )

    return render_template(
        "admin/settings/social_links_list.html",
        links=links,
    )


@admin_bp.route(
    "/settings/social-links/create",
    methods=["GET", "POST"],
)
@permission_required("manage_settings")
def social_link_create():

    form = SocialLinkForm()

    if form.validate_on_submit():

        link = SocialLink(
            platform=form.platform.data,
            icon_class=form.icon_class.data,
            url=form.url.data,
            display_order=form.display_order.data or 0,
            is_active=form.is_active.data,
        )

        db.session.add(link)
        db.session.commit()

        cache.delete_memoized(
            _get_cached_social_links
        )

        flash(
            "Social link added.",
            "success",
        )

        return redirect(
            url_for("admin.social_links_list")
        )

    return render_template(
        "admin/settings/social_link_form.html",
        form=form,
        link=None,
    )


@admin_bp.route(
    "/settings/social-links/<int:link_id>/edit",
    methods=["GET", "POST"],
)
@permission_required("manage_settings")
def social_link_edit(link_id):

    link = SocialLink.query.get_or_404(
        link_id
    )

    form = SocialLinkForm(
        obj=link
    )

    if form.validate_on_submit():

        link.platform = form.platform.data
        link.icon_class = form.icon_class.data
        link.url = form.url.data
        link.display_order = (
            form.display_order.data or 0
        )
        link.is_active = form.is_active.data

        db.session.commit()

        cache.delete_memoized(
            _get_cached_social_links
        )

        flash(
            "Social link updated.",
            "success",
        )

        return redirect(
            url_for("admin.social_links_list")
        )

    return render_template(
        "admin/settings/social_link_form.html",
        form=form,
        link=link,
    )


@admin_bp.route(
    "/settings/social-links/<int:link_id>/delete",
    methods=["POST"],
)
@permission_required("manage_settings")
def social_link_delete(link_id):

    link = SocialLink.query.get_or_404(
        link_id
    )

    db.session.delete(link)
    db.session.commit()

    cache.delete_memoized(
        _get_cached_social_links
    )

    flash(
        "Social link removed.",
        "info",
    )

    return redirect(
        url_for("admin.social_links_list")
    )