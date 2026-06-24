from datetime import date, datetime
from xml.etree import ElementTree as ET

from flask import Response
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.public import (
    public_bp,
)
from capture_pakistan.extensions import db
from capture_pakistan.seo import (
    get_site_url,
    slugify,
)


SITEMAP_NAMESPACE = (
    "http://www.sitemaps.org/"
    "schemas/sitemap/0.9"
)


def _date_value(value):
    if isinstance(
        value,
        datetime,
    ):
        value = value.date()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    return None


def _add_url(
    urlset,
    location,
    last_modified=None,
    change_frequency=None,
    priority=None,
):
    url_element = ET.SubElement(
        urlset,
        (
            "{"
            + SITEMAP_NAMESPACE
            + "}url"
        ),
    )

    location_element = ET.SubElement(
        url_element,
        (
            "{"
            + SITEMAP_NAMESPACE
            + "}loc"
        ),
    )

    location_element.text = location

    last_modified = _date_value(
        last_modified
    )

    if last_modified:
        lastmod_element = ET.SubElement(
            url_element,
            (
                "{"
                + SITEMAP_NAMESPACE
                + "}lastmod"
            ),
        )

        lastmod_element.text = (
            last_modified
        )

    if change_frequency:
        changefreq_element = ET.SubElement(
            url_element,
            (
                "{"
                + SITEMAP_NAMESPACE
                + "}changefreq"
            ),
        )

        changefreq_element.text = (
            change_frequency
        )

    if priority is not None:
        priority_element = ET.SubElement(
            url_element,
            (
                "{"
                + SITEMAP_NAMESPACE
                + "}priority"
            ),
        )

        priority_element.text = (
            str(priority)
        )


@public_bp.get("/sitemap.xml")
def sitemap_xml():
    ET.register_namespace(
        "",
        SITEMAP_NAMESPACE,
    )

    urlset = ET.Element(
        (
            "{"
            + SITEMAP_NAMESPACE
            + "}urlset"
        )
    )

    site_url = get_site_url()

    static_urls = [
        ("/", "daily", "1.0"),
        ("/tours", "daily", "0.9"),
        ("/destinations", "weekly", "0.8"),
        ("/trekking", "weekly", "0.8"),
        ("/gallery", "weekly", "0.7"),
        ("/pakistan-visa/", "monthly", "0.7"),
        ("/about", "monthly", "0.6"),
        ("/contact", "monthly", "0.5"),
    ]

    added_urls = set()

    for (
        path,
        change_frequency,
        priority,
    ) in static_urls:
        location = (
            site_url
            + path
        )

        normalized = (
            location.rstrip("/")
            if path != "/"
            else location
        )

        if normalized in added_urls:
            continue

        added_urls.add(normalized)

        _add_url(
            urlset=urlset,
            location=location,
            change_frequency=(
                change_frequency
            ),
            priority=priority,
        )

    try:
        from capture_pakistan.models import (
            Category,
            Tour,
        )

        tours = (
            Tour.query.filter_by(
                status="published",
            )
            .order_by(
                Tour.updated_at.desc()
            )
            .all()
        )

        for tour in tours:
            location = (
                site_url
                + "/tours/"
                + tour.slug
            )

            if location in added_urls:
                continue

            added_urls.add(location)

            _add_url(
                urlset=urlset,
                location=location,
                last_modified=(
                    tour.updated_at
                    or tour.created_at
                ),
                change_frequency="weekly",
                priority="0.8",
            )

        category_query = (
            Category.query
        )

        if hasattr(
            Category,
            "is_active",
        ):
            category_query = (
                category_query.filter_by(
                    is_active=True,
                )
            )

        categories = (
            category_query.order_by(
                Category.name.asc()
            )
            .all()
        )

        for category in categories:
            location = (
                site_url
                + "/categories/"
                + category.slug
            )

            if location in added_urls:
                continue

            added_urls.add(location)

            _add_url(
                urlset=urlset,
                location=location,
                last_modified=getattr(
                    category,
                    "updated_at",
                    None,
                ),
                change_frequency="weekly",
                priority="0.7",
            )

        destination_rows = (
            db.session.query(
                Tour.destination,
                func.max(
                    Tour.updated_at
                ).label(
                    "last_modified"
                ),
            )
            .filter(
                Tour.status
                == "published",
                Tour.destination.isnot(
                    None
                ),
                Tour.destination
                != "",
            )
            .group_by(
                Tour.destination
            )
            .all()
        )

        for (
            destination,
            last_modified,
        ) in destination_rows:
            destination_slug = slugify(
                destination
            )

            if not destination_slug:
                continue

            location = (
                site_url
                + "/destinations/"
                + destination_slug
            )

            if location in added_urls:
                continue

            added_urls.add(location)

            _add_url(
                urlset=urlset,
                location=location,
                last_modified=last_modified,
                change_frequency="weekly",
                priority="0.7",
            )

    except (
        ImportError,
        SQLAlchemyError,
    ):
        db.session.rollback()

    xml_body = ET.tostring(
        urlset,
        encoding="utf-8",
        xml_declaration=True,
    )

    return Response(
        xml_body,
        mimetype="application/xml",
    )


@public_bp.get("/robots.txt")
def robots_txt():
    sitemap_url = (
        get_site_url()
        + "/sitemap.xml"
    )

    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /dashboard/",
            "Disallow: /login",
            "Disallow: /register",
            "Disallow: /api/",
            "",
            "Sitemap: " + sitemap_url,
            "",
        ]
    )

    return Response(
        content,
        mimetype="text/plain",
    )
