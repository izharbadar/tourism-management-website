import math

from datetime import (
    date,
    datetime,
    timezone,
)

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import current_user

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import (
    admin_bp,
)

from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    Tour,
    TourReview,
)

from capture_pakistan.services.review_service import (
    validate_review_form,
)


VALID_STATUSES = {
    "pending",
    "approved",
    "rejected",
}

VALID_SOURCES = {
    "customer",
    "admin",
}


def _approval_timestamp():
    return datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


def _review_date_from_form():
    value = request.form.get(
        "review_date",
        "",
    ).strip()

    if not value:
        return date.today()

    try:
        return date.fromisoformat(
            value
        )

    except ValueError:
        raise ValueError(
            "Please enter a valid review date."
        ) from None


def _set_review_status(
    review,
    status,
):
    review.status = status

    if status == "approved":
        review.approved_by = (
            current_user.id
        )
        review.approved_at = (
            _approval_timestamp()
        )

    else:
        review.approved_by = None
        review.approved_at = None


def _populate_review_from_form(
    review,
    *,
    source,
):
    clean_data = validate_review_form(
        request.form,
        require_email=False,
    )

    tour_id = request.form.get(
        "tour_id",
        type=int,
    )

    tour = db.session.get(
        Tour,
        tour_id,
    )

    if not tour:
        raise ValueError(
            "Please select a valid tour."
        )

    status = request.form.get(
        "status",
        "approved",
    ).strip().lower()

    if status not in VALID_STATUSES:
        raise ValueError(
            "Please select a valid review status."
        )

    review.tour_id = tour.id
    review.reviewer_name = (
        clean_data[
            "reviewer_name"
        ]
    )
    review.reviewer_email = (
        clean_data[
            "reviewer_email"
        ]
    )
    review.rating = (
        clean_data["rating"]
    )
    review.title = (
        clean_data["title"]
    )
    review.review_text = (
        clean_data[
            "review_text"
        ]
    )
    review.review_date = (
        _review_date_from_form()
    )
    review.admin_note = (
        request.form.get(
            "admin_note",
            "",
        ).strip()
        or None
    )
    review.is_verified = (
        request.form.get(
            "is_verified"
        )
        == "on"
    )
    review.source = source

    _set_review_status(
        review,
        status,
    )


@admin_bp.route("/reviews")
@admin_required
def reviews():
    search = request.args.get(
        "search",
        "",
    ).strip()

    selected_status = (
        request.args.get(
            "status",
            "",
        ).strip().lower()
    )

    selected_source = (
        request.args.get(
            "source",
            "",
        ).strip().lower()
    )

    selected_rating = (
        request.args.get(
            "rating",
            type=int,
        )
    )

    page = max(
        request.args.get(
            "page",
            1,
            type=int,
        ),
        1,
    )

    query = (
        TourReview.query.join(
            Tour,
            TourReview.tour_id
            == Tour.id,
        )
    )

    if search:
        term = f"%{search}%"

        query = query.filter(
            or_(
                TourReview.reviewer_name.ilike(
                    term
                ),
                TourReview.reviewer_email.ilike(
                    term
                ),
                TourReview.title.ilike(
                    term
                ),
                TourReview.review_text.ilike(
                    term
                ),
                Tour.title.ilike(term),
            )
        )

    if selected_status in VALID_STATUSES:
        query = query.filter(
            TourReview.status
            == selected_status
        )
    else:
        selected_status = ""

    if selected_source in VALID_SOURCES:
        query = query.filter(
            TourReview.source
            == selected_source
        )
    else:
        selected_source = ""

    if selected_rating in {
        1,
        2,
        3,
        4,
        5,
    }:
        query = query.filter(
            TourReview.rating
            == selected_rating
        )
    else:
        selected_rating = None

    total = query.count()
    per_page = 20
    pages = max(
        1,
        math.ceil(
            total / per_page
        ),
    )

    if page > pages:
        page = pages

    review_rows = (
        query.order_by(
            TourReview.created_at.desc()
        )
        .limit(per_page)
        .offset(
            (page - 1)
            * per_page
        )
        .all()
    )

    stats = {
        "total": (
            TourReview.query.count()
        ),
        "pending": (
            TourReview.query.filter_by(
                status="pending"
            ).count()
        ),
        "approved": (
            TourReview.query.filter_by(
                status="approved"
            ).count()
        ),
        "admin_added": (
            TourReview.query.filter_by(
                source="admin"
            ).count()
        ),
    }

    return render_template(
        "admin/reviews.html",
        reviews=review_rows,
        stats=stats,
        search=search,
        selected_status=(
            selected_status
        ),
        selected_source=(
            selected_source
        ),
        selected_rating=(
            selected_rating
        ),
        page=page,
        pages=pages,
        total=total,
    )


@admin_bp.route(
    "/reviews/add",
    methods=["GET", "POST"],
)
@admin_required
def add_review():
    tours = (
        Tour.query.order_by(
            Tour.title.asc()
        ).all()
    )

    if request.method == "POST":
        review = TourReview(
            source="admin",
        )

        try:
            _populate_review_from_form(
                review,
                source="admin",
            )

            db.session.add(review)
            db.session.commit()

            flash(
                "Review added successfully.",
                "success",
            )

            return redirect(
                url_for(
                    "admin.reviews"
                )
            )

        except ValueError as error:
            flash(
                str(error),
                "error",
            )

        except SQLAlchemyError as error:
            db.session.rollback()

            print(
                "Admin review creation error:"
            )
            print(error)

            flash(
                "Review could not be added.",
                "error",
            )

    return render_template(
        "admin/review_form.html",
        review=None,
        tours=tours,
        form_mode="add",
    )


@admin_bp.route(
    "/reviews/<int:review_id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_review(review_id):
    review = db.session.get(
        TourReview,
        review_id,
    )

    if not review:
        abort(404)

    tours = (
        Tour.query.order_by(
            Tour.title.asc()
        ).all()
    )

    if request.method == "POST":
        try:
            _populate_review_from_form(
                review,
                source=review.source,
            )

            db.session.commit()

            flash(
                "Review updated successfully.",
                "success",
            )

            return redirect(
                url_for(
                    "admin.reviews"
                )
            )

        except ValueError as error:
            flash(
                str(error),
                "error",
            )

        except SQLAlchemyError as error:
            db.session.rollback()

            print(
                "Admin review update error:"
            )
            print(error)

            flash(
                "Review could not be updated.",
                "error",
            )

    return render_template(
        "admin/review_form.html",
        review=review,
        tours=tours,
        form_mode="edit",
    )


@admin_bp.route(
    "/reviews/<int:review_id>/status",
    methods=["POST"],
)
@admin_required
def review_status(review_id):
    review = db.session.get(
        TourReview,
        review_id,
    )

    if not review:
        abort(404)

    status = request.form.get(
        "status",
        "",
    ).strip().lower()

    if status not in VALID_STATUSES:
        flash(
            "Invalid review status.",
            "error",
        )

        return redirect(
            url_for(
                "admin.reviews"
            )
        )

    try:
        _set_review_status(
            review,
            status,
        )

        db.session.commit()

        flash(
            f"Review marked {status}.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Review status update error:"
        )
        print(error)

        flash(
            "Review status could not be updated.",
            "error",
        )

    return redirect(
        request.referrer
        or url_for(
            "admin.reviews"
        )
    )


@admin_bp.route(
    "/reviews/<int:review_id>/delete",
    methods=["POST"],
)
@admin_required
def delete_review(review_id):
    review = db.session.get(
        TourReview,
        review_id,
    )

    if not review:
        abort(404)

    try:
        db.session.delete(review)
        db.session.commit()

        flash(
            "Review deleted successfully.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Review deletion error:"
        )
        print(error)

        flash(
            "Review could not be deleted.",
            "error",
        )

    return redirect(
        url_for(
            "admin.reviews"
        )
    )
