from datetime import date

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
)

from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.customer import (
    customer_bp,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    Booking,
    TourReview,
)

from capture_pakistan.services.review_service import (
    booking_is_reviewable,
    eligible_bookings_for_user,
    validate_review_form,
)


def _customer_only_redirect():
    if current_user.role == "admin":
        return redirect(
            url_for(
                "admin.reviews"
            )
        )

    return None


@customer_bp.route(
    "/dashboard/reviews"
)
@login_required
def reviews():
    admin_redirect = (
        _customer_only_redirect()
    )

    if admin_redirect:
        return admin_redirect

    customer_reviews = (
        TourReview.query.filter_by(
            user_id=current_user.id,
            source="customer",
        )
        .order_by(
            TourReview.created_at.desc()
        )
        .all()
    )

    eligible_bookings = (
        eligible_bookings_for_user(
            current_user.id
        )
    )

    return render_template(
        "customer/reviews.html",
        reviews=customer_reviews,
        eligible_bookings=(
            eligible_bookings
        ),
    )


@customer_bp.route(
    "/dashboard/bookings/"
    "<string:booking_number>/review",
    methods=["GET", "POST"],
)
@login_required
def booking_review(booking_number):
    admin_redirect = (
        _customer_only_redirect()
    )

    if admin_redirect:
        return admin_redirect

    booking = Booking.query.filter_by(
        booking_number=booking_number,
        user_id=current_user.id,
    ).first_or_404()

    if not booking_is_reviewable(
        booking
    ):
        flash(
            "A review can be submitted after the booking is marked completed.",
            "error",
        )

        return redirect(
            url_for(
                "customer.booking_detail",
                booking_number=(
                    booking.booking_number
                ),
            )
        )

    review = TourReview.query.filter_by(
        booking_id=booking.id
    ).first()

    if request.method == "POST":
        customer_form = {
            "reviewer_name": (
                current_user.name
            ),
            "reviewer_email": (
                current_user.email
            ),
            "rating": request.form.get(
                "rating",
                "",
            ),
            "title": request.form.get(
                "title",
                "",
            ),
            "review_text": (
                request.form.get(
                    "review_text",
                    "",
                )
            ),
        }

        try:
            clean_data = (
                validate_review_form(
                    customer_form,
                    require_email=True,
                )
            )

            if not review:
                review = TourReview(
                    tour_id=booking.tour_id,
                    user_id=current_user.id,
                    booking_id=booking.id,
                    source="customer",
                    is_verified=True,
                    review_date=date.today(),
                )

                db.session.add(review)

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

            review.status = "pending"
            review.admin_note = None
            review.approved_by = None
            review.approved_at = None

            db.session.commit()

            flash(
                "Thank you. Your review was submitted for approval.",
                "success",
            )

            return redirect(
                url_for(
                    "customer.reviews"
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
                "Customer review save error:"
            )
            print(error)

            flash(
                "Your review could not be saved. Please try again.",
                "error",
            )

    return render_template(
        "customer/review_form.html",
        booking=booking,
        review=review,
    )
