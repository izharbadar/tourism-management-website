import re

from datetime import date

from sqlalchemy import func

from capture_pakistan.extensions import db
from capture_pakistan.models import (
    Booking,
    TourReview,
)


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9.-]+"
    r"\.[A-Za-z]{2,}$"
)


def validate_review_form(
    form,
    *,
    require_email=False,
):
    reviewer_name = form.get(
        "reviewer_name",
        "",
    ).strip()

    reviewer_email = form.get(
        "reviewer_email",
        "",
    ).strip().lower()

    title = form.get(
        "title",
        "",
    ).strip()

    review_text = form.get(
        "review_text",
        "",
    ).strip()

    rating_raw = form.get(
        "rating",
        "",
    ).strip()

    if len(reviewer_name) < 2:
        raise ValueError(
            "Please enter the reviewer's complete name."
        )

    if require_email and not reviewer_email:
        raise ValueError(
            "Reviewer email is required."
        )

    if (
        reviewer_email
        and not EMAIL_PATTERN.match(
            reviewer_email
        )
    ):
        raise ValueError(
            "Please enter a valid reviewer email address."
        )

    try:
        rating = int(rating_raw)

    except (
        TypeError,
        ValueError,
    ):
        raise ValueError(
            "Please select a rating from 1 to 5 stars."
        ) from None

    if rating < 1 or rating > 5:
        raise ValueError(
            "Rating must be between 1 and 5 stars."
        )

    if len(title) > 180:
        raise ValueError(
            "Review title cannot exceed 180 characters."
        )

    if len(review_text) < 20:
        raise ValueError(
            "Please write at least 20 characters in the review."
        )

    if len(review_text) > 5000:
        raise ValueError(
            "Review text cannot exceed 5,000 characters."
        )

    return {
        "reviewer_name": reviewer_name,
        "reviewer_email": (
            reviewer_email or None
        ),
        "rating": rating,
        "title": title or None,
        "review_text": review_text,
    }


def booking_is_reviewable(booking):
    return bool(
        booking
        and booking.booking_status
        == "completed"
    )


def eligible_bookings_for_user(user_id):
    return (
        Booking.query.outerjoin(
            TourReview,
            TourReview.booking_id
            == Booking.id,
        )
        .filter(
            Booking.user_id == user_id,
            Booking.booking_status
            == "completed",
            TourReview.id.is_(None),
        )
        .order_by(
            Booking.travel_date.desc(),
            Booking.created_at.desc(),
        )
        .all()
    )


def find_reviewable_booking_for_tour(
    user_id,
    tour_id,
):
    return (
        Booking.query.outerjoin(
            TourReview,
            TourReview.booking_id
            == Booking.id,
        )
        .filter(
            Booking.user_id == user_id,
            Booking.tour_id == tour_id,
            Booking.booking_status
            == "completed",
            TourReview.id.is_(None),
        )
        .order_by(
            Booking.travel_date.desc(),
            Booking.created_at.desc(),
        )
        .first()
    )


def approved_reviews_for_tour(
    tour_id,
    limit=30,
):
    return (
        TourReview.query.filter_by(
            tour_id=tour_id,
            status="approved",
        )
        .order_by(
            TourReview.review_date.desc(),
            TourReview.created_at.desc(),
        )
        .limit(limit)
        .all()
    )


def get_review_summary(tour_id):
    count_value, average_value = (
        db.session.query(
            func.count(
                TourReview.id
            ),
            func.avg(
                TourReview.rating
            ),
        )
        .filter(
            TourReview.tour_id
            == tour_id,
            TourReview.status
            == "approved",
        )
        .one()
    )

    total = int(
        count_value or 0
    )

    average = float(
        average_value or 0
    )

    grouped = (
        db.session.query(
            TourReview.rating,
            func.count(
                TourReview.id
            ),
        )
        .filter(
            TourReview.tour_id
            == tour_id,
            TourReview.status
            == "approved",
        )
        .group_by(
            TourReview.rating
        )
        .all()
    )

    grouped_counts = {
        int(rating): int(count)
        for rating, count
        in grouped
    }

    distribution = []

    for rating in range(5, 0, -1):
        count = grouped_counts.get(
            rating,
            0,
        )

        percentage = (
            round(
                count / total * 100,
                1,
            )
            if total
            else 0
        )

        distribution.append(
            {
                "rating": rating,
                "count": count,
                "percentage": percentage,
            }
        )

    positive_reviews = (
        grouped_counts.get(5, 0)
        + grouped_counts.get(4, 0)
    )

    recommended_percentage = (
        round(
            positive_reviews
            / total
            * 100
        )
        if total
        else 0
    )

    return {
        "count": total,
        "average": round(
            average,
            1,
        ),
        "recommended_percentage": (
            recommended_percentage
        ),
        "distribution": distribution,
    }
