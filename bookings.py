import re

from datetime import date
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

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
    Booking,
    Tour,
)
from capture_pakistan.services.booking_service import (
    generate_booking_number,
)
from capture_pakistan.services.email_service import (
    send_booking_cancelled_notifications,
    send_booking_created_notifications,
    send_booking_update_notification,
)


VALID_BOOKING_STATUSES = {
    "pending",
    "confirmed",
    "cancelled",
    "completed",
}

VALID_PAYMENT_STATUSES = {
    "unpaid",
    "partially_paid",
    "paid",
    "refunded",
}

VALID_PAYMENT_METHODS = {
    "cash_on_pickup",
    "online_card",
    "bank_transfer",
    "jazzcash",
    "easypaisa",
    "cash",
    "other",
}

VALID_PRICING_TYPES = {
    "person",
    "couple",
}

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def _decimal_value(
    raw_value,
    field_name,
):
    try:
        value = Decimal(
            str(
                raw_value or "0"
            ).replace(",", "").strip()
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Please enter a valid {field_name}."
        ) from error

    if value < 0:
        raise ValueError(
            f"{field_name.title()} cannot be negative."
        )

    return value


def _integer_value(
    raw_value,
    field_name,
    minimum=0,
    maximum=200,
):
    try:
        value = int(
            str(
                raw_value or "0"
            ).strip()
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Please enter a valid {field_name}."
        ) from error

    if value < minimum or value > maximum:
        raise ValueError(
            f"{field_name.title()} must be between "
            f"{minimum} and {maximum}."
        )

    return value


def _date_value(
    raw_value,
    field_name,
):
    try:
        return date.fromisoformat(
            str(
                raw_value or ""
            ).strip()
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Please select a valid {field_name}."
        ) from error


def _tour_options():
    return (
        Tour.query.filter_by(
            status="published",
        )
        .order_by(
            Tour.title.asc()
        )
        .all()
    )


@admin_bp.route("/bookings")
@admin_required
def bookings():
    status_filter = request.args.get(
        "status",
        "",
    ).strip()

    payment_filter = request.args.get(
        "payment",
        "",
    ).strip()

    search = request.args.get(
        "search",
        "",
    ).strip()

    query = Booking.query

    if status_filter in VALID_BOOKING_STATUSES:
        query = query.filter(
            Booking.booking_status
            == status_filter
        )

    if payment_filter in VALID_PAYMENT_STATUSES:
        query = query.filter(
            Booking.payment_status
            == payment_filter
        )

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            or_(
                Booking.booking_number.ilike(
                    search_term
                ),
                Booking.customer_name.ilike(
                    search_term
                ),
                Booking.customer_email.ilike(
                    search_term
                ),
                Booking.customer_phone.ilike(
                    search_term
                ),
                Booking.custom_tour_name.ilike(
                    search_term
                ),
            )
        )

    booking_rows = (
        query.order_by(
            Booking.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin/bookings.html",
        bookings=booking_rows,
        selected_status=status_filter,
        selected_payment=payment_filter,
        search=search,
    )


@admin_bp.route(
    "/bookings/add",
    methods=["GET", "POST"],
)
@admin_required
def add_booking():
    tours = _tour_options()

    if request.method == "GET":
        return render_template(
            "admin/booking_form.html",
            tours=tours,
            today=date.today(),
        )

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

    tour_mode = request.form.get(
        "tour_mode",
        "existing",
    ).strip()

    selected_tour = None
    custom_tour_name = None
    custom_destination = None

    try:
        if not customer_name:
            raise ValueError(
                "Customer name is required."
            )

        if not EMAIL_PATTERN.match(
            customer_email
        ):
            raise ValueError(
                "Please enter a valid customer email."
            )

        if len(customer_phone) < 7:
            raise ValueError(
                "Please enter a valid phone or WhatsApp number."
            )

        if tour_mode == "existing":
            tour_id = _integer_value(
                request.form.get("tour_id"),
                "tour",
                minimum=1,
            )

            selected_tour = db.session.get(
                Tour,
                tour_id,
            )

            if not selected_tour:
                raise ValueError(
                    "Please select a valid tour."
                )

        elif tour_mode == "custom":
            custom_tour_name = request.form.get(
                "custom_tour_name",
                "",
            ).strip()

            custom_destination = request.form.get(
                "custom_destination",
                "",
            ).strip()

            if not custom_tour_name:
                raise ValueError(
                    "Please enter the custom tour name."
                )

        else:
            raise ValueError(
                "Please select an existing or custom tour."
            )

        travel_date = _date_value(
            request.form.get("travel_date"),
            "travel date",
        )

        invoice_date = _date_value(
            request.form.get("invoice_date"),
            "invoice date",
        )

        pricing_type = request.form.get(
            "pricing_type",
            "person",
        ).strip()

        if pricing_type not in VALID_PRICING_TYPES:
            raise ValueError(
                "Please select a valid pricing type."
            )

        package_quantity = _integer_value(
            request.form.get(
                "package_quantity"
            ),
            (
                "number of couples"
                if pricing_type == "couple"
                else "number of persons"
            ),
            minimum=1,
            maximum=100,
        )

        adults = _integer_value(
            request.form.get("adults"),
            "adults",
            minimum=0,
        )

        children = _integer_value(
            request.form.get("children"),
            "children",
            minimum=0,
        )

        total_travelers = _integer_value(
            request.form.get(
                "total_travelers"
            ),
            "total travelers",
            minimum=1,
        )

        total_amount = _decimal_value(
            request.form.get(
                "total_amount"
            ),
            "total amount",
        )

        paid_amount = _decimal_value(
            request.form.get(
                "paid_amount"
            ),
            "advance or paid amount",
        )

        if paid_amount > total_amount:
            raise ValueError(
                "Paid amount cannot be greater than the total amount."
            )

        balance_amount = (
            total_amount - paid_amount
        )

        payment_method = request.form.get(
            "payment_method",
            "cash_on_pickup",
        ).strip()

        if payment_method not in VALID_PAYMENT_METHODS:
            raise ValueError(
                "Please select a valid payment method."
            )

        custom_payment_method = (
            request.form.get(
                "custom_payment_method",
                "",
            ).strip()
            or None
        )

        if (
            payment_method == "other"
            and not custom_payment_method
        ):
            raise ValueError(
                "Please enter the custom payment method."
            )

        booking_status = request.form.get(
            "booking_status",
            "pending",
        ).strip()

        payment_status = request.form.get(
            "payment_status",
            "unpaid",
        ).strip()

        if booking_status not in VALID_BOOKING_STATUSES:
            raise ValueError(
                "Please select a valid booking status."
            )

        if payment_status not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                "Please select a valid payment status."
            )

        unit_price = (
            total_amount
            / Decimal(package_quantity)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        booking = Booking(
            booking_number=(
                generate_booking_number()
            ),
            user_id=None,
            tour_id=(
                selected_tour.id
                if selected_tour
                else None
            ),
            custom_tour_name=(
                custom_tour_name
            ),
            custom_destination=(
                custom_destination
                or None
            ),
            booking_source="admin",
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=(
                customer_phone
                or None
            ),
            travel_date=travel_date,
            invoice_date=invoice_date,
            pricing_type=pricing_type,
            package_quantity=(
                package_quantity
            ),
            adults=adults,
            children=children,
            total_travelers=(
                total_travelers
            ),
            unit_price=unit_price,
            child_unit_price=Decimal("0"),
            total_amount=total_amount,
            paid_amount=paid_amount,
            balance_amount=balance_amount,
            payment_method=payment_method,
            custom_payment_method=(
                custom_payment_method
            ),
            special_request=(
                request.form.get(
                    "special_request",
                    "",
                ).strip()
                or None
            ),
            booking_status=booking_status,
            payment_status=payment_status,
            admin_notes=(
                request.form.get(
                    "admin_notes",
                    "",
                ).strip()
                or None
            ),
        )

        db.session.add(booking)
        db.session.commit()

        send_booking_created_notifications(
            booking
        )

        flash(
            "Booking created successfully. "
            "The customer invoice email and staff notification were sent.",
            "success",
        )

        return redirect(
            url_for(
                "admin.booking_detail",
                booking_id=booking.id,
            )
        )

    except ValueError as error:
        db.session.rollback()
        flash(
            str(error),
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()
        print(
            "Admin manual booking error:"
        )
        print(error)

        flash(
            "The booking could not be created.",
            "error",
        )

    return render_template(
        "admin/booking_form.html",
        tours=tours,
        today=date.today(),
        form_data=request.form,
    )


@admin_bp.route(
    "/bookings/<int:booking_id>"
)
@admin_required
def booking_detail(booking_id):
    booking = db.session.get(
        Booking,
        booking_id,
    )

    if not booking:
        abort(404)

    return render_template(
        "admin/booking_detail.html",
        booking=booking,
    )


@admin_bp.route(
    "/bookings/<int:booking_id>/update",
    methods=["POST"],
)
@admin_required
def update_booking(booking_id):
    booking = db.session.get(
        Booking,
        booking_id,
    )

    if not booking:
        abort(404)

    previous_booking_status = (
        booking.booking_status
    )

    previous_payment_status = (
        booking.payment_status
    )

    try:
        booking_status = request.form.get(
            "booking_status",
            booking.booking_status,
        ).strip()

        payment_status = request.form.get(
            "payment_status",
            booking.payment_status,
        ).strip()

        if booking_status not in VALID_BOOKING_STATUSES:
            raise ValueError(
                "Invalid booking status."
            )

        if payment_status not in VALID_PAYMENT_STATUSES:
            raise ValueError(
                "Invalid payment status."
            )

        total_amount = _decimal_value(
            request.form.get(
                "total_amount",
                booking.total_amount,
            ),
            "total amount",
        )

        paid_amount = _decimal_value(
            request.form.get(
                "paid_amount",
                booking.paid_amount,
            ),
            "paid amount",
        )

        if paid_amount > total_amount:
            raise ValueError(
                "Paid amount cannot be greater than the total amount."
            )

        payment_method = request.form.get(
            "payment_method",
            booking.payment_method,
        ).strip()

        if payment_method not in VALID_PAYMENT_METHODS:
            raise ValueError(
                "Invalid payment method."
            )

        invoice_date_raw = request.form.get(
            "invoice_date",
            "",
        ).strip()

        invoice_date = (
            _date_value(
                invoice_date_raw,
                "invoice date",
            )
            if invoice_date_raw
            else booking.invoice_date
        )

        booking.booking_status = (
            booking_status
        )

        booking.payment_status = (
            payment_status
        )

        booking.total_amount = (
            total_amount
        )

        booking.paid_amount = (
            paid_amount
        )

        booking.balance_amount = (
            total_amount - paid_amount
        )

        booking.payment_method = (
            payment_method
        )

        booking.custom_payment_method = (
            request.form.get(
                "custom_payment_method",
                "",
            ).strip()
            or None
        )

        booking.invoice_date = invoice_date

        booking.admin_notes = (
            request.form.get(
                "admin_notes",
                "",
            ).strip()
            or None
        )

        db.session.commit()

        booking_changed = (
            previous_booking_status
            != booking.booking_status
            or previous_payment_status
            != booking.payment_status
        )

        if booking_changed:
            if (
                booking.booking_status
                == "cancelled"
                and previous_booking_status
                != "cancelled"
            ):
                send_booking_cancelled_notifications(
                    booking,
                    cancelled_by="admin",
                    include_customer=True,
                )

            else:
                send_booking_update_notification(
                    booking,
                    previous_booking_status=(
                        previous_booking_status
                    ),
                    previous_payment_status=(
                        previous_payment_status
                    ),
                )

        flash(
            "Booking updated successfully.",
            "success",
        )

    except ValueError as error:
        db.session.rollback()

        flash(
            str(error),
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Admin booking update error:"
        )
        print(error)

        flash(
            "Booking could not be updated.",
            "error",
        )

    return redirect(
        url_for(
            "admin.booking_detail",
            booking_id=booking.id,
        )
    )
