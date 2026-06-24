from capture_pakistan.extensions import db


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    setting_key = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True,
    )

    setting_value = db.Column(
        db.Text,
        nullable=True,
    )

    setting_group = db.Column(
        db.String(60),
        nullable=False,
        default="general",
    )

    value_type = db.Column(
        db.String(30),
        nullable=False,
        default="text",
    )

    is_public = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
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
