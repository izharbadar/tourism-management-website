from capture_pakistan.services.site_setting_service import get_setting

import smtplib
import ssl
import certifi

from email.message import EmailMessage
from email.utils import formataddr

from flask import current_app, render_template

from capture_pakistan.extensions import db
from capture_pakistan.models import (
    EmailLog,
    NotificationRecipient,
)

from capture_pakistan.services.invoice_service import (
    generate_booking_invoice_pdf,
    invoice_filename,
)


def email_configuration_status():
    enabled = bool(
        current_app.config.get("MAIL_ENABLED")
    )

    server = (
        current_app.config.get("MAIL_SERVER")
        or ""
    ).strip()

    sender = (
        current_app.config.get(
            "MAIL_DEFAULT_SENDER"
        )
        or ""
    ).strip()

    username = (
        current_app.config.get("MAIL_USERNAME")
        or ""
    ).strip()

    password = (
        current_app.config.get("MAIL_PASSWORD")
        or ""
    )

    missing = []

    if not server:
        missing.append("MAIL_SERVER")

    if not sender:
        missing.append("MAIL_DEFAULT_SENDER")

    if username and not password:
        missing.append("MAIL_PASSWORD")

    return {
        "enabled": enabled,
        "configured": (
            enabled and not missing
        ),
        "missing": missing,
        "server": server,
        "port": current_app.config.get(
            "MAIL_PORT"
        ),
        "sender": sender,
        "use_tls": bool(
            current_app.config.get(
                "MAIL_USE_TLS"
            )
        ),
        "use_ssl": bool(
            current_app.config.get(
                "MAIL_USE_SSL"
            )
        ),
    }


def _site_url():
    return (
        current_app.config.get(
            "SITE_URL",
            "http://127.0.0.1:5001",
        )
        .strip()
        .rstrip("/")
    )


def _record_email_log(
    *,
    event_type,
    recipient_email,
    subject,
    delivery_status,
    related_type=None,
    related_id=None,
    error_message=None,
):
    try:
        log = EmailLog(
            event_type=event_type,
            recipient_email=(
                recipient_email.lower()
            ),
            subject=subject[:255],
            delivery_status=(
                delivery_status
            ),
            related_type=related_type,
            related_id=related_id,
            error_message=(
                error_message[:2000]
                if error_message
                else None
            ),
        )

        db.session.add(log)
        db.session.commit()

    except Exception as error:
        db.session.rollback()

        print("Email log database error:")
        print(error)


def _open_smtp_connection():
    server = current_app.config[
        "MAIL_SERVER"
    ]

    port = int(
        current_app.config.get(
            "MAIL_PORT",
            587,
        )
    )

    timeout = int(
        current_app.config.get(
            "MAIL_TIMEOUT",
            20,
        )
    )

    use_ssl = bool(
        current_app.config.get(
            "MAIL_USE_SSL"
        )
    )

    use_tls = bool(
        current_app.config.get(
            "MAIL_USE_TLS"
        )
    )

    username = (
        current_app.config.get(
            "MAIL_USERNAME"
        )
        or ""
    ).strip()

    password = (
        current_app.config.get(
            "MAIL_PASSWORD"
        )
        or ""
    )

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    if use_ssl:
        connection = smtplib.SMTP_SSL(
            server,
            port,
            timeout=timeout,
            context=ssl_context,
        )

    else:
        connection = smtplib.SMTP(
            server,
            port,
            timeout=timeout,
        )

        connection.ehlo()

        if use_tls:
            connection.starttls(
                context=ssl_context
            )

            connection.ehlo()

    if username:
        connection.login(
            username,
            password,
        )

    return connection


def send_email(
    *,
    recipient_email,
    subject,
    html_template,
    text_body,
    context=None,
    event_type="general",
    related_type=None,
    related_id=None,
    reply_to=None,
    attachments=None,
):
    recipient_email = (
        recipient_email or ""
    ).strip().lower()

    if not recipient_email:
        return False

    configuration = (
        email_configuration_status()
    )

    if not configuration["configured"]:
        missing_text = (
            ", ".join(
                configuration["missing"]
            )
            or "MAIL_ENABLED"
        )

        _record_email_log(
            event_type=event_type,
            recipient_email=recipient_email,
            subject=subject,
            delivery_status="skipped",
            related_type=related_type,
            related_id=related_id,
            error_message=(
                "Email delivery is disabled or "
                f"incomplete: {missing_text}"
            ),
        )

        return False

    template_context = dict(
        context or {}
    )

    template_context.setdefault(
        "site_url",
        _site_url(),
    )

    html_body = render_template(
        html_template,
        **template_context,
    )

    message = EmailMessage()

    sender_name = (
        get_setting(
            "email_sender_name",
            current_app.config.get(
                "MAIL_SENDER_NAME",
                "Capture Pakistan",
            ),
        )
        or "Capture Pakistan"
    ).strip()

    sender_email = current_app.config[
        "MAIL_DEFAULT_SENDER"
    ]

    message["Subject"] = subject
    message["From"] = formataddr(
        (
            sender_name,
            sender_email,
        )
    )
    message["To"] = recipient_email

    if reply_to:
        message["Reply-To"] = reply_to

    message.set_content(text_body)

    message.add_alternative(
        html_body,
        subtype="html",
    )

    for attachment in attachments or []:
        content = attachment.get("content")
        filename = attachment.get("filename")

        if not content or not filename:
            continue

        message.add_attachment(
            content,
            maintype=attachment.get(
                "maintype",
                "application",
            ),
            subtype=attachment.get(
                "subtype",
                "octet-stream",
            ),
            filename=filename,
        )

    try:
        with _open_smtp_connection() as connection:
            connection.send_message(message)

        _record_email_log(
            event_type=event_type,
            recipient_email=recipient_email,
            subject=subject,
            delivery_status="sent",
            related_type=related_type,
            related_id=related_id,
        )

        return True

    except Exception as error:
        print("Email delivery error:")
        print(error)

        _record_email_log(
            event_type=event_type,
            recipient_email=recipient_email,
            subject=subject,
            delivery_status="failed",
            related_type=related_type,
            related_id=related_id,
            error_message=str(error),
        )

        return False


def _staff_recipients(flag_name):
    flag_column = getattr(
        NotificationRecipient,
        flag_name,
    )

    return (
        NotificationRecipient.query.filter(
            NotificationRecipient.is_active.is_(
                True
            ),
            flag_column.is_(True),
        )
        .order_by(
            NotificationRecipient.name.asc()
        )
        .all()
    )


def send_booking_created_notifications(
    booking,
):
    customer_subject = (
        "Booking received — "
        f"{booking.booking_number}"
    )

    customer_text = (
        f"Hello {booking.customer_name},\n\n"
        "We have received your Capture Pakistan "
        f"booking for {booking.tour_name}.\n"
        f"Booking reference: {booking.booking_number}\n"
        f"Travel date: {booking.travel_date:%d %B %Y}\n"
        f"Travelers: {booking.total_travelers}\n"
        f"Total: PKR {booking.total_amount:,.0f}\n\n"
        "Our team will contact you with the next steps.\n"
        "Your booking invoice PDF is attached to this email."
    )

    if booking.user_id:
        customer_url = (
            f"{_site_url()}/dashboard/bookings/"
            f"{booking.booking_number}"
        )

        invoice_url = (
            f"{customer_url}/invoice"
        )

    else:
        customer_url = ""
        invoice_url = ""

    invoice_attachments = []

    try:
        invoice_attachments.append(
            {
                "content": (
                    generate_booking_invoice_pdf(
                        booking
                    )
                ),
                "filename": (
                    invoice_filename(booking)
                ),
                "maintype": "application",
                "subtype": "pdf",
            }
        )

    except Exception as error:
        print("Booking invoice attachment error:")
        print(error)

    send_email(
        recipient_email=booking.customer_email,
        subject=customer_subject,
        html_template=(
            "emails/booking_received_customer.html"
        ),
        text_body=customer_text,
        context={
            "booking": booking,
            "booking_url": customer_url,
            "invoice_url": invoice_url,
            "invoice_attached": bool(
                invoice_attachments
            ),
        },
        event_type="booking_customer_received",
        related_type="booking",
        related_id=booking.id,
        attachments=invoice_attachments,
    )

    admin_subject = (
        "New booking — "
        f"{booking.booking_number} — "
        f"{booking.customer_name}"
    )

    admin_text = (
        "A new booking has been received.\n\n"
        f"Reference: {booking.booking_number}\n"
        f"Customer: {booking.customer_name}\n"
        f"Email: {booking.customer_email}\n"
        f"Phone: {booking.customer_phone or 'Not provided'}\n"
        f"Tour: {booking.tour_name}\n"
        f"Travel date: {booking.travel_date:%d %B %Y}\n"
        f"Travelers: {booking.total_travelers}\n"
        f"Total: PKR {booking.total_amount:,.0f}"
    )

    admin_url = (
        f"{_site_url()}/admin/bookings/"
        f"{booking.id}"
    )

    for recipient in _staff_recipients(
        "receive_new_bookings"
    ):
        send_email(
            recipient_email=recipient.email,
            subject=admin_subject,
            html_template=(
                "emails/booking_received_admin.html"
            ),
            text_body=admin_text,
            context={
                "booking": booking,
                "recipient": recipient,
                "admin_booking_url": admin_url,
            },
            event_type="booking_admin_received",
            related_type="booking",
            related_id=booking.id,
            reply_to=booking.customer_email,
        )


def send_booking_update_notification(
    booking,
    *,
    previous_booking_status=None,
    previous_payment_status=None,
):
    subject = (
        "Booking update — "
        f"{booking.booking_number}"
    )

    text_body = (
        f"Hello {booking.customer_name},\n\n"
        "Your Capture Pakistan booking has been updated.\n"
        f"Booking status: {booking.booking_status.title()}\n"
        f"Payment status: {booking.payment_status.title()}\n"
        f"Reference: {booking.booking_number}\n\n"
        "You can view the latest details in your account."
    )

    booking_url = (
        (
            f"{_site_url()}/dashboard/bookings/"
            f"{booking.booking_number}"
        )
        if booking.user_id
        else ""
    )

    return send_email(
        recipient_email=booking.customer_email,
        subject=subject,
        html_template=(
            "emails/booking_status_customer.html"
        ),
        text_body=text_body,
        context={
            "booking": booking,
            "booking_url": booking_url,
            "previous_booking_status": (
                previous_booking_status
            ),
            "previous_payment_status": (
                previous_payment_status
            ),
        },
        event_type="booking_status_update",
        related_type="booking",
        related_id=booking.id,
    )


def send_booking_cancelled_notifications(
    booking,
    *,
    cancelled_by="customer",
    include_customer=True,
):
    if include_customer:
        customer_subject = (
            "Booking cancelled — "
            f"{booking.booking_number}"
        )

        customer_text = (
            f"Hello {booking.customer_name},\n\n"
            "Your booking has been marked as cancelled.\n"
            f"Reference: {booking.booking_number}\n"
            f"Tour: {booking.tour_name}\n\n"
            "Please contact our team if you need help."
        )

        booking_url = (
            (
                f"{_site_url()}/dashboard/bookings/"
                f"{booking.booking_number}"
            )
            if booking.user_id
            else ""
        )

        send_email(
            recipient_email=booking.customer_email,
            subject=customer_subject,
            html_template=(
                "emails/booking_cancelled_customer.html"
            ),
            text_body=customer_text,
            context={
                "booking": booking,
                "booking_url": booking_url,
            },
            event_type="booking_cancelled_customer",
            related_type="booking",
            related_id=booking.id,
        )

    admin_subject = (
        "Booking cancelled — "
        f"{booking.booking_number}"
    )

    admin_text = (
        "A booking has been cancelled.\n\n"
        f"Reference: {booking.booking_number}\n"
        f"Customer: {booking.customer_name}\n"
        f"Tour: {booking.tour_name}\n"
        f"Cancelled by: {cancelled_by.title()}"
    )

    admin_url = (
        f"{_site_url()}/admin/bookings/"
        f"{booking.id}"
    )

    for recipient in _staff_recipients(
        "receive_booking_cancellations"
    ):
        send_email(
            recipient_email=recipient.email,
            subject=admin_subject,
            html_template=(
                "emails/booking_cancelled_admin.html"
            ),
            text_body=admin_text,
            context={
                "booking": booking,
                "recipient": recipient,
                "cancelled_by": cancelled_by,
                "admin_booking_url": admin_url,
            },
            event_type="booking_cancelled_admin",
            related_type="booking",
            related_id=booking.id,
            reply_to=booking.customer_email,
        )


def send_tour_inquiry_created_notifications(
    inquiry,
):
    customer_subject = (
        "Inquiry received — "
        f"{inquiry.inquiry_number}"
    )

    customer_text = (
        f"Hello {inquiry.customer_name},\n\n"
        "We have received your Capture Pakistan inquiry.\n"
        f"Reference: {inquiry.inquiry_number}\n"
        f"Tour: {inquiry.tour.title}\n"
        f"Travelers: {inquiry.travelers}\n\n"
        "Our team will contact you with a quotation or answer."
    )

    inquiry_url = (
        f"{_site_url()}/inquiry/success/"
        f"{inquiry.inquiry_number}"
    )

    send_email(
        recipient_email=inquiry.customer_email,
        subject=customer_subject,
        html_template=(
            "emails/inquiry_received_customer.html"
        ),
        text_body=customer_text,
        context={
            "inquiry": inquiry,
            "inquiry_url": inquiry_url,
        },
        event_type="inquiry_customer_received",
        related_type="tour_inquiry",
        related_id=inquiry.id,
    )

    admin_subject = (
        "New tour inquiry — "
        f"{inquiry.inquiry_number} — "
        f"{inquiry.customer_name}"
    )

    admin_text = (
        "A new tour inquiry has been received.\n\n"
        f"Reference: {inquiry.inquiry_number}\n"
        f"Customer: {inquiry.customer_name}\n"
        f"Email: {inquiry.customer_email}\n"
        f"Phone: {inquiry.customer_phone}\n"
        f"Tour: {inquiry.tour.title}\n"
        f"Travelers: {inquiry.travelers}\n"
        f"Message: {inquiry.message}"
    )

    admin_url = (
        f"{_site_url()}/admin/inquiries/"
        f"{inquiry.id}"
    )

    for recipient in _staff_recipients(
        "receive_new_inquiries"
    ):
        send_email(
            recipient_email=recipient.email,
            subject=admin_subject,
            html_template=(
                "emails/inquiry_received_admin.html"
            ),
            text_body=admin_text,
            context={
                "inquiry": inquiry,
                "recipient": recipient,
                "admin_inquiry_url": admin_url,
            },
            event_type="inquiry_admin_received",
            related_type="tour_inquiry",
            related_id=inquiry.id,
            reply_to=inquiry.customer_email,
        )


def send_homepage_inquiry_staff_notifications(
    inquiry,
):
    subject = (
        "New website inquiry — "
        f"{inquiry.destination} — "
        f"{inquiry.name}"
    )

    text_body = (
        "A new homepage inquiry has been received.\n\n"
        f"Customer: {inquiry.name}\n"
        f"Phone: {inquiry.phone}\n"
        f"Destination: {inquiry.destination}\n"
        f"Travelers: {inquiry.travelers}\n"
        f"Message: {inquiry.message or 'Not provided'}"
    )

    for recipient in _staff_recipients(
        "receive_new_inquiries"
    ):
        send_email(
            recipient_email=recipient.email,
            subject=subject,
            html_template=(
                "emails/homepage_inquiry_admin.html"
            ),
            text_body=text_body,
            context={
                "inquiry": inquiry,
                "recipient": recipient,
            },
            event_type="homepage_inquiry_admin",
            related_type="inquiry",
            related_id=inquiry.id,
        )


def send_inquiry_status_notification(
    inquiry,
    *,
    previous_status=None,
):
    subject = (
        "Inquiry update — "
        f"{inquiry.inquiry_number}"
    )

    text_body = (
        f"Hello {inquiry.customer_name},\n\n"
        "Your Capture Pakistan inquiry has been updated.\n"
        f"Current status: {inquiry.inquiry_status.replace('_', ' ').title()}\n"
        f"Reference: {inquiry.inquiry_number}\n\n"
        "Our team will contact you if more information is needed."
    )

    inquiry_url = (
        f"{_site_url()}/inquiry/success/"
        f"{inquiry.inquiry_number}"
    )

    return send_email(
        recipient_email=inquiry.customer_email,
        subject=subject,
        html_template=(
            "emails/inquiry_status_customer.html"
        ),
        text_body=text_body,
        context={
            "inquiry": inquiry,
            "inquiry_url": inquiry_url,
            "previous_status": previous_status,
        },
        event_type="inquiry_status_update",
        related_type="tour_inquiry",
        related_id=inquiry.id,
    )


def send_test_email(recipient):
    subject = "Capture Pakistan email test"

    text_body = (
        f"Hello {recipient.name},\n\n"
        "This is a test email from the Capture Pakistan "
        "notification system. Your address is configured correctly."
    )

    return send_email(
        recipient_email=recipient.email,
        subject=subject,
        html_template="emails/test_email.html",
        text_body=text_body,
        context={
            "recipient": recipient,
        },
        event_type="test_email",
        related_type="notification_recipient",
        related_id=recipient.id,
    )
