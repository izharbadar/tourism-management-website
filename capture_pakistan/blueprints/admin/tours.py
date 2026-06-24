from decimal import Decimal, InvalidOperation

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import admin_bp
from capture_pakistan.blueprints.admin.decorators import admin_required
from capture_pakistan.extensions import db
from capture_pakistan.models import Category, Tour
from capture_pakistan.services.gallery_service import remove_tour_gallery_folder
from capture_pakistan.services.tour_service import (
    clean_tour_description,
    generate_unique_slug,
    replace_tour_sections,
    rich_text_is_empty,
)


VALID_TOUR_STATUSES = {
    "draft",
    "published",
    "inactive",
}


def active_categories():
    return Category.query.filter_by(
        is_active=True
    ).order_by(Category.name.asc()).all()


def read_tour_form():
    return {
        "title": request.form.get("title", "").strip(),
        "destination": request.form.get("destination", "").strip(),
        "tour_type": request.form.get("tour_type", "").strip(),
        "category_id": request.form.get("category_id", "").strip(),
        "short_description": request.form.get(
            "short_description",
            "",
        ).strip(),
        "description": clean_tour_description(
            request.form.get("description", "")
        ),
        "duration_days": request.form.get("duration_days", "").strip(),
        "base_price": request.form.get("base_price", "").strip(),
        "couple_price": request.form.get("couple_price", "0").strip(),
        "child_price": request.form.get("child_price", "0").strip(),
        "main_image": request.form.get("main_image", "").strip(),
        "included_services": request.form.get(
            "included_services",
            "",
        ).strip(),
        "excluded_services": request.form.get(
            "excluded_services",
            "",
        ).strip(),
        "cancellation_policy": request.form.get(
            "cancellation_policy",
            "",
        ).strip(),
        "status": request.form.get("status", "draft").strip(),
        "is_featured": request.form.get("is_featured") == "on",
    }


def validate_tour_form(form_data):
    required_values = [
        form_data["title"],
        form_data["destination"],
        form_data["tour_type"],
        form_data["category_id"],
        form_data["duration_days"],
        form_data["base_price"],
    ]

    if not all(required_values) or rich_text_is_empty(
        form_data["description"]
    ):
        raise ValueError("Please complete all required fields.")

    category_id = int(form_data["category_id"])
    duration_days = int(form_data["duration_days"])
    base_price = Decimal(form_data["base_price"])
    couple_price = Decimal(form_data["couple_price"] or "0")
    child_price = Decimal(form_data["child_price"] or "0")

    category = db.session.get(Category, category_id)

    if not category or not category.is_active:
        raise ValueError("Please select a valid active category.")

    if duration_days < 1:
        raise ValueError("Duration must be at least one day.")

    if base_price < 0 or couple_price < 0 or child_price < 0:
        raise ValueError("Tour prices cannot be negative.")

    status = form_data["status"]

    if status not in VALID_TOUR_STATUSES:
        status = "draft"

    return {
        "category": category,
        "duration_days": duration_days,
        "base_price": base_price,
        "couple_price": couple_price,
        "child_price": child_price,
        "status": status,
    }


def apply_tour_values(tour, form_data, converted):
    tour.title = form_data["title"]
    tour.destination = form_data["destination"]
    tour.tour_type = form_data["tour_type"]
    tour.category_id = converted["category"].id
    tour.short_description = form_data["short_description"] or None
    tour.description = form_data["description"]
    tour.duration_days = converted["duration_days"]
    tour.base_price = converted["base_price"]
    tour.couple_price = converted["couple_price"]
    tour.child_price = converted["child_price"]
    tour.main_image = form_data["main_image"] or None
    tour.included_services = form_data["included_services"] or None
    tour.excluded_services = form_data["excluded_services"] or None
    tour.cancellation_policy = form_data["cancellation_policy"] or None
    tour.status = converted["status"]
    tour.is_featured = form_data["is_featured"]


@admin_bp.route("/tours")
@admin_required
def tours():
    tour_rows = Tour.query.order_by(Tour.created_at.desc()).all()

    return render_template(
        "admin/tours.html",
        tours=tour_rows,
    )


@admin_bp.route("/tours/add", methods=["GET", "POST"])
@admin_required
def add_tour():
    categories = active_categories()

    if request.method == "POST":
        form_data = read_tour_form()

        try:
            converted = validate_tour_form(form_data)

            tour = Tour(
                slug=generate_unique_slug(Tour, form_data["title"]),
                created_by=current_user.id,
            )

            apply_tour_values(tour, form_data, converted)

            db.session.add(tour)
            db.session.flush()
            replace_tour_sections(tour)
            db.session.commit()

            flash("Tour created successfully.", "success")
            return redirect(url_for("admin.tours"))

        except (ValueError, InvalidOperation) as error:
            db.session.rollback()
            flash(str(error) or "Please enter valid tour details.", "error")

        except SQLAlchemyError as error:
            db.session.rollback()
            print("Tour creation error:")
            print(error)
            flash("Tour could not be created.", "error")

    return render_template(
        "admin/tour_form.html",
        categories=categories,
        tour=None,
        form_mode="add",
    )


@admin_bp.route(
    "/tours/edit/<int:tour_id>",
    methods=["GET", "POST"],
)
@admin_required
def edit_tour(tour_id):
    tour = db.session.get(Tour, tour_id)

    if not tour:
        abort(404)

    categories = active_categories()

    if request.method == "POST":
        form_data = read_tour_form()

        try:
            converted = validate_tour_form(form_data)

            tour.slug = generate_unique_slug(
                Tour,
                form_data["title"],
                tour.id,
            )

            apply_tour_values(tour, form_data, converted)
            replace_tour_sections(tour)
            db.session.commit()

            flash("Tour updated successfully.", "success")
            return redirect(url_for("admin.tours"))

        except (ValueError, InvalidOperation) as error:
            db.session.rollback()
            flash(str(error) or "Please enter valid tour details.", "error")

        except SQLAlchemyError as error:
            db.session.rollback()
            print("Tour update error:")
            print(error)
            flash("Tour could not be updated.", "error")

    return render_template(
        "admin/tour_form.html",
        categories=categories,
        tour=tour,
        form_mode="edit",
    )


@admin_bp.route(
    "/tours/delete/<int:tour_id>",
    methods=["POST"],
)
@admin_required
def delete_tour(tour_id):
    tour = db.session.get(Tour, tour_id)

    if not tour:
        abort(404)

    try:
        db.session.delete(tour)
        db.session.commit()
        remove_tour_gallery_folder(tour_id)
        flash("Tour deleted successfully.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Tour delete error:")
        print(error)
        flash(
            "This tour could not be deleted. It may have existing bookings.",
            "error",
        )

    return redirect(url_for("admin.tours"))
