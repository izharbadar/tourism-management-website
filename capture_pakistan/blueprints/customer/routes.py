import re

from decimal import InvalidOperation

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
    Tour,
)

from capture_pakistan.services.booking_service import (
    calculate_booking_summary,
    generate_booking_number,
)

from capture_pakistan.services.email_service import (
    send_booking_cancelled_notifications,
    send_booking_created_notifications,
)


def redirect_admin_to_dashboard():
    if current_user.role != "admin":
        return None

    return redirect(
        url_for("admin.dashboard")
    )


@customer_bp.route("/dashboard")
@login_required
def dashboard():
    admin_redirect = (
        redirect_admin_to_dashboard()
    )

    if admin_redirect:
        return admin_redirect

    customer_bookings = (
        Booking.query.filter_by(
            user_id=current_user.id
        )
    )

    booking_stats = {
        "total": (
            customer_bookings.count()
        ),

        "pending": (
            customer_bookings.filter_by(
                booking_status="pending"
            ).count()
        ),

        "confirmed": (
            customer_bookings.filter_by(
                booking_status="confirmed"
            ).count()
        ),

        "completed": (
            customer_bookings.filter_by(
                booking_status="completed"
            ).count()
        ),
    }

    recent_bookings = (
        customer_bookings
        .order_by(
            Booking.created_at.desc()
        )
        .limit(5)
        .all()
    )

    return render_template(
        "customer/dashboard.html",
        booking_stats=booking_stats,
        recent_bookings=recent_bookings,
    )


@customer_bp.route(
    "/tours/<string:slug>/booking/checkout",
    methods=["POST"],
)
@login_required
def booking_checkout(slug):
    if current_user.role == "admin":
        flash(
            "Please use a customer account to book a tour.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=slug,
            )
        )

    tour = Tour.query.filter_by(
        slug=slug,
        status="published",
    ).first_or_404()

    try:
        booking_summary = (
            calculate_booking_summary(
                tour,
                request.form,
            )
        )

    except ValueError as error:
        flash(
            str(error),
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    return render_template(
        "booking/checkout.html",
        tour=tour,
        booking_summary=booking_summary,
    )


@customer_bp.route(
    "/tours/<string:slug>/book",
    methods=["POST"],
)
@login_required
def book_tour(slug):
    if current_user.role == "admin":
        flash(
            "Please use a customer account to book a tour.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=slug,
            )
        )

    tour = Tour.query.filter_by(
        slug=slug,
        status="published",
    ).first_or_404()

    customer_name = request.form.get(
        "customer_name",
        "",
    ).strip()

    customer_email = request.form.get(
        "customer_email",
        "",
    ).strip().lower()

    customer_phone = request.form.get(
        "customer_phone",
        "",
    ).strip()

    payment_method = request.form.get(
        "payment_method",
        "",
    ).strip()

    if len(customer_name) < 2:
        flash(
            "Please enter your complete name.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    email_pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}$"
    )

    if not re.match(
        email_pattern,
        customer_email,
    ):
        flash(
            "Please enter a valid email address.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    if len(customer_phone) < 7:
        flash(
            "Please enter a valid WhatsApp number.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    if payment_method not in {
        "cash_on_pickup",
        "online_card",
    }:
        flash(
            "Please select a payment method.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    try:
        booking_summary = (
            calculate_booking_summary(
                tour,
                request.form,
            )
        )

        booking = Booking(
            booking_number=(
                generate_booking_number()
            ),
            user_id=current_user.id,
            tour_id=tour.id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            travel_date=(
                booking_summary[
                    "travel_date"
                ]
            ),
            pricing_type=(
                booking_summary[
                    "pricing_type"
                ]
            ),
            package_quantity=(
                booking_summary[
                    "quantity"
                ]
            ),
            adults=(
                booking_summary[
                    "adults"
                ]
            ),
            children=(
                booking_summary[
                    "children"
                ]
            ),
            total_travelers=(
                booking_summary[
                    "total_travelers"
                ]
            ),
            unit_price=(
                booking_summary[
                    "unit_price"
                ]
            ),
            child_unit_price=(
                booking_summary[
                    "child_unit_price"
                ]
            ),
            total_amount=(
                booking_summary[
                    "total_amount"
                ]
            ),
            payment_method=payment_method,
            special_request=(
                booking_summary[
                    "special_request"
                ]
                or None
            ),
            booking_status="pending",
            payment_status="unpaid",
        )

        db.session.add(booking)
        db.session.commit()

        send_booking_created_notifications(
            booking
        )

        return redirect(
            url_for(
                "customer.booking_success",
                booking_number=(
                    booking.booking_number
                ),
            )
        )

    except (
        ValueError,
        InvalidOperation,
    ) as error:
        db.session.rollback()

        flash(
            str(error)
            or "Please enter valid booking details.",
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Booking creation error:")
        print(error)

        flash(
            (
                "Your booking could not be "
                "confirmed. Please try again."
            ),
            "error",
        )

    return redirect(
        url_for(
            "public.tour_detail",
            slug=tour.slug,
        )
    )


@customer_bp.route(
    "/booking/success/<string:booking_number>"
)
@login_required
def booking_success(booking_number):
    booking = Booking.query.filter_by(
        booking_number=booking_number,
        user_id=current_user.id,
    ).first_or_404()

    return render_template(
        "booking/success.html",
        booking=booking,
    )


@customer_bp.route("/dashboard/bookings")
@login_required
def bookings():
    admin_redirect = (
        redirect_admin_to_dashboard()
    )

    if admin_redirect:
        return admin_redirect

    status_filter = request.args.get(
        "status",
        "",
    ).strip()

    query = Booking.query.filter_by(
        user_id=current_user.id
    )

    if status_filter in {
        "pending",
        "confirmed",
        "cancelled",
        "completed",
    }:
        query = query.filter_by(
            booking_status=status_filter
        )

    customer_bookings = (
        query.order_by(
            Booking.created_at.desc()
        ).all()
    )

    return render_template(
        "customer/bookings.html",
        bookings=customer_bookings,
        selected_status=status_filter,
    )


@customer_bp.route(
    "/dashboard/bookings/"
    "<string:booking_number>"
)
@login_required
def booking_detail(booking_number):
    booking = Booking.query.filter_by(
        booking_number=booking_number,
        user_id=current_user.id,
    ).first_or_404()

    return render_template(
        "customer/booking_detail.html",
        booking=booking,
    )


@customer_bp.route(
    (
        "/dashboard/bookings/"
        "<string:booking_number>/cancel"
    ),
    methods=["POST"],
)
@login_required
def cancel_booking(booking_number):
    booking = Booking.query.filter_by(
        booking_number=booking_number,
        user_id=current_user.id,
    ).first_or_404()

    if booking.booking_status not in {
        "pending",
        "confirmed",
    }:
        flash(
            "This booking can no longer be cancelled.",
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

    if booking.payment_status == "paid":
        flash(
            (
                "Please contact our team for cancellation "
                "because this booking is already paid."
            ),
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

    try:
        booking.booking_status = "cancelled"

        db.session.commit()

        send_booking_cancelled_notifications(
            booking,
            cancelled_by="customer",
            include_customer=True,
        )

        flash(
            "Your booking has been cancelled.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Customer cancellation error:")
        print(error)

        flash(
            "Booking could not be cancelled.",
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
