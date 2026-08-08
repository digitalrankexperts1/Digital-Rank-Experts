"""
Digital Rank Experts - Context Processors
------------------------------------------------
Injects globally available variables into every template render:
website settings, social links, and the current year.
"""

from app.extensions import cache
from app.utils import get_current_year


def register_context_processors(app):

    @app.context_processor
    def inject_globals():
        return {
            "site_settings": _get_cached_site_settings(),
            "social_links": _get_cached_social_links(),
            "current_year": get_current_year(),
        }


# @cache.memoize(timeout=300)
def _get_cached_site_settings():
    from app.models import WebsiteSetting

    settings = WebsiteSetting.query.first()
    if settings is None:
        # Return a lightweight default object so templates never break
        # before the admin has saved settings for the first time.
        class _DefaultSettings:
            site_name = "Digital Rank Experts"
            site_tagline = "Data-Driven Digital Marketing & SEO Agency"
            logo = None
            favicon = None
            default_meta_title = "Digital Rank Experts | SEO & Digital Marketing Agency"
            default_meta_description = (
                "Digital Rank Experts is a premium digital marketing and SEO "
                "agency based in Lahore, Pakistan, helping brands rank higher "
                "and grow faster."
            )
            default_meta_keywords = "SEO agency, digital marketing, Lahore, Pakistan"
            default_og_image = None
            company_name = "Digital Rank Experts"
            owner_name = "Sohail Ahmad"
            phone = "+92 3297 562092"
            email = None
            address = "Johar Town, Lahore, Pakistan"
            google_business_url = "https://maps.app.goo.gl/uuH6fPQYDqHBzFHE6"
            google_analytics_id = None
            google_tag_manager_id = None
            google_site_verification = None
            maintenance_mode = False

        return _DefaultSettings()
    return settings


# @cache.memoize(timeout=300)
def _get_cached_social_links():
    from app.models import SocialLink

    return SocialLink.query.filter_by(is_active=True).order_by(SocialLink.display_order.asc()).all()
