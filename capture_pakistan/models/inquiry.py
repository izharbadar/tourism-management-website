from capture_pakistan.extensions import db


class Inquiry(db.Model):
    """
    Homepage ke simple quotation/contact form ki inquiries.
    """

    __tablename__ = "inquiries"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    phone = db.Column(
        db.String(30),
        nullable=False,
    )

    destination = db.Column(
        db.String(100),
        nullable=False,
    )

    travelers = db.Column(
        db.Integer,
        nullable=False,
    )

    message = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="new",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )


class TourInquiry(db.Model):
    """
    Single tour page se aane wali private/custom tour inquiries.
    """

    __tablename__ = "tour_inquiries"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    inquiry_number = db.Column(
        db.String(32),
        unique=True,
        nullable=False,
    )

    tour_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "tours.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
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
        nullable=False,
    )

    inquiry_type = db.Column(
        db.Enum(
            "general",
            "private_tour",
            "customized_tour",
            "group_tour",
            "price_quotation",
        ),
        nullable=False,
        default="general",
    )

    preferred_date = db.Column(
        db.Date,
        nullable=True,
    )

    travelers = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    message = db.Column(
        db.Text,
        nullable=False,
    )

    inquiry_status = db.Column(
        db.Enum(
            "new",
            "contacted",
            "quotation_sent",
            "converted",
            "closed",
        ),
        nullable=False,
        default="new",
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
        back_populates="tour_inquiries",
    )

    tour = db.relationship(
        "Tour",
        back_populates="tour_inquiries",
    )