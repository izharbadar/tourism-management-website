from capture_pakistan.extensions import db


class SiteGalleryImage(db.Model):
    __tablename__ = "site_gallery_images"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    title = db.Column(
        db.String(180),
        nullable=True,
    )

    caption = db.Column(
        db.String(700),
        nullable=True,
    )

    alt_text = db.Column(
        db.String(180),
        nullable=True,
    )

    category = db.Column(
        db.String(100),
        nullable=True,
        index=True,
    )

    location = db.Column(
        db.String(160),
        nullable=True,
    )

    image_path = db.Column(
        db.String(255),
        nullable=False,
    )

    original_name = db.Column(
        db.String(255),
        nullable=True,
    )

    is_featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
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

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )
