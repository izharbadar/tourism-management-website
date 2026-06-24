from capture_pakistan.extensions import db


class TourReview(db.Model):
    __tablename__ = "tour_reviews"

    __table_args__ = (
        db.UniqueConstraint(
            "booking_id",
            name="uq_tour_reviews_booking_id",
        ),
        db.Index(
            "ix_tour_reviews_tour_status",
            "tour_id",
            "status",
        ),
        db.Index(
            "ix_tour_reviews_created_at",
            "created_at",
        ),
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_tour_reviews_rating",
        ),
    )

    id = db.Column(
        db.BigInteger,
        primary_key=True,
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

    booking_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "bookings.id",
            ondelete="CASCADE",
        ),
        nullable=True,
    )

    reviewer_name = db.Column(
        db.String(120),
        nullable=False,
    )

    reviewer_email = db.Column(
        db.String(190),
        nullable=True,
    )

    rating = db.Column(
        db.Integer,
        nullable=False,
    )

    title = db.Column(
        db.String(180),
        nullable=True,
    )

    review_text = db.Column(
        db.Text,
        nullable=False,
    )

    source = db.Column(
        db.Enum(
            "customer",
            "admin",
        ),
        nullable=False,
        default="customer",
    )

    status = db.Column(
        db.Enum(
            "pending",
            "approved",
            "rejected",
        ),
        nullable=False,
        default="pending",
    )

    is_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    review_date = db.Column(
        db.Date,
        nullable=False,
    )

    admin_note = db.Column(
        db.Text,
        nullable=True,
    )

    approved_by = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    approved_at = db.Column(
        db.DateTime,
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

    tour = db.relationship(
        "Tour",
        backref=db.backref(
            "reviews",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref=db.backref(
            "submitted_reviews",
            lazy=True,
        ),
    )

    booking = db.relationship(
        "Booking",
        backref=db.backref(
            "review",
            uselist=False,
        ),
    )

    approver = db.relationship(
        "User",
        foreign_keys=[approved_by],
    )

    @property
    def display_date(self):
        if self.review_date:
            return self.review_date

        if self.created_at:
            return self.created_at.date()

        return None
