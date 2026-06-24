import re

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

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from capture_pakistan.blueprints.customer import (
    customer_bp,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    Booking,
    TourInquiry,
)

from capture_pakistan.services.email_service import (
    send_email,
)


def redirect_admin_to_dashboard():
    if current_user.role != "admin":
        return None

    return redirect(
        url_for("admin.dashboard")
    )


def profile_statistics():
    total_bookings = (
        Booking.query.filter_by(
            user_id=current_user.id
        ).count()
    )

    upcoming_bookings = (
        Booking.query.filter(
            Booking.user_id
            == current_user.id,
            Booking.booking_status.in_(
                [
                    "pending",
                    "confirmed",
                ]
            ),
            Booking.travel_date
            >= date.today(),
        ).count()
    )

    total_inquiries = (
        TourInquiry.query.filter_by(
            user_id=current_user.id
        ).count()
    )

    return {
        "total_bookings": total_bookings,
        "upcoming_bookings": (
            upcoming_bookings
        ),
        "total_inquiries": total_inquiries,
    }


@customer_bp.route(
    "/dashboard/profile",
    methods=["GET", "POST"],
)
@login_required
def profile():
    admin_redirect = (
        redirect_admin_to_dashboard()
    )

    if admin_redirect:
        return admin_redirect

    if request.method == "POST":
        name = request.form.get(
            "name",
            "",
        ).strip()

        phone = request.form.get(
            "phone",
            "",
        ).strip()

        if len(name) < 2:
            flash(
                "Please enter your complete name.",
                "error",
            )

            return redirect(
                url_for("customer.profile")
            )

        if len(name) > 120:
            flash(
                "Your name cannot exceed 120 characters.",
                "error",
            )

            return redirect(
                url_for("customer.profile")
            )

        phone_pattern = (
            r"^[0-9+()\-\s]{7,30}$"
        )

        if (
            not phone
            or not re.fullmatch(
                phone_pattern,
                phone,
            )
        ):
            flash(
                "Please enter a valid phone or WhatsApp number.",
                "error",
            )

            return redirect(
                url_for("customer.profile")
            )

        try:
            current_user.name = name
            current_user.phone = phone

            db.session.commit()

            flash(
                "Your profile information has been updated.",
                "success",
            )

        except SQLAlchemyError as error:
            db.session.rollback()

            print("Customer profile update error:")
            print(error)

            flash(
                "Your profile could not be updated.",
                "error",
            )

        return redirect(
            url_for("customer.profile")
        )

    return render_template(
        "customer/profile.html",
        profile_stats=profile_statistics(),
    )


@customer_bp.route(
    "/dashboard/profile/password",
    methods=["POST"],
)
@login_required
def change_password():
    admin_redirect = (
        redirect_admin_to_dashboard()
    )

    if admin_redirect:
        return admin_redirect

    current_password = request.form.get(
        "current_password",
        "",
    )

    new_password = request.form.get(
        "new_password",
        "",
    )

    confirm_password = request.form.get(
        "confirm_password",
        "",
    )

    if not check_password_hash(
        current_user.password_hash,
        current_password,
    ):
        flash(
            "Your current password is incorrect.",
            "error",
        )

        return redirect(
            url_for(
                "customer.profile"
            )
            + "#security"
        )

    if len(new_password) < 8:
        flash(
            "New password must contain at least 8 characters.",
            "error",
        )

        return redirect(
            url_for(
                "customer.profile"
            )
            + "#security"
        )

    if new_password != confirm_password:
        flash(
            "New passwords do not match.",
            "error",
        )

        return redirect(
            url_for(
                "customer.profile"
            )
            + "#security"
        )

    if check_password_hash(
        current_user.password_hash,
        new_password,
    ):
        flash(
            "Your new password must be different from the current password.",
            "error",
        )

        return redirect(
            url_for(
                "customer.profile"
            )
            + "#security"
        )

    try:
        current_user.password_hash = (
            generate_password_hash(
                new_password
            )
        )

        db.session.commit()

        send_email(
            recipient_email=(
                current_user.email
            ),
            subject=(
                "Your Capture Pakistan password was changed"
            ),
            html_template=(
                "emails/password_changed.html"
            ),
            text_body=(
                "Your Capture Pakistan account password "
                "was changed successfully. If you did not "
                "make this change, contact our team immediately."
            ),
            context={
                "customer": current_user,
            },
            event_type=(
                "customer_password_changed"
            ),
            related_type="user",
            related_id=current_user.id,
        )

        flash(
            "Your password has been changed successfully.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Customer password change error:")
        print(error)

        flash(
            "Your password could not be changed.",
            "error",
        )

    return redirect(
        url_for(
            "customer.profile"
        )
        + "#security"
    )
