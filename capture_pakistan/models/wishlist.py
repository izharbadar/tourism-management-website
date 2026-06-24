from capture_pakistan.extensions import db


class Wishlist(db.Model):
    __tablename__ = "wishlists"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
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

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    user = db.relationship(
        "User",
        back_populates="wishlist_items",
    )

    tour = db.relationship(
        "Tour",
        back_populates="wishlist_items",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "tour_id",
            name="uq_wishlists_user_tour",
        ),
        db.Index(
            "ix_wishlists_user_created",
            "user_id",
            "created_at",
        ),
        db.Index(
            "ix_wishlists_tour",
            "tour_id",
        ),
    )
