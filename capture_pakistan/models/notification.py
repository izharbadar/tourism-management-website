
from capture_pakistan.extensions import db


class NotificationRecipient(db.Model):
    __tablename__ = "notification_recipients"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    name = db.Column(
        db.String(120),
        nullable=False,
    )

    email = db.Column(
        db.String(190),
        unique=True,
        nullable=False,
        index=True,
    )

    receive_new_bookings = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    receive_booking_cancellations = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    receive_new_inquiries = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_by = db.Column(
        db.BigInteger,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    event_type = db.Column(
        db.String(60),
        nullable=False,
        index=True,
    )

    recipient_email = db.Column(
        db.String(190),
        nullable=False,
        index=True,
    )

    subject = db.Column(
        db.String(255),
        nullable=False,
    )

    delivery_status = db.Column(
        db.String(20),
        nullable=False,
        default="sent",
        index=True,
    )

    related_type = db.Column(
        db.String(40),
        nullable=True,
    )

    related_id = db.Column(
        db.BigInteger,
        nullable=True,
    )

    error_message = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        index=True,
    )
