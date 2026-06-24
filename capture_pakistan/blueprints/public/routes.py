import re

from datetime import date

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import (
    current_user,
)

from sqlalchemy import (
    func,
    or_,
)

from sqlalchemy.exc import (
    SQLAlchemyError,
)

from capture_pakistan.blueprints.public import (
    public_bp,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    Category,
    Inquiry,
    Tour,
    TourInquiry,
    TourReview,
)

from capture_pakistan.services.helpers import (
    generate_inquiry_number,
)

from capture_pakistan.services.tour_service import (
    create_slug,
)


from capture_pakistan.services.review_service import (
    approved_reviews_for_tour,
    find_reviewable_booking_for_tour,
    get_review_summary,
)

from capture_pakistan.services.email_service import (
    send_homepage_inquiry_staff_notifications,
    send_tour_inquiry_created_notifications,
)


# =========================================
# PUBLIC FRONTEND HELPERS
# =========================================

@public_bp.app_template_filter("destination_slug")
def destination_slug_filter(value):
    return create_slug(value)


def _published_tours():
    return Tour.query.filter(
        Tour.status == "published"
    )


def _destination_records():
    rows = (
        db.session.query(
            Tour.destination,
            func.count(Tour.id).label(
                "tour_count"
            ),
            func.max(Tour.main_image).label(
                "cover_image"
            ),
        )
        .filter(
            Tour.status == "published",
            Tour.destination.isnot(None),
            Tour.destination != "",
        )
        .group_by(Tour.destination)
        .order_by(
            func.count(Tour.id).desc(),
            Tour.destination.asc(),
        )
        .all()
    )

    return [
        {
            "name": destination,
            "slug": create_slug(destination),
            "tour_count": int(
                tour_count or 0
            ),
            "cover_image": cover_image,
        }
        for (
            destination,
            tour_count,
            cover_image,
        ) in rows
    ]


def _destination_from_slug(slug):
    normalized_slug = create_slug(slug)

    for destination in (
        _destination_records()
    ):
        if destination["slug"] == normalized_slug:
            return destination

    return None


def _valid_email(value):
    return bool(
        re.match(
            r"^[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+"
            r"\\.[A-Za-z]{2,}$",
            value or "",
        )
    )


def _save_general_inquiry(
    *,
    name,
    phone,
    destination,
    travelers,
    message,
):
    inquiry = Inquiry(
        name=name,
        phone=phone,
        destination=destination,
        travelers=travelers,
        message=message or None,
        status="new",
    )

    db.session.add(inquiry)
    db.session.commit()

    send_homepage_inquiry_staff_notifications(
        inquiry
    )

    return inquiry


# =========================================
# HOMEPAGE
# =========================================

@public_bp.route("/")
def home():
    featured_tours = (
        _published_tours()
        .filter(
            Tour.is_featured.is_(True)
        )
        .order_by(
            Tour.created_at.desc()
        )
        .limit(6)
        .all()
    )

    if not featured_tours:
        featured_tours = (
            _published_tours()
            .order_by(
                Tour.created_at.desc()
            )
            .limit(6)
            .all()
        )

    homepage_tours = (
        _published_tours()
        .order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )
        .all()
    )

    trekking_tours = (
        _published_tours()
        .join(
            Category,
            Tour.category_id
            == Category.id,
        )
        .filter(
            (
                Category.slug
                == "trekking-expeditions"
            )
            | (
                Category.name
                == "Trekking & Expeditions"
            )
        )
        .order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )
        .all()
    )

    latest_tours = (
        _published_tours()
        .order_by(
            Tour.created_at.desc()
        )
        .limit(6)
        .all()
    )

    categories = (
        Category.query.filter_by(
            is_active=True
        )
        .order_by(
            Category.name.asc()
        )
        .all()
    )

    destinations = (
        _destination_records()
    )

    public_stats = {
        "tours": _published_tours().count(),
        "destinations": len(
            _destination_records()
        ),
        "categories": len(categories),
    }

    return render_template(
        "index.html",
        featured_tours=featured_tours,
        homepage_tours=homepage_tours,
        trekking_tours=trekking_tours,
        latest_tours=latest_tours,
        categories=categories,
        destinations=destinations,
        public_stats=public_stats,
    )


# =========================================
# HOMEPAGE QUOTE FORM
# =========================================

@public_bp.route(
    "/quote",
    methods=["POST"],
)
def quote():
    name = request.form.get(
        "name",
        "",
    ).strip()

    phone = request.form.get(
        "phone",
        "",
    ).strip()

    destination = request.form.get(
        "destination",
        "",
    ).strip()

    travelers = request.form.get(
        "travelers",
        "",
    ).strip()

    message = request.form.get(
        "message",
        "",
    ).strip()

    if (
        not name
        or not phone
        or not destination
        or not travelers
    ):
        flash(
            "Please fill in all required fields.",
            "error",
        )

        return redirect(
            url_for("public.home")
            + "#contact"
        )

    try:
        travelers_number = int(
            travelers
        )

        if travelers_number < 1:
            flash(
                (
                    "Number of travelers "
                    "must be at least 1."
                ),
                "error",
            )

            return redirect(
                url_for("public.home")
                + "#contact"
            )

        new_inquiry = Inquiry(
            name=name,
            phone=phone,
            destination=destination,
            travelers=travelers_number,
            message=message or None,
            status="new",
        )

        db.session.add(
            new_inquiry
        )

        db.session.commit()

        send_homepage_inquiry_staff_notifications(
            new_inquiry
        )

        flash(
            (
                "Your tour request has been "
                "submitted successfully!"
            ),
            "success",
        )

    except ValueError:
        flash(
            (
                "Please enter a valid "
                "number of travelers."
            ),
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Homepage inquiry error:"
        )

        print(error)

        flash(
            (
                "Your request could not be "
                "submitted. Please try again."
            ),
            "error",
        )

    return redirect(
        url_for("public.home")
        + "#contact"
    )


# =========================================
# ALL PUBLIC TOURS
# =========================================

@public_bp.route("/tours")
def public_tours():
    search = request.args.get(
        "search",
        "",
    ).strip()

    category_slug = request.args.get(
        "category",
        "",
    ).strip()

    destination = request.args.get(
        "destination",
        "",
    ).strip()

    tour_type = request.args.get(
        "type",
        "",
    ).strip()

    sort_by = request.args.get(
        "sort",
        "featured",
    ).strip()

    page = request.args.get(
        "page",
        1,
        type=int,
    )

    if page < 1:
        page = 1

    query = _published_tours()

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            or_(
                Tour.title.ilike(
                    search_term
                ),
                Tour.destination.ilike(
                    search_term
                ),
                Tour.short_description.ilike(
                    search_term
                ),
            )
        )

    if category_slug:
        query = query.join(
            Category
        ).filter(
            Category.slug
            == category_slug,
            Category.is_active.is_(
                True
            ),
        )

    if destination:
        query = query.filter(
            Tour.destination
            == destination
        )

    if tour_type:
        query = query.filter(
            Tour.tour_type
            == tour_type
        )

    if sort_by == "price_low":
        query = query.order_by(
            Tour.base_price.asc()
        )

    elif sort_by == "price_high":
        query = query.order_by(
            Tour.base_price.desc()
        )

    elif sort_by == "newest":
        query = query.order_by(
            Tour.created_at.desc()
        )

    else:
        query = query.order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )

    pagination = query.paginate(
        page=page,
        per_page=9,
        error_out=False,
    )

    categories = (
        Category.query.filter_by(
            is_active=True
        )
        .order_by(
            Category.name.asc()
        )
        .all()
    )

    destinations = (
        _destination_records()
    )

    return render_template(
        "tours/tours.html",
        tours=pagination.items,
        pagination=pagination,
        categories=categories,
        destinations=destinations,
        search=search,
        selected_category=(
            category_slug
        ),
        selected_destination=(
            destination
        ),
        selected_type=tour_type,
        selected_sort=sort_by,
    )


# =========================================
# SINGLE TOUR PAGE
# =========================================

@public_bp.route(
    "/tours/<string:slug>"
)
def tour_detail(slug):
    tour = Tour.query.filter_by(
        slug=slug,
        status="published",
    ).first_or_404()

    related_tours = (
        Tour.query.filter(
            Tour.status
            == "published",

            Tour.id
            != tour.id,

            Tour.category_id
            == tour.category_id,
        )
        .order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )
        .limit(3)
        .all()
    )

    approved_reviews = (
        approved_reviews_for_tour(
            tour.id
        )
    )

    review_summary = (
        get_review_summary(
            tour.id
        )
    )

    customer_review = None
    reviewable_booking = None

    if (
        current_user.is_authenticated
        and current_user.role
        == "customer"
    ):
        customer_review = (
            TourReview.query.filter_by(
                tour_id=tour.id,
                user_id=current_user.id,
                source="customer",
            )
            .order_by(
                TourReview.created_at.desc()
            )
            .first()
        )

        reviewable_booking = (
            find_reviewable_booking_for_tour(
                current_user.id,
                tour.id,
            )
        )

    return render_template(
        "tours/tour_detail.html",
        tour=tour,
        related_tours=related_tours,
        approved_reviews=approved_reviews,
        review_summary=review_summary,
        customer_review=customer_review,
        reviewable_booking=reviewable_booking,
    )


# =========================================
# SUBMIT TOUR INQUIRY
# =========================================

@public_bp.route(
    "/tours/<string:slug>/inquiry",
    methods=["POST"],
)
def submit_tour_inquiry(slug):
    tour = Tour.query.filter_by(
        slug=slug,
        status="published",
    ).first_or_404()

    customer_name = request.form.get(
        "customer_name",
        "",
    ).strip()

    customer_email = request.form.get(
        "customer_email",
        "",
    ).strip().lower()

    customer_phone = request.form.get(
        "customer_phone",
        "",
    ).strip()

    inquiry_type = request.form.get(
        "inquiry_type",
        "general",
    ).strip()

    preferred_date_raw = (
        request.form.get(
            "preferred_date",
            "",
        ).strip()
    )

    travelers_raw = request.form.get(
        "travelers",
        "1",
    ).strip()

    message = request.form.get(
        "message",
        "",
    ).strip()

    allowed_types = {
        "general",
        "private_tour",
        "customized_tour",
        "group_tour",
        "price_quotation",
    }

    if inquiry_type not in allowed_types:
        inquiry_type = "general"

    if len(customer_name) < 2:
        flash(
            "Please enter your complete name.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    email_pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}$"
    )

    if not re.match(
        email_pattern,
        customer_email,
    ):
        flash(
            "Please enter a valid email address.",
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    if len(customer_phone) < 7:
        flash(
            (
                "Please enter a valid "
                "WhatsApp number."
            ),
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    if len(message) < 10:
        flash(
            (
                "Please write a little more "
                "detail about your inquiry."
            ),
            "error",
        )

        return redirect(
            url_for(
                "public.tour_detail",
                slug=tour.slug,
            )
        )

    try:
        travelers = int(
            travelers_raw
        )

        if (
            travelers < 1
            or travelers > 50
        ):
            raise ValueError

        preferred_date = None

        if preferred_date_raw:
            preferred_date = (
                date.fromisoformat(
                    preferred_date_raw
                )
            )

            if preferred_date < date.today():
                flash(
                    (
                        "Please select today "
                        "or a future date."
                    ),
                    "error",
                )

                return redirect(
                    url_for(
                        "public.tour_detail",
                        slug=tour.slug,
                    )
                )

        user_id = None

        if current_user.is_authenticated:
            user_id = current_user.id

        inquiry = TourInquiry(
            inquiry_number=(
                generate_inquiry_number()
            ),
            tour_id=tour.id,
            user_id=user_id,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            inquiry_type=inquiry_type,
            preferred_date=preferred_date,
            travelers=travelers,
            message=message,
            inquiry_status="new",
        )

        db.session.add(
            inquiry
        )

        db.session.commit()

        send_tour_inquiry_created_notifications(
            inquiry
        )

        return redirect(
            url_for(
                "public.tour_inquiry_success",
                inquiry_number=(
                    inquiry.inquiry_number
                ),
            )
        )

    except ValueError:
        db.session.rollback()

        flash(
            (
                "Please enter valid traveler "
                "and date information."
            ),
            "error",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Tour inquiry error:"
        )

        print(error)

        flash(
            (
                "Your inquiry could not be "
                "submitted. Please try again."
            ),
            "error",
        )

    return redirect(
        url_for(
            "public.tour_detail",
            slug=tour.slug,
        )
    )


# =========================================
# INQUIRY SUCCESS PAGE
# =========================================

@public_bp.route(
    "/inquiry/success/"
    "<string:inquiry_number>"
)
def tour_inquiry_success(
    inquiry_number,
):
    inquiry = (
        TourInquiry.query.filter_by(
            inquiry_number=(
                inquiry_number
            )
        )
        .first_or_404()
    )

    return render_template(
        "inquiry/success.html",
        inquiry=inquiry,
    )


# =========================================
# DESTINATIONS
# =========================================

@public_bp.route("/destinations")
def destinations():
    destination_items = (
        _destination_records()
    )

    return render_template(
        "public/destinations.html",
        destinations=destination_items,
    )


@public_bp.route(
    "/destinations/<string:slug>"
)
def destination_detail(slug):
    destination = (
        _destination_from_slug(slug)
    )

    if not destination:
        from flask import abort
        abort(404)

    tours = (
        _published_tours()
        .filter(
            Tour.destination
            == destination["name"]
        )
        .order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )
        .all()
    )

    return render_template(
        "public/destination_detail.html",
        destination=destination,
        tours=tours,
    )


# =========================================
# CATEGORY TOUR PAGE
# =========================================

@public_bp.route(
    "/categories/<string:slug>"
)
def category_detail(slug):
    category = Category.query.filter_by(
        slug=slug,
        is_active=True,
    ).first_or_404()

    tours = (
        _published_tours()
        .filter(
            Tour.category_id
            == category.id
        )
        .order_by(
            Tour.is_featured.desc(),
            Tour.created_at.desc(),
        )
        .all()
    )

    return render_template(
        "public/category_detail.html",
        category=category,
        tours=tours,
    )


# =========================================
# ABOUT & CONTACT
# =========================================

@public_bp.route("/about")
def about():
    return render_template(
        "public/about.html",
        total_tours=_published_tours().count(),
        total_destinations=len(
            _destination_records()
        ),
    )


@public_bp.route(
    "/contact",
    methods=["GET", "POST"],
)
def contact():
    if request.method == "POST":
        name = request.form.get(
            "name",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        phone = request.form.get(
            "phone",
            "",
        ).strip()

        destination = request.form.get(
            "destination",
            "Custom Pakistan Tour",
        ).strip()

        travelers_raw = request.form.get(
            "travelers",
            "1",
        ).strip()

        message = request.form.get(
            "message",
            "",
        ).strip()

        if (
            len(name) < 2
            or len(phone) < 7
            or not _valid_email(email)
            or len(message) < 10
        ):
            flash(
                "Please complete all contact fields with valid information.",
                "error",
            )

            return render_template(
                "public/contact.html",
                destinations=(
                    _destination_records()
                ),
            )

        try:
            travelers = int(
                travelers_raw
            )

            if travelers < 1 or travelers > 100:
                raise ValueError

            combined_message = (
                f"Email: {email}\\n\\n"
                f"{message}"
            )

            _save_general_inquiry(
                name=name,
                phone=phone,
                destination=(
                    destination
                    or "Custom Pakistan Tour"
                ),
                travelers=travelers,
                message=combined_message,
            )

            flash(
                "Your message has been sent. Our travel team will contact you shortly.",
                "success",
            )

            return redirect(
                url_for("public.contact")
            )

        except ValueError:
            flash(
                "Please enter a valid number of travelers.",
                "error",
            )

        except SQLAlchemyError as error:
            db.session.rollback()
            print("Contact inquiry error:")
            print(error)

            flash(
                "Your message could not be sent. Please try again.",
                "error",
            )

    return render_template(
        "public/contact.html",
        destinations=_destination_records(),
    )


# =========================================
# PAKISTAN VISA HELP
# =========================================

@public_bp.route(
    "/pakistan-visa/",
    methods=["GET", "POST"],
)
def pakistan_visa():
    if request.method == "POST":
        name = request.form.get(
            "name",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        phone = request.form.get(
            "phone",
            "",
        ).strip()

        nationality = request.form.get(
            "nationality",
            "",
        ).strip()

        passport_country = request.form.get(
            "passport_country",
            "",
        ).strip()

        planned_date = request.form.get(
            "planned_date",
            "",
        ).strip()

        message = request.form.get(
            "message",
            "",
        ).strip()

        if (
            len(name) < 2
            or len(phone) < 7
            or not _valid_email(email)
            or not nationality
            or not passport_country
        ):
            flash(
                "Please complete all required visa-help fields.",
                "error",
            )

            return render_template(
                "public/pakistan_visa.html"
            )

        details = (
            f"Visa Assistance Request\\n"
            f"Email: {email}\\n"
            f"Nationality: {nationality}\\n"
            f"Passport Country: {passport_country}\\n"
            f"Planned Travel Date: {planned_date or 'Not decided'}\\n\\n"
            f"Message: {message or 'No additional message'}"
        )

        try:
            _save_general_inquiry(
                name=name,
                phone=phone,
                destination=(
                    "Pakistan Visa Assistance"
                ),
                travelers=1,
                message=details,
            )

            flash(
                "Your visa-help request has been received. Our team will contact you shortly.",
                "success",
            )

            return redirect(
                url_for(
                    "public.pakistan_visa"
                )
            )

        except SQLAlchemyError as error:
            db.session.rollback()
            print("Visa inquiry error:")
            print(error)

            flash(
                "Your visa-help request could not be submitted. Please try again.",
                "error",
            )

    return render_template(
        "public/pakistan_visa.html"
    )
