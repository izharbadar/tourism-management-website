from flask import (
    jsonify,
    request,
    url_for,
)

from sqlalchemy import (
    case,
    func,
    or_,
)

from capture_pakistan.blueprints.public import (
    public_bp,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    Category,
    Tour,
)


def _safe_image_url(image_path):
    image_path = str(
        image_path or ""
    ).strip()

    if not image_path:
        return url_for(
            "static",
            filename="images/tour-hunza.jpg",
        )

    if image_path.startswith(
        (
            "http://",
            "https://",
            "/",
        )
    ):
        return image_path

    if image_path.startswith(
        "static/"
    ):
        return "/" + image_path

    if image_path.startswith(
        "uploads/"
    ):
        return url_for(
            "static",
            filename=image_path,
        )

    return image_path


def _destination_results(
    query_text,
    limit=4,
):
    query = (
        db.session.query(
            Tour.destination,
            func.count(
                Tour.id
            ).label(
                "tour_count"
            ),
            func.max(
                Tour.main_image
            ).label(
                "cover_image"
            ),
        )
        .filter(
            Tour.status == "published",
            Tour.destination.isnot(None),
            Tour.destination != "",
        )
    )

    if query_text:
        query = query.filter(
            Tour.destination.ilike(
                f"%{query_text}%"
            )
        )

    rows = (
        query.group_by(
            Tour.destination
        )
        .order_by(
            func.count(
                Tour.id
            ).desc(),
            Tour.destination.asc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "name": destination,
            "tour_count": int(
                tour_count or 0
            ),
            "image": _safe_image_url(
                cover_image
            ),
            "url": url_for(
                "public.destination_detail",
                slug=destination,
            ),
        }
        for (
            destination,
            tour_count,
            cover_image,
        ) in rows
    ]


def _tour_results(
    query_text,
    limit=8,
):
    query = (
        Tour.query.outerjoin(
            Category,
            Tour.category_id
            == Category.id,
        )
        .filter(
            Tour.status
            == "published"
        )
    )

    if query_text:
        search_term = (
            f"%{query_text}%"
        )

        query = query.filter(
            or_(
                Tour.title.ilike(
                    search_term
                ),
                Tour.destination.ilike(
                    search_term
                ),
                Tour.short_description.ilike(
                    search_term
                ),
                Tour.tour_type.ilike(
                    search_term
                ),
                Category.name.ilike(
                    search_term
                ),
            )
        )

        normalized_query = (
            query_text.lower()
        )

        query = query.order_by(
            case(
                (
                    func.lower(
                        Tour.title
                    )
                    == normalized_query,
                    0,
                ),
                (
                    func.lower(
                        Tour.destination
                    )
                    == normalized_query,
                    1,
                ),
                (
                    func.lower(
                        Tour.title
                    ).like(
                        f"{normalized_query}%"
                    ),
                    2,
                ),
                (
                    func.lower(
                        Tour.destination
                    ).like(
                        f"{normalized_query}%"
                    ),
                    3,
                ),
                else_=4,
            ),
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )

    else:
        query = query.order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )

    tours = (
        query.limit(limit)
        .all()
    )

    return [
        {
            "title": tour.title,
            "destination": (
                tour.destination
                or "Pakistan"
            ),
            "duration_days": int(
                tour.duration_days or 0
            ),
            "price": float(
                tour.base_price or 0
            ),
            "currency": "PKR",
            "category": (
                tour.category.name
                if tour.category
                else (
                    tour.tour_type
                    or "Tour"
                )
            ),
            "image": _safe_image_url(
                tour.main_image
            ),
            "url": url_for(
                "public.tour_detail",
                slug=tour.slug,
            ),
        }
        for tour in tours
    ]


@public_bp.get(
    "/api/tour-search"
)
def tour_search_api():
    query_text = request.args.get(
        "q",
        "",
    ).strip()[:120]

    return jsonify(
        {
            "query": query_text,
            "destinations": (
                _destination_results(
                    query_text,
                    limit=4,
                )
            ),
            "tours": (
                _tour_results(
                    query_text,
                    limit=8,
                )
            ),
        }
    )
