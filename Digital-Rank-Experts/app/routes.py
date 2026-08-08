"""
Digital Rank Experts - Main Routes
-----------------------------------
All customer-facing routes:
home, about, services, portfolio, blog,
contact, careers, FAQs, newsletter,
search, robots.txt and sitemap.xml.
"""

import uuid
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    current_app,
)

from app.extensions import db, limiter, cache

from app.forms import (
    ContactForm,
    NewsletterForm,
    JobApplicationForm,
)

from app.models import (
    Service,
    Portfolio,
    Testimonial,
    BlogPost,
    BlogCategory,
    FAQ,
    TeamMember,
    Career,
    NewsletterSubscriber,
    ContactMessage,
    JobApplication,
)

from app.utils import (
    save_uploaded_file,
    get_client_ip,
)

from app.email import (
    send_contact_form_notification,
    send_contact_form_autoreply,
    send_newsletter_confirmation,
    send_job_application_notification,
)

from app.seo import (
    build_meta,
    organization_schema,
    breadcrumb_schema,
    blog_posting_schema,
    faq_page_schema,
)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@main_bp.route("/")
def index():
    featured_services = (
        Service.query
        .filter_by(is_published=True, is_featured=True)
        .order_by(Service.display_order.asc())
        .limit(6)
        .all()
    )

    featured_portfolio = (
        Portfolio.query
        .filter_by(is_published=True, is_featured=True)
        .order_by(Portfolio.display_order.asc())
        .limit(6)
        .all()
    )

    testimonials = (
        Testimonial.query
        .filter_by(is_published=True)
        .order_by(Testimonial.display_order.asc())
        .limit(6)
        .all()
    )

    latest_posts = (
        BlogPost.query
        .filter_by(is_published=True)
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )

    meta = build_meta(
        page_identifier="home"
    )

    return render_template(
        "index.html",
        featured_services=featured_services,
        featured_portfolio=featured_portfolio,
        testimonials=testimonials,
        latest_posts=latest_posts,
        meta=meta,
        organization_schema=organization_schema(),
    )


# Keep compatibility if any Python code uses main.home
main_bp.add_url_rule(
    "/",
    endpoint="home",
    view_func=index,
)


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------

@main_bp.route("/about")
def about():
    team_members = (
        TeamMember.query
        .filter_by(is_published=True)
        .order_by(TeamMember.display_order.asc())
        .all()
    )

    meta = build_meta(
        title="About Us | Digital Rank Experts",
        description=(
            "Meet Digital Rank Experts, a Lahore-based SEO "
            "and digital marketing agency led by Sohail Ahmad."
        ),
        page_identifier="about",
    )

    return render_template(
        "about.html",
        team_members=team_members,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

@main_bp.route("/services")
def services():
    all_services = (
        Service.query
        .filter_by(is_published=True)
        .order_by(Service.display_order.asc())
        .all()
    )

    meta = build_meta(
        title="Our Services | Digital Rank Experts",
        description=(
            "Explore SEO, PPC, social media, and web design "
            "services from Digital Rank Experts."
        ),
        page_identifier="services",
    )

    return render_template(
        "services.html",
        services=all_services,
        meta=meta,
    )


@main_bp.route("/services/<slug>")
def service_detail(slug):
    service = (
        Service.query
        .filter_by(
            slug=slug,
            is_published=True,
        )
        .first_or_404()
    )

    related_services = (
        Service.query
        .filter(
            Service.id != service.id,
            Service.is_published.is_(True),
        )
        .order_by(Service.display_order.asc())
        .limit(3)
        .all()
    )

    meta = build_meta(
        title=service.meta_title or service.title,
        description=(
            service.meta_description
            or service.short_description
            or ""
        ),
        keywords=service.meta_keywords,
        page_identifier=f"service:{service.slug}",
    )

    breadcrumbs = breadcrumb_schema(
        [
            (
                "Home",
                url_for(
                    "main.index",
                    _external=True,
                ),
            ),
            (
                "Services",
                url_for(
                    "main.services",
                    _external=True,
                ),
            ),
            (
                service.title,
                url_for(
                    "main.service_detail",
                    slug=service.slug,
                    _external=True,
                ),
            ),
        ]
    )

    return render_template(
        "service_detail.html",
        service=service,
        related_services=related_services,
        meta=meta,
        breadcrumb_schema=breadcrumbs,
    )


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@main_bp.route("/portfolio")
def portfolio():
    page = request.args.get(
        "page",
        1,
        type=int,
    )

    category = request.args.get(
        "category",
        "",
    ).strip()

    query = (
        Portfolio.query
        .filter_by(is_published=True)
        .order_by(Portfolio.display_order.asc())
    )

    if category:
        query = query.filter_by(
            category=category
        )

    pagination = query.paginate(
        page=page,
        per_page=current_app.config.get(
            "PORTFOLIO_PER_PAGE",
            12,
        ),
        error_out=False,
    )

    categories = [
        row[0]
        for row in (
            db.session
            .query(Portfolio.category)
            .filter(
                Portfolio.category.isnot(None)
            )
            .distinct()
            .all()
        )
    ]

    meta = build_meta(
        title="Our Portfolio | Digital Rank Experts",
        description=(
            "Browse case studies and projects "
            "delivered by Digital Rank Experts."
        ),
        page_identifier="portfolio",
    )

    return render_template(
        "portfolio.html",
        pagination=pagination,
        categories=categories,
        active_category=category,
        meta=meta,
    )


@main_bp.route("/portfolio/<slug>")
def portfolio_detail(slug):
    item = (
        Portfolio.query
        .filter_by(
            slug=slug,
            is_published=True,
        )
        .first_or_404()
    )

    meta = build_meta(
        title=item.meta_title or item.title,
        description=(
            item.meta_description
            or item.summary
            or ""
        ),
        page_identifier=f"portfolio:{item.slug}",
    )

    return render_template(
        "portfolio_detail.html",
        item=item,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Blog
# ---------------------------------------------------------------------------

@main_bp.route("/blog")
def blog():
    page = request.args.get(
        "page",
        1,
        type=int,
    )

    category_slug = request.args.get(
        "category",
        "",
    ).strip()

    tag_slug = request.args.get(
        "tag",
        "",
    ).strip()

    query = (
        BlogPost.query
        .filter_by(is_published=True)
        .order_by(BlogPost.published_at.desc())
    )

    if category_slug:
        category = (
            BlogCategory.query
            .filter_by(slug=category_slug)
            .first()
        )

        if category:
            query = query.filter_by(
                category_id=category.id
            )

    if tag_slug:
        query = query.filter(
            BlogPost.tags.any(
                slug=tag_slug
            )
        )

    pagination = query.paginate(
        page=page,
        per_page=current_app.config.get(
            "POSTS_PER_PAGE",
            10,
        ),
        error_out=False,
    )

    categories = (
        BlogCategory.query
        .order_by(BlogCategory.name.asc())
        .all()
    )

    meta = build_meta(
        title="Blog | Digital Rank Experts",
        description=(
            "SEO tips, digital marketing insights, "
            "and industry news from Digital Rank Experts."
        ),
        page_identifier="blog",
    )

    return render_template(
        "blog.html",
        pagination=pagination,
        categories=categories,
        active_category=category_slug,
        active_tag=tag_slug,
        meta=meta,
    )


@main_bp.route("/blog/<slug>")
def blog_detail(slug):
    post = (
        BlogPost.query
        .filter_by(
            slug=slug,
            is_published=True,
        )
        .first_or_404()
    )

    post.views_count = (
        post.views_count or 0
    ) + 1

    db.session.commit()

    related_posts = (
        BlogPost.query
        .filter(
            BlogPost.id != post.id,
            BlogPost.is_published.is_(True),
            BlogPost.category_id == post.category_id,
        )
        .order_by(
            BlogPost.published_at.desc()
        )
        .limit(3)
        .all()
    )

    meta = build_meta(
        title=post.meta_title or post.title,
        description=(
            post.meta_description
            or post.excerpt
            or ""
        ),
        keywords=post.meta_keywords,
        image=post.featured_image,
        page_identifier=f"blog:{post.slug}",
    )

    return render_template(
        "blog_detail.html",
        post=post,
        related_posts=related_posts,
        meta=meta,
        article_schema=blog_posting_schema(post),
    )


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@main_bp.route(
    "/contact",
    methods=["GET", "POST"],
)
@limiter.limit("5 per minute")
def contact():
    form = ContactForm()

    if form.validate_on_submit():
        message = ContactMessage(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get(
                "User-Agent",
                "",
            )[:255],
        )

        db.session.add(message)
        db.session.commit()

        send_contact_form_notification(
            message
        )

        send_contact_form_autoreply(
            message
        )

        flash(
            "Thank you! Your message has been sent. "
            "We'll get back to you soon.",
            "success",
        )

        return redirect(
            url_for("main.contact")
        )

    meta = build_meta(
        title="Contact Us | Digital Rank Experts",
        description=(
            "Get in touch with Digital Rank Experts "
            "in Johar Town, Lahore, Pakistan."
        ),
        page_identifier="contact",
    )

    return render_template(
        "contact.html",
        form=form,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# FAQs
# ---------------------------------------------------------------------------

@main_bp.route("/faqs")
def faqs():
    all_faqs = (
        FAQ.query
        .filter_by(is_published=True)
        .order_by(FAQ.display_order.asc())
        .all()
    )

    meta = build_meta(
        title=(
            "Frequently Asked Questions | "
            "Digital Rank Experts"
        ),
        description=(
            "Answers to common questions about our "
            "SEO and digital marketing services."
        ),
        page_identifier="faqs",
    )

    return render_template(
        "faqs.html",
        faqs=all_faqs,
        meta=meta,
        faq_schema=faq_page_schema(
            all_faqs
        ),
    )


# ---------------------------------------------------------------------------
# Careers
# ---------------------------------------------------------------------------

@main_bp.route("/careers")
def careers():
    open_positions = (
        Career.query
        .filter_by(is_open=True)
        .order_by(Career.created_at.desc())
        .all()
    )

    meta = build_meta(
        title="Careers | Digital Rank Experts",
        description=(
            "Join the Digital Rank Experts team "
            "in Lahore, Pakistan."
        ),
        page_identifier="careers",
    )

    return render_template(
        "careers.html",
        positions=open_positions,
        meta=meta,
    )


@main_bp.route(
    "/careers/<slug>",
    methods=["GET", "POST"],
)
@limiter.limit(
    "5 per minute",
    methods=["POST"],
)
def career_detail(slug):
    career = (
        Career.query
        .filter_by(slug=slug)
        .first_or_404()
    )

    form = JobApplicationForm()

    if form.validate_on_submit():
        resume_path = save_uploaded_file(
            form.resume_file.data,
            subfolder="resumes",
            allowed_extensions=current_app.config[
                "ALLOWED_DOCUMENT_EXTENSIONS"
            ],
        )

        application = JobApplication(
            career_id=career.id,
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            cover_letter=form.cover_letter.data,
            resume_file=resume_path,
            portfolio_url=form.portfolio_url.data,
        )

        db.session.add(application)
        db.session.commit()

        send_job_application_notification(
            application
        )

        flash(
            "Your application has been submitted "
            "successfully. Good luck!",
            "success",
        )

        return redirect(
            url_for(
                "main.career_detail",
                slug=career.slug,
            )
        )

    description = (
        career.description or ""
    )

    meta = build_meta(
        title=(
            f"{career.title} | Careers | "
            "Digital Rank Experts"
        ),
        description=description[:160],
        page_identifier=f"career:{career.slug}",
    )

    return render_template(
        "career_detail.html",
        career=career,
        form=form,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

@main_bp.route(
    "/newsletter/subscribe",
    methods=["POST"],
)
@limiter.limit("5 per minute")
def newsletter_subscribe():
    form = NewsletterForm()

    if form.validate_on_submit():
        email = (
            form.email.data
            .lower()
            .strip()
        )

        existing = (
            NewsletterSubscriber.query
            .filter_by(email=email)
            .first()
        )

        if existing is None:
            subscriber = NewsletterSubscriber(
                email=email,
                unsubscribe_token=uuid.uuid4().hex,
            )

            db.session.add(subscriber)
            db.session.commit()

            send_newsletter_confirmation(
                subscriber
            )

            flash(
                "You're subscribed! Check your inbox "
                "for a confirmation email.",
                "success",
            )

        else:
            flash(
                "You're already subscribed "
                "to our newsletter.",
                "info",
            )

    else:
        flash(
            "Please provide a valid email address.",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for("main.index")
    )


@main_bp.route(
    "/newsletter/unsubscribe/<token>"
)
def newsletter_unsubscribe(token):
    subscriber = (
        NewsletterSubscriber.query
        .filter_by(
            unsubscribe_token=token
        )
        .first_or_404()
    )

    subscriber.is_active = False
    db.session.commit()

    flash(
        "You have been unsubscribed "
        "from our newsletter.",
        "info",
    )

    return redirect(
        url_for("main.index")
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@main_bp.route("/search")
def search():
    query = request.args.get(
        "q",
        "",
    ).strip()

    services = []
    posts = []
    portfolio_items = []

    if query:
        search_term = f"%{query}%"

        services = (
            Service.query
            .filter(
                Service.is_published.is_(True),
                Service.title.ilike(search_term),
            )
            .order_by(
                Service.display_order.asc()
            )
            .all()
        )

        posts = (
            BlogPost.query
            .filter(
                BlogPost.is_published.is_(True),
                BlogPost.title.ilike(search_term),
            )
            .order_by(
                BlogPost.published_at.desc()
            )
            .limit(20)
            .all()
        )

        portfolio_items = (
            Portfolio.query
            .filter(
                Portfolio.is_published.is_(True),
                Portfolio.title.ilike(search_term),
            )
            .order_by(
                Portfolio.display_order.asc()
            )
            .limit(20)
            .all()
        )

    meta = build_meta(
        title="Search | Digital Rank Experts",
        description=(
            "Search Digital Rank Experts "
            "services, portfolio and blog."
        ),
        page_identifier="search",
    )

    return render_template(
        "search.html",
        query=query,
        services=services,
        posts=posts,
        portfolio_items=portfolio_items,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Robots.txt
# ---------------------------------------------------------------------------

@main_bp.route("/robots.txt")
def robots_txt():
    site_url = (
        current_app.config["SITE_URL"]
        .rstrip("/")
    )

    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /auth/",
        "Disallow: /static/uploads/",
        f"Sitemap: {site_url}/sitemap.xml",
    ]

    return Response(
        "\n".join(lines),
        mimetype="text/plain",
    )


# ---------------------------------------------------------------------------
# Sitemap.xml
# ---------------------------------------------------------------------------

@main_bp.route("/sitemap.xml")
@cache.cached(timeout=3600)
def sitemap_xml():
    site_url = (
        current_app.config["SITE_URL"]
        .rstrip("/")
    )

    static_pages = [
        ("/", 1.0),
        ("/about", 0.8),
        ("/services", 0.9),
        ("/portfolio", 0.8),
        ("/blog", 0.8),
        ("/faqs", 0.6),
        ("/careers", 0.6),
        ("/contact", 0.7),
    ]

    urls = [
        {
            "loc": f"{site_url}{path}",
            "priority": priority,
            "lastmod": None,
        }
        for path, priority in static_pages
    ]

    # Services
    for service in (
        Service.query
        .filter_by(is_published=True)
        .all()
    ):
        lastmod = None

        if service.updated_at:
            lastmod = (
                service.updated_at
                .date()
                .isoformat()
            )

        urls.append(
            {
                "loc": (
                    f"{site_url}/services/"
                    f"{service.slug}"
                ),
                "priority": 0.7,
                "lastmod": lastmod,
            }
        )

    # Portfolio
    for item in (
        Portfolio.query
        .filter_by(is_published=True)
        .all()
    ):
        lastmod = None

        if item.updated_at:
            lastmod = (
                item.updated_at
                .date()
                .isoformat()
            )

        urls.append(
            {
                "loc": (
                    f"{site_url}/portfolio/"
                    f"{item.slug}"
                ),
                "priority": 0.6,
                "lastmod": lastmod,
            }
        )

    # Blog
    for post in (
        BlogPost.query
        .filter_by(is_published=True)
        .all()
    ):
        lastmod = None

        if post.updated_at:
            lastmod = (
                post.updated_at
                .date()
                .isoformat()
            )

        urls.append(
            {
                "loc": (
                    f"{site_url}/blog/"
                    f"{post.slug}"
                ),
                "priority": 0.6,
                "lastmod": lastmod,
            }
        )

    # Careers
    for career in (
        Career.query
        .filter_by(is_open=True)
        .all()
    ):
        lastmod = None

        if career.updated_at:
            lastmod = (
                career.updated_at
                .date()
                .isoformat()
            )

        urls.append(
            {
                "loc": (
                    f"{site_url}/careers/"
                    f"{career.slug}"
                ),
                "priority": 0.5,
                "lastmod": lastmod,
            }
        )

    # XML
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            '<urlset xmlns='
            '"http://www.sitemaps.org/schemas/'
            'sitemap/0.9">'
        ),
    ]

    for item in urls:
        xml_parts.append("<url>")

        xml_parts.append(
            f"<loc>{item['loc']}</loc>"
        )

        if item["lastmod"]:
            xml_parts.append(
                f"<lastmod>{item['lastmod']}</lastmod>"
            )

        xml_parts.append(
            f"<priority>{item['priority']}</priority>"
        )

        xml_parts.append("</url>")

    xml_parts.append("</urlset>")

    return Response(
        "\n".join(xml_parts),
        mimetype="application/xml",
    )


# ---------------------------------------------------------------------------
# Current date/time
# ---------------------------------------------------------------------------

@main_bp.context_processor
def inject_current_year():
    return {
        "now": datetime.utcnow()
    }