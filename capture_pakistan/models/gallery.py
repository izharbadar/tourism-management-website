from capture_pakistan.extensions import db


class TourImage(db.Model):
    __tablename__ = "tour_images"

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

    image_path = db.Column(
        db.String(255),
        nullable=False,
    )

    original_name = db.Column(
        db.String(255),
        nullable=True,
    )

    alt_text = db.Column(
        db.String(180),
        nullable=True,
    )

    is_cover = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    tour = db.relationship(
        "Tour",
        back_populates="gallery_images",
    )