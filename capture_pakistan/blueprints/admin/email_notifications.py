
import re

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import current_user

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from capture_pakistan.blueprints.admin import (
    admin_bp,
)

from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    EmailLog,
    NotificationRecipient,
)

from capture_pakistan.services.email_service import (
    email_configuration_status,
    send_test_email,
)


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9.-]+"
    r"\.[A-Za-z]{2,}$"
)


def _recipient_form_values(recipient):
    recipient.name = request.form.get(
        "name",
        "",
    ).strip()

    recipient.email = request.form.get(
        "email",
        "",
    ).strip().lower()

    recipient.receive_new_bookings = (
        request.form.get(
            "receive_new_bookings"
        )
        == "on"
    )

    recipient.receive_booking_cancellations = (
        request.form.get(
            "receive_booking_cancellations"
        )
        == "on"
    )

    recipient.receive_new_inquiries = (
        request.form.get(
            "receive_new_inquiries"
        )
        == "on"
    )

    recipient.is_active = (
        request.form.get("is_active")
        == "on"
    )


def _valid_recipient(recipient):
    if len(recipient.name) < 2:
        return (
            False,
            "Please enter the recipient name.",
        )

    if not EMAIL_PATTERN.match(
        recipient.email
    ):
        return (
            False,
            "Please enter a valid email address.",
        )

    if not any(
        (
            recipient.receive_new_bookings,
            recipient.receive_booking_cancellations,
            recipient.receive_new_inquiries,
        )
    ):
        return (
            False,
            "Select at least one notification type.",
        )

    return True, ""


@admin_bp.route("/email-notifications")
@admin_required
def email_notifications():
    recipients = (
        NotificationRecipient.query.order_by(
            NotificationRecipient.is_active.desc(),
            NotificationRecipient.name.asc(),
        ).all()
    )

    recent_logs = (
        EmailLog.query.order_by(
            EmailLog.created_at.desc()
        )
        .limit(50)
        .all()
    )

    return render_template(
        "admin/email_notifications.html",
        recipients=recipients,
        recent_logs=recent_logs,
        email_status=(
            email_configuration_status()
        ),
    )


@admin_bp.route(
    "/email-notifications/add",
    methods=["POST"],
)
@admin_required
def add_email_recipient():
    recipient = NotificationRecipient(
        name="",
        email="",
        created_by=current_user.id,
    )

    _recipient_form_values(recipient)

    is_valid, message = (
        _valid_recipient(recipient)
    )

    if not is_valid:
        flash(message, "error")

        return redirect(
            url_for(
                "admin.email_notifications"
            )
        )

    try:
        db.session.add(recipient)
        db.session.commit()

        flash(
            "Notification recipient added.",
            "success",
        )

    except IntegrityError:
        db.session.rollback()

        flash(
            "This email address is already added.",
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Add email recipient error:")
        print(error)

        flash(
            "Recipient could not be added.",
            "error",
        )

    return redirect(
        url_for("admin.email_notifications")
    )


@admin_bp.route(
    "/email-notifications/<int:recipient_id>/update",
    methods=["POST"],
)
@admin_required
def update_email_recipient(recipient_id):
    recipient = db.session.get(
        NotificationRecipient,
        recipient_id,
    )

    if not recipient:
        abort(404)

    _recipient_form_values(recipient)

    is_valid, message = (
        _valid_recipient(recipient)
    )

    if not is_valid:
        flash(message, "error")

        return redirect(
            url_for(
                "admin.email_notifications"
            )
        )

    try:
        db.session.commit()

        flash(
            "Notification recipient updated.",
            "success",
        )

    except IntegrityError:
        db.session.rollback()

        flash(
            "Another recipient already uses this email.",
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Update email recipient error:")
        print(error)

        flash(
            "Recipient could not be updated.",
            "error",
        )

    return redirect(
        url_for("admin.email_notifications")
    )


@admin_bp.route(
    "/email-notifications/<int:recipient_id>/delete",
    methods=["POST"],
)
@admin_required
def delete_email_recipient(recipient_id):
    recipient = db.session.get(
        NotificationRecipient,
        recipient_id,
    )

    if not recipient:
        abort(404)

    try:
        db.session.delete(recipient)
        db.session.commit()

        flash(
            "Notification recipient deleted.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Delete email recipient error:")
        print(error)

        flash(
            "Recipient could not be deleted.",
            "error",
        )

    return redirect(
        url_for("admin.email_notifications")
    )


@admin_bp.route(
    "/email-notifications/<int:recipient_id>/test",
    methods=["POST"],
)
@admin_required
def test_email_recipient(recipient_id):
    recipient = db.session.get(
        NotificationRecipient,
        recipient_id,
    )

    if not recipient:
        abort(404)

    if send_test_email(recipient):
        flash(
            f"Test email sent to {recipient.email}.",
            "success",
        )

    else:
        flash(
            (
                "Test email could not be sent. "
                "Check SMTP settings and the email log."
            ),
            "error",
        )

    return redirect(
        url_for("admin.email_notifications")
    )
