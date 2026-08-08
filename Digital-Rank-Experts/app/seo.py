"""
Digital Rank Experts - SEO Helpers
-----------------------------------------
Centralized helpers for generating dynamic meta tags, canonical URLs,
Open Graph / Twitter Card data, and JSON-LD structured data.

These helpers return plain dictionaries that templates can unpack, so
future templates just need to call `build_meta(...)` from a route and
render the resulting values — no SEO logic belongs in templates.
"""

import json

from flask import request, current_app

from app.context_processors import _get_cached_site_settings


def build_meta(
    title=None,
    description=None,
    keywords=None,
    image=None,
    canonical=None,
    page_identifier=None,
):
    """
    Build a complete meta-tag context dict for a page, honoring per-page
    SEOSetting overrides (keyed by page_identifier) before falling back
    to explicit arguments and finally to global WebsiteSetting defaults.
    """
    settings = _get_cached_site_settings()
    override = _get_seo_override(page_identifier) if page_identifier else None

    resolved_title = (
        (override.meta_title if override else None)
        or title
        or settings.default_meta_title
        or settings.site_name
    )
    resolved_description = (
        (override.meta_description if override else None)
        or description
        or settings.default_meta_description
        or ""
    )
    resolved_keywords = (
        (override.meta_keywords if override else None)
        or keywords
        or settings.default_meta_keywords
        or ""
    )
    resolved_canonical = (
        (override.canonical_url if override else None) or canonical or request.url
    )
    resolved_image = (
        (override.og_image if override else None) or image or settings.default_og_image or ""
    )

    return {
        "title": _truncate(resolved_title, 70),
        "description": _truncate(resolved_description, 160),
        "keywords": resolved_keywords,
        "canonical_url": resolved_canonical,
        "og_image": resolved_image,
        "og_type": "website",
        "site_name": settings.site_name,
        "twitter_card": "summary_large_image",
    }


def _get_seo_override(page_identifier):
    from app.models import SEOSetting

    return SEOSetting.query.filter_by(page_identifier=page_identifier).first()


def _truncate(value, max_len):
    if not value:
        return ""
    return value if len(value) <= max_len else value[: max_len - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# JSON-LD structured data builders
# ---------------------------------------------------------------------------

def organization_schema():
    """LocalBusiness / Organization structured data for the whole site."""
    settings = _get_cached_site_settings()
    data = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": settings.company_name,
        "founder": settings.owner_name,
        "telephone": settings.phone,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": settings.address,
            "addressLocality": "Lahore",
            "addressRegion": "Punjab",
            "addressCountry": "PK",
        },
        "url": current_app.config.get("SITE_URL"),
        "sameAs": [settings.google_business_url] if settings.google_business_url else [],
    }
    return json.dumps(data)


def breadcrumb_schema(items):
    """
    Build a BreadcrumbList JSON-LD block.
    `items` is a list of (name, url) tuples in order.
    """
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(items)
        ],
    }
    return json.dumps(data)


def blog_posting_schema(post):
    """Article / BlogPosting JSON-LD for a single blog post."""
    settings = _get_cached_site_settings()
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.excerpt or "",
        "datePublished": post.published_at.isoformat() if post.published_at else None,
        "dateModified": post.updated_at.isoformat() if post.updated_at else None,
        "author": {
            "@type": "Person",
            "name": post.author.full_name if post.author else settings.owner_name,
        },
        "publisher": {
            "@type": "Organization",
            "name": settings.company_name,
        },
    }
    return json.dumps({k: v for k, v in data.items() if v is not None})


def faq_page_schema(faqs):
    """FAQPage JSON-LD for a collection of FAQ objects."""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }
    return json.dumps(data)
