from decimal import Decimal

from capture_pakistan.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    booking_number = db.Column(
        db.String(32),
        unique=True,
        nullable=False,
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=True,
    )

    tour_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tours.id"),
        nullable=True,
    )

    custom_tour_name = db.Column(
        db.String(255),
        nullable=True,
    )

    custom_destination = db.Column(
        db.String(190),
        nullable=True,
    )

    booking_source = db.Column(
        db.Enum(
            "customer",
            "admin",
        ),
        nullable=False,
        default="customer",
    )

    customer_name = db.Column(
        db.String(120),
        nullable=False,
    )

    customer_email = db.Column(
        db.String(190),
        nullable=False,
    )

    customer_phone = db.Column(
        db.String(30),
        nullable=True,
    )

    travel_date = db.Column(
        db.Date,
        nullable=False,
    )

    invoice_date = db.Column(
        db.Date,
        nullable=True,
    )

    pricing_type = db.Column(
        db.Enum(
            "person",
            "couple",
        ),
        nullable=False,
        default="person",
    )

    package_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    adults = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    children = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    total_travelers = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    unit_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    child_unit_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    total_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    paid_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    balance_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    payment_method = db.Column(
        db.Enum(
            "cash_on_pickup",
            "online_card",
            "bank_transfer",
            "jazzcash",
            "easypaisa",
            "cash",
            "other",
        ),
        nullable=False,
        default="cash_on_pickup",
    )

    custom_payment_method = db.Column(
        db.String(120),
        nullable=True,
    )

    special_request = db.Column(
        db.Text,
        nullable=True,
    )

    booking_status = db.Column(
        db.Enum(
            "pending",
            "confirmed",
            "cancelled",
            "completed",
        ),
        nullable=False,
        default="pending",
    )

    payment_status = db.Column(
        db.Enum(
            "unpaid",
            "partially_paid",
            "paid",
            "refunded",
        ),
        nullable=False,
        default="unpaid",
    )

    admin_notes = db.Column(
        db.Text,
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

    user = db.relationship(
        "User",
        back_populates="bookings",
    )

    tour = db.relationship(
        "Tour",
        back_populates="bookings",
    )

    @property
    def tour_name(self):
        if self.tour:
            return self.tour.title

        return (
            self.custom_tour_name
            or "Custom Tour"
        )

    @property
    def tour_destination(self):
        if self.tour:
            return (
                self.tour.destination
                or "Pakistan"
            )

        return (
            self.custom_destination
            or "Pakistan"
        )

    @property
    def payment_method_label(self):
        if (
            self.payment_method == "other"
            and self.custom_payment_method
        ):
            return self.custom_payment_method

        labels = {
            "cash_on_pickup": "Cash on Pickup",
            "online_card": "Online Card Payment",
            "bank_transfer": "Bank Transfer",
            "jazzcash": "JazzCash",
            "easypaisa": "EasyPaisa",
            "cash": "Cash",
            "other": "Other",
        }

        return labels.get(
            self.payment_method,
            str(
                self.payment_method
                or ""
            ).replace("_", " ").title(),
        )

    @property
    def calculated_balance(self):
        total = Decimal(
            self.total_amount or 0
        )

        paid = Decimal(
            self.paid_amount or 0
        )

        return max(
            total - paid,
            Decimal("0"),
        )
