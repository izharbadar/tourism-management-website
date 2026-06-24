from flask_login import UserMixin

from capture_pakistan.extensions import (
    db,
    login_manager,
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

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
    )

    phone = db.Column(
        db.String(30),
        nullable=True,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    role = db.Column(
        db.Enum(
            "admin",
            "customer",
        ),
        nullable=False,
        default="customer",
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
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

    bookings = db.relationship(
        "Booking",
        back_populates="user",
        lazy=True,
    )

    tour_inquiries = db.relationship(
        "TourInquiry",
        back_populates="user",
        lazy=True,
    )


    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )

    @property
    def wishlist_tour_ids(self):
        return {
            item.tour_id
            for item in self.wishlist_items
        }


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(
            User,
            int(user_id),
        )

    except (
        TypeError,
        ValueError,
    ):
        return None