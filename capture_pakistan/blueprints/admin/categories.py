from flask import abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import admin_bp
from capture_pakistan.blueprints.admin.decorators import admin_required
from capture_pakistan.extensions import db
from capture_pakistan.models import Category
from capture_pakistan.services.tour_service import generate_unique_slug


@admin_bp.route("/categories")
@admin_required
def categories():
    category_rows = Category.query.order_by(
        Category.created_at.desc()
    ).all()

    return render_template(
        "admin/categories.html",
        categories=category_rows,
    )


@admin_bp.route("/categories/add", methods=["POST"])
@admin_required
def add_category():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    icon = request.form.get("icon", "").strip()
    is_active = request.form.get("is_active") == "on"

    if not name:
        flash("Category name is required.", "error")
        return redirect(url_for("admin.categories"))

    existing_category = Category.query.filter(
        db.func.lower(Category.name) == name.lower()
    ).first()

    if existing_category:
        flash("A category with this name already exists.", "error")
        return redirect(url_for("admin.categories"))

    try:
        db.session.add(
            Category(
                name=name,
                slug=generate_unique_slug(Category, name),
                description=description or None,
                icon=icon or None,
                is_active=is_active,
            )
        )

        db.session.commit()
        flash("Category created successfully.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Category creation error:")
        print(error)
        flash("Category could not be created.", "error")

    return redirect(url_for("admin.categories"))


@admin_bp.route(
    "/categories/edit/<int:category_id>",
    methods=["GET", "POST"],
)
@admin_required
def edit_category(category_id):
    category = db.session.get(Category, category_id)

    if not category:
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        icon = request.form.get("icon", "").strip()
        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("Category name is required.", "error")
            return render_template(
                "admin/category_form.html",
                category=category,
            )

        duplicate = Category.query.filter(
            db.func.lower(Category.name) == name.lower(),
            Category.id != category.id,
        ).first()

        if duplicate:
            flash("Another category already uses this name.", "error")
            return render_template(
                "admin/category_form.html",
                category=category,
            )

        try:
            category.name = name
            category.slug = generate_unique_slug(
                Category,
                name,
                category.id,
            )
            category.description = description or None
            category.icon = icon or None
            category.is_active = is_active

            db.session.commit()
            flash("Category updated successfully.", "success")
            return redirect(url_for("admin.categories"))

        except SQLAlchemyError as error:
            db.session.rollback()
            print("Category update error:")
            print(error)
            flash("Category could not be updated.", "error")

    return render_template(
        "admin/category_form.html",
        category=category,
    )


@admin_bp.route(
    "/categories/delete/<int:category_id>",
    methods=["POST"],
)
@admin_required
def delete_category(category_id):
    category = db.session.get(Category, category_id)

    if not category:
        abort(404)

    if category.tours:
        flash(
            "This category cannot be deleted because tours are assigned to it.",
            "error",
        )
        return redirect(url_for("admin.categories"))

    try:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted successfully.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Category delete error:")
        print(error)
        flash("Category could not be deleted.", "error")

    return redirect(url_for("admin.categories"))
