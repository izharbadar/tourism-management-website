from pathlib import Path

from flask import (
    current_app,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import func, or_

from capture_pakistan.blueprints.public import (
    public_bp,
)
from capture_pakistan.extensions import db
from capture_pakistan.models import (
    Category,
    Tour,
)
from capture_pakistan.models.site_gallery import (
    SiteGalleryImage,
)


@public_bp.route("/gallery")
def gallery_page():
    images = (
        SiteGalleryImage.query.filter(
            SiteGalleryImage.is_active.is_(
                True
            )
        )
        .order_by(
            SiteGalleryImage.is_featured.desc(),
            SiteGalleryImage.sort_order.asc(),
            SiteGalleryImage.created_at.desc(),
        )
        .all()
    )

    categories = sorted(
        {
            image.category.strip()
            for image in images
            if image.category
            and image.category.strip()
        },
        key=str.lower,
    )

    locations = {
        image.location.strip()
        for image in images
        if image.location
        and image.location.strip()
    }

    return render_template(
        "public/gallery.html",
        images=images,
        categories=categories,
        gallery_stats={
            "images": len(images),
            "locations": len(locations),
            "featured": sum(
                1
                for image in images
                if image.is_featured
            ),
        },
    )


@public_bp.route("/trekking")
def trekking():
    destination = request.args.get(
        "destination",
        "",
    ).strip()

    sort_by = request.args.get(
        "sort",
        "featured",
    ).strip()

    trekking_filter = or_(
        Category.slug
        == "trekking-expeditions",
        func.lower(
            Category.name
        )
        == "trekking & expeditions",
        Tour.tour_type.ilike(
            "%trek%"
        ),
        Tour.tour_type.ilike(
            "%expedition%"
        ),
    )

    base_query = (
        Tour.query.outerjoin(
            Category,
            Tour.category_id
            == Category.id,
        )
        .filter(
            Tour.status == "published",
            trekking_filter,
        )
    )

    available_tours = base_query.all()

    destinations = sorted(
        {
            tour.destination
            for tour in available_tours
            if tour.destination
        },
        key=str.lower,
    )

    query = base_query

    if destination:
        query = query.filter(
            Tour.destination
            == destination
        )

    if sort_by == "price_low":
        query = query.order_by(
            Tour.base_price.asc(),
            Tour.created_at.desc(),
        )

    elif sort_by == "price_high":
        query = query.order_by(
            Tour.base_price.desc(),
            Tour.created_at.desc(),
        )

    elif sort_by == "duration":
        query = query.order_by(
            Tour.duration_days.asc(),
            Tour.created_at.desc(),
        )

    elif sort_by == "newest":
        query = query.order_by(
            Tour.created_at.desc()
        )

    else:
        query = query.order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )

    tours = query.all()

    featured_tour = next(
        (
            tour
            for tour in tours
            if tour.is_featured
        ),
        tours[0]
        if tours
        else None,
    )

    return render_template(
        "public/trekking.html",
        tours=tours,
        featured_tour=featured_tour,
        destinations=destinations,
        selected_destination=destination,
        selected_sort=sort_by,
        trekking_stats={
            "tours": len(available_tours),
            "destinations": len(destinations),
            "longest": max(
                (
                    tour.duration_days or 0
                    for tour in available_tours
                ),
                default=0,
            ),
        },
    )


@public_bp.route("/company-profile")
def company_profile():
    documents_directory = (
        Path(current_app.static_folder)
        / "documents"
    )

    return send_from_directory(
        documents_directory,
        "capture-pakistan-company-profile.pdf",
        as_attachment=True,
        download_name=(
            "Capture-Pakistan-Company-Profile.pdf"
        ),
    )
