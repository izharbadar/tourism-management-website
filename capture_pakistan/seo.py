import os
import re

from datetime import date, datetime
from decimal import Decimal
from html import unescape
from pathlib import Path

from flask import current_app, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError


SITE_NAME = "Capture Pakistan Tourism"

DEFAULT_DESCRIPTION = (
    "Explore Pakistan tours, private trips, trekking expeditions, "
    "cultural journeys and customized travel packages with "
    "Capture Pakistan Tourism."
)

DEFAULT_OG_IMAGE = "images/hero.jpg"

DEFAULT_CURRENCY = "PKR"


def slugify(value):
    value = str(value or "").strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return value.strip("-")


def get_site_url():
    value = (
        os.getenv("SITE_URL")
        or current_app.config.get("SITE_URL")
        or request.url_root
    )

    value = str(value or "").strip()

    if not value:
        value = request.url_root

    return value.rstrip("/")


def absolute_url(value):
    value = str(value or "").strip()

    if not value:
        return get_site_url()

    if value.startswith(
        (
            "http://",
            "https://",
        )
    ):
        return value

    if value.startswith("//"):
        return "https:" + value

    site_url = get_site_url()

    if value.startswith("/"):
        return site_url + value

    if value.startswith("static/"):
        return (
            site_url
            + "/"
            + value.lstrip("/")
        )

    return (
        site_url
        + "/static/"
        + value.lstrip("/")
    )


def _clean_text(value):
    value = str(value or "")

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    value = unescape(value)

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def _truncate(value, length=158):
    value = _clean_text(value)

    if len(value) <= length:
        return value

    shortened = value[: length + 1]

    if " " in shortened:
        shortened = shortened.rsplit(
            " ",
            1,
        )[0]

    return shortened.rstrip(" ,.-") + "…"


def _title_case_slug(value):
    return str(value or "").replace(
        "-",
        " ",
    ).strip().title()


def _default_og_image():
    configured = (
        os.getenv("SEO_DEFAULT_OG_IMAGE")
        or current_app.config.get(
            "SEO_DEFAULT_OG_IMAGE"
        )
        or DEFAULT_OG_IMAGE
    )

    static_folder = Path(
        current_app.static_folder
    )

    candidate = (
        static_folder
        / str(configured).lstrip("/")
    )

    if candidate.exists():
        return absolute_url(configured)

    logo_candidate = (
        static_folder
        / "images"
        / "logo.png"
    )

    if logo_candidate.exists():
        return absolute_url(
            "images/logo.png"
        )

    return absolute_url(configured)


def _get_tour_from_request():
    slug = (
        request.view_args or {}
    ).get("slug")

    if not slug:
        return None

    try:
        from capture_pakistan.models import Tour

        return (
            Tour.query.filter_by(
                slug=slug,
                status="published",
            )
            .first()
        )

    except (
        ImportError,
        SQLAlchemyError,
    ):
        return None


def _get_category_from_request():
    slug = (
        request.view_args or {}
    ).get("slug")

    if not slug:
        return None

    try:
        from capture_pakistan.models import Category

        return (
            Category.query.filter_by(
                slug=slug,
            )
            .first()
        )

    except (
        ImportError,
        SQLAlchemyError,
    ):
        return None


def _approved_review_data(tour_id):
    try:
        from capture_pakistan.models import TourReview

    except ImportError:
        try:
            from capture_pakistan.models.review import (
                TourReview,
            )

        except ImportError:
            return {
                "count": 0,
                "average": 0.0,
                "reviews": [],
            }

    try:
        query = (
            TourReview.query.filter_by(
                tour_id=tour_id,
                status="approved",
            )
        )

        count = query.count()

        average = (
            query.with_entities(
                func.avg(
                    TourReview.rating
                )
            )
            .scalar()
            or 0
        )

        review_rows = (
            query.order_by(
                TourReview.review_date.desc(),
                TourReview.created_at.desc(),
            )
            .limit(10)
            .all()
        )

    except SQLAlchemyError:
        return {
            "count": 0,
            "average": 0.0,
            "reviews": [],
        }

    reviews = []

    for review in review_rows:
        review_date = (
            getattr(
                review,
                "review_date",
                None,
            )
            or getattr(
                review,
                "created_at",
                None,
            )
            or date.today()
        )

        if isinstance(
            review_date,
            datetime,
        ):
            review_date = review_date.date()

        reviews.append(
            {
                "@type": "Review",
                "author": {
                    "@type": "Person",
                    "name": (
                        getattr(
                            review,
                            "reviewer_name",
                            None,
                        )
                        or "Verified Traveler"
                    ),
                },
                "datePublished": (
                    review_date.isoformat()
                ),
                "name": (
                    getattr(
                        review,
                        "title",
                        None,
                    )
                    or "Traveler review"
                ),
                "reviewBody": _clean_text(
                    getattr(
                        review,
                        "review_text",
                        "",
                    )
                ),
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": int(
                        getattr(
                            review,
                            "rating",
                            0,
                        )
                    ),
                    "bestRating": 5,
                    "worstRating": 1,
                },
            }
        )

    return {
        "count": int(count or 0),
        "average": round(
            float(average or 0),
            1,
        ),
        "reviews": reviews,
    }


def _organization_schema():
    site_url = get_site_url()

    return {
        "@type": "TravelAgency",
        "@id": site_url + "/#organization",
        "name": SITE_NAME,
        "url": site_url + "/",
        "logo": {
            "@type": "ImageObject",
            "url": absolute_url(
                "images/logo.png"
            ),
        },
        "image": _default_og_image(),
        "email": (
            os.getenv("SEO_CONTACT_EMAIL")
            or "info@capturepakistan.com"
        ),
        "telephone": (
            os.getenv("SEO_CONTACT_PHONE")
            or "+92 327 1125667"
        ),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Lahore",
            "addressCountry": "PK",
        },
        "sameAs": [
            url
            for url in [
                os.getenv(
                    "SEO_FACEBOOK_URL"
                ),
                os.getenv(
                    "SEO_INSTAGRAM_URL"
                ),
                os.getenv(
                    "SEO_YOUTUBE_URL"
                ),
                os.getenv(
                    "SEO_LINKEDIN_URL"
                ),
            ]
            if url
        ],
    }


def _website_schema():
    site_url = get_site_url()

    return {
        "@type": "WebSite",
        "@id": site_url + "/#website",
        "url": site_url + "/",
        "name": SITE_NAME,
        "publisher": {
            "@id": (
                site_url
                + "/#organization"
            ),
        },
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": (
                    site_url
                    + "/tours?search={search_term_string}"
                ),
            },
            "query-input": (
                "required name=search_term_string"
            ),
        },
    }


def _tour_schema(
    tour,
    canonical_url,
    image_url,
    description,
):
    review_data = (
        _approved_review_data(
            tour.id
        )
    )

    tour_name = _clean_text(
        getattr(
            tour,
            "title",
            "",
        )
    )

    destination = _clean_text(
        getattr(
            tour,
            "destination",
            "Pakistan",
        )
    )

    duration_days = int(
        getattr(
            tour,
            "duration_days",
            0,
        )
        or 0
    )

    category = getattr(
        tour,
        "category",
        None,
    )

    category_name = (
        getattr(
            category,
            "name",
            None,
        )
        or getattr(
            tour,
            "tour_type",
            None,
        )
        or "Pakistan Tour"
    )

    base_price = getattr(
        tour,
        "base_price",
        0,
    )

    if isinstance(
        base_price,
        Decimal,
    ):
        base_price = float(
            base_price
        )

    product = {
        "@type": "Product",
        "@id": (
            canonical_url
            + "#tour-product"
        ),
        "name": tour_name,
        "description": description,
        "image": [image_url],
        "url": canonical_url,
        "category": _clean_text(
            category_name
        ),
        "brand": {
            "@type": "Brand",
            "name": SITE_NAME,
        },
        "offers": {
            "@type": "Offer",
            "url": canonical_url,
            "priceCurrency": (
                os.getenv(
                    "SEO_CURRENCY"
                )
                or DEFAULT_CURRENCY
            ),
            "price": round(
                float(
                    base_price or 0
                ),
                2,
            ),
            "availability": (
                "https://schema.org/InStock"
            ),
        },
    }

    if review_data["count"] > 0:
        product["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": (
                review_data["average"]
            ),
            "reviewCount": (
                review_data["count"]
            ),
            "bestRating": 5,
            "worstRating": 1,
        }

        product["review"] = (
            review_data["reviews"]
        )

    tourist_trip = {
        "@type": "TouristTrip",
        "@id": (
            canonical_url
            + "#tourist-trip"
        ),
        "name": tour_name,
        "description": description,
        "url": canonical_url,
        "image": image_url,
        "touristType": _clean_text(
            getattr(
                tour,
                "tour_type",
                "",
            )
        ),
        "itinerary": {
            "@type": "Place",
            "name": destination,
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "PK",
            },
        },
        "provider": {
            "@id": (
                get_site_url()
                + "/#organization"
            ),
        },
    }

    if duration_days > 0:
        tourist_trip["duration"] = (
            "P"
            + str(duration_days)
            + "D"
        )

    breadcrumb = {
        "@type": "BreadcrumbList",
        "@id": (
            canonical_url
            + "#breadcrumb"
        ),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": (
                    get_site_url()
                    + "/"
                ),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Tours",
                "item": (
                    get_site_url()
                    + "/tours"
                ),
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": tour_name,
                "item": canonical_url,
            },
        ],
    }

    return [
        product,
        tourist_trip,
        breadcrumb,
    ]


def _endpoint_metadata(endpoint):
    view_args = (
        request.view_args or {}
    )

    title = SITE_NAME
    description = DEFAULT_DESCRIPTION
    image = _default_og_image()
    og_type = "website"
    robots = (
        "index, follow, "
        "max-image-preview:large, "
        "max-snippet:-1, "
        "max-video-preview:-1"
    )
    schema_items = [
        _organization_schema(),
        _website_schema(),
    ]

    tour = None

    if endpoint == "public.home":
        title = (
            "Pakistan Tours, Trekking & "
            "Travel Packages | "
            + SITE_NAME
        )

    elif endpoint == "public.public_tours":
        title = (
            "Pakistan Tour Packages & "
            "Private Trips | "
            + SITE_NAME
        )

        description = (
            "Browse private tours, group trips, "
            "trekking adventures and customized "
            "Pakistan travel packages."
        )

    elif endpoint == "public.tour_detail":
        tour = _get_tour_from_request()

        if tour:
            destination = _clean_text(
                tour.destination
            )

            title = _truncate(
                (
                    tour.title
                    + " | "
                    + destination
                    + " Tour"
                ),
                64,
            )

            description = _truncate(
                (
                    tour.short_description
                    or tour.description
                    or (
                        "Book "
                        + tour.title
                        + " with Capture Pakistan Tourism."
                    )
                ),
                158,
            )

            image = absolute_url(
                tour.main_image
                or DEFAULT_OG_IMAGE
            )

            og_type = "product"

    elif endpoint == "public.destinations":
        title = (
            "Pakistan Travel Destinations | "
            + SITE_NAME
        )

        description = (
            "Discover Hunza, Skardu, Kashmir, "
            "Naran, Swat and other unforgettable "
            "travel destinations across Pakistan."
        )

    elif endpoint == "public.destination_detail":
        destination = _title_case_slug(
            view_args.get("slug")
        )

        title = (
            "Tours to "
            + destination
            + " | "
            + SITE_NAME
        )

        description = (
            "Explore tours, attractions and travel "
            "experiences in "
            + destination
            + ", Pakistan."
        )

    elif endpoint == "public.trekking":
        title = (
            "Pakistan Trekking Tours & "
            "Expeditions | "
            + SITE_NAME
        )

        description = (
            "Explore guided trekking tours, lake "
            "hikes, mountain expeditions and base "
            "camp adventures across Pakistan."
        )

    elif endpoint in {
        "public.gallery_page",
        "public.gallery",
    }:
        title = (
            "Pakistan Travel Gallery | "
            + SITE_NAME
        )

        description = (
            "View travel photos from tours, "
            "trekking expeditions and memorable "
            "journeys across Pakistan."
        )

    elif endpoint == "public.about":
        title = (
            "About Capture Pakistan Tourism | "
            "Pakistan Tour Operator"
        )

        description = (
            "Learn about Capture Pakistan Tourism, "
            "our local travel expertise and our "
            "carefully planned tours across Pakistan."
        )

    elif endpoint == "public.contact":
        title = (
            "Contact Capture Pakistan Tourism | "
            "Plan Your Trip"
        )

        description = (
            "Contact our travel team for Pakistan "
            "tour packages, private trips, trekking "
            "expeditions and customized itineraries."
        )

    elif endpoint == "public.pakistan_visa":
        title = (
            "Pakistan Visa Guide & Assistance | "
            + SITE_NAME
        )

        description = (
            "Learn about Pakistan visa requirements "
            "and get travel planning assistance for "
            "your visit to Pakistan."
        )

    elif endpoint == "public.category_detail":
        category = (
            _get_category_from_request()
        )

        category_name = (
            getattr(
                category,
                "name",
                None,
            )
            or _title_case_slug(
                view_args.get("slug")
            )
        )

        title = (
            category_name
            + " Tours in Pakistan | "
            + SITE_NAME
        )

        description = (
            "Browse "
            + category_name
            + " tours, packages and travel "
            "experiences across Pakistan."
        )

    endpoint_prefix = (
        endpoint.split(
            ".",
            1,
        )[0]
        if endpoint
        else ""
    )

    if (
        endpoint_prefix
        in {
            "admin",
            "auth",
            "customer",
        }
        or endpoint
        in {
            "public.tour_inquiry_success",
            "public.booking_success",
        }
        or "/api/" in request.path
    ):
        robots = (
            "noindex, nofollow, noarchive"
        )

    canonical_url = (
        get_site_url()
        + request.path
    )

    if request.path != "/":
        canonical_url = (
            canonical_url.rstrip("/")
        )

    if tour:
        schema_items.extend(
            _tour_schema(
                tour=tour,
                canonical_url=canonical_url,
                image_url=image,
                description=description,
            )
        )

    schema = {
        "@context": "https://schema.org",
        "@graph": schema_items,
    }

    return {
        "title": _truncate(
            title,
            68,
        ),
        "description": _truncate(
            description,
            158,
        ),
        "canonical_url": canonical_url,
        "og_image": image,
        "og_image_alt": (
            (
                _clean_text(
                    tour.title
                )
                + " tour image"
            )
            if tour
            else (
                SITE_NAME
                + " travel experiences"
            )
        ),
        "og_type": og_type,
        "robots": robots,
        "schema": schema,
        "site_name": SITE_NAME,
    }


def build_seo_data():
    try:
        return _endpoint_metadata(
            request.endpoint or ""
        )

    except Exception:
        canonical_url = (
            get_site_url()
            + request.path
        )

        return {
            "title": SITE_NAME,
            "description": (
                DEFAULT_DESCRIPTION
            ),
            "canonical_url": (
                canonical_url
            ),
            "og_image": (
                _default_og_image()
            ),
            "og_image_alt": (
                SITE_NAME
                + " travel experiences"
            ),
            "og_type": "website",
            "robots": (
                "index, follow, "
                "max-image-preview:large"
            ),
            "schema": {
                "@context": (
                    "https://schema.org"
                ),
                "@graph": [
                    _organization_schema(),
                    _website_schema(),
                ],
            },
            "site_name": SITE_NAME,
        }


def register_seo(app):
    @app.context_processor
    def inject_seo_data():
        return {
            "seo_data": (
                build_seo_data()
            ),
        }

    @app.after_request
    def add_seo_headers(response):
        endpoint = (
            request.endpoint or ""
        )

        endpoint_prefix = (
            endpoint.split(
                ".",
                1,
            )[0]
            if endpoint
            else ""
        )

        if (
            endpoint_prefix
            in {
                "admin",
                "auth",
                "customer",
            }
            or "/api/" in request.path
        ):
            response.headers[
                "X-Robots-Tag"
            ] = (
                "noindex, nofollow, noarchive"
            )

        if request.path in {
            "/sitemap.xml",
            "/robots.txt",
        }:
            response.headers[
                "Cache-Control"
            ] = (
                "public, max-age=3600"
            )

        return response
