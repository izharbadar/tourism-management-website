from capture_pakistan.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    name = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
    )

    slug = db.Column(
        db.String(150),
        unique=True,
        nullable=False,
    )

    description = db.Column(
        db.String(500),
        nullable=True,
    )

    icon = db.Column(
        db.String(50),
        nullable=True,
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

    tours = db.relationship(
        "Tour",
        back_populates="category",
        lazy=True,
    )


class Tour(db.Model):
    __tablename__ = "tours"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    title = db.Column(
        db.String(180),
        nullable=False,
    )

    slug = db.Column(
        db.String(200),
        unique=True,
        nullable=False,
    )

    destination = db.Column(
        db.String(120),
        nullable=False,
    )

    tour_type = db.Column(
        db.String(60),
        nullable=False,
    )

    category_id = db.Column(
        db.BigInteger,
        db.ForeignKey("categories.id"),
        nullable=True,
    )

    short_description = db.Column(
        db.String(500),
        nullable=True,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    duration_days = db.Column(
        db.Integer,
        nullable=False,
    )

    base_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    couple_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    child_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    main_image = db.Column(
        db.String(255),
        nullable=True,
    )

    included_services = db.Column(
        db.Text,
        nullable=True,
    )

    excluded_services = db.Column(
        db.Text,
        nullable=True,
    )

    cancellation_policy = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.Enum(
            "draft",
            "published",
            "inactive",
        ),
        nullable=False,
        default="draft",
    )

    is_featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    created_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
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

    # ---------------------------------
    # Relationships
    # ---------------------------------

    category = db.relationship(
        "Category",
        back_populates="tours",
    )

    itineraries = db.relationship(
        "TourItinerary",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourItinerary.day_number",
    )

    attractions = db.relationship(
        "TourAttraction",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourAttraction.sort_order",
    )

    faqs = db.relationship(
        "TourFAQ",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourFAQ.sort_order",
    )

    bookings = db.relationship(
        "Booking",
        back_populates="tour",
        lazy=True,
    )

    tour_inquiries = db.relationship(
        "TourInquiry",
        back_populates="tour",
        cascade="all, delete-orphan",
        lazy=True,
    )
    gallery_images = db.relationship(
        "TourImage",
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourImage.sort_order",
        lazy=True,
    )



    wishlist_items = db.relationship(
        "Wishlist",
        back_populates="tour",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy=True,
    )


class TourItinerary(db.Model):
    __tablename__ = "tour_itineraries"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    tour_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tours.id"),
        nullable=False,
    )

    day_number = db.Column(
        db.Integer,
        nullable=False,
    )

    title = db.Column(
        db.String(180),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    accommodation = db.Column(
        db.String(180),
        nullable=True,
    )

    meals = db.Column(
        db.String(180),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
    )

    tour = db.relationship(
        "Tour",
        back_populates="itineraries",
    )


class TourAttraction(db.Model):
    __tablename__ = "tour_attractions"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    tour_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tours.id"),
        nullable=False,
    )

    title = db.Column(
        db.String(180),
        nullable=False,
    )

    description = db.Column(
        db.String(500),
        nullable=True,
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
        back_populates="attractions",
    )


class TourFAQ(db.Model):
    __tablename__ = "tour_faqs"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
    )

    tour_id = db.Column(
        db.BigInteger,
        db.ForeignKey("tours.id"),
        nullable=False,
    )

    question = db.Column(
        db.String(255),
        nullable=False,
    )

    answer = db.Column(
        db.Text,
        nullable=False,
    )

    sort_order = db.Column(
        db.Integer,
        nullable=False,
        default=0,
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

    tour = db.relationship(
        "Tour",
        back_populates="faqs",
    )
