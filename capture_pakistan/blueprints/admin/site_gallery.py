from pathlib import Path

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import (
    admin_bp,
)
from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)
from capture_pakistan.extensions import db
from capture_pakistan.models.site_gallery import (
    SiteGalleryImage,
)
from capture_pakistan.services.site_gallery_service import (
    normalize_site_gallery_order,
    remove_site_gallery_file,
    save_uploaded_site_gallery_image,
)


def _clean_text(
    field_name,
    maximum_length,
):
    return request.form.get(
        field_name,
        "",
    ).strip()[:maximum_length]


def _filename_title(filename):
    stem = Path(
        filename or "Gallery Photo"
    ).stem

    return stem.replace(
        "_",
        " ",
    ).replace(
        "-",
        " ",
    ).strip().title()[:180]


@admin_bp.route("/gallery")
@admin_required
def site_gallery():
    search = request.args.get(
        "search",
        "",
    ).strip()

    category = request.args.get(
        "category",
        "",
    ).strip()

    status = request.args.get(
        "status",
        "all",
    ).strip()

    query = SiteGalleryImage.query

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            or_(
                SiteGalleryImage.title.ilike(
                    search_term
                ),
                SiteGalleryImage.caption.ilike(
                    search_term
                ),
                SiteGalleryImage.location.ilike(
                    search_term
                ),
                SiteGalleryImage.category.ilike(
                    search_term
                ),
            )
        )

    if category:
        query = query.filter(
            SiteGalleryImage.category
            == category
        )

    if status == "active":
        query = query.filter(
            SiteGalleryImage.is_active.is_(
                True
            )
        )

    elif status == "hidden":
        query = query.filter(
            SiteGalleryImage.is_active.is_(
                False
            )
        )

    elif status == "featured":
        query = query.filter(
            SiteGalleryImage.is_featured.is_(
                True
            )
        )

    images = query.order_by(
        SiteGalleryImage.sort_order.asc(),
        SiteGalleryImage.id.asc(),
    ).all()

    categories = [
        row[0]
        for row in (
            db.session.query(
                SiteGalleryImage.category
            )
            .filter(
                SiteGalleryImage.category.isnot(
                    None
                ),
                SiteGalleryImage.category != "",
            )
            .distinct()
            .order_by(
                SiteGalleryImage.category.asc()
            )
            .all()
        )
    ]

    stats = {
        "total": SiteGalleryImage.query.count(),
        "active": SiteGalleryImage.query.filter(
            SiteGalleryImage.is_active.is_(
                True
            )
        ).count(),
        "featured": SiteGalleryImage.query.filter(
            SiteGalleryImage.is_featured.is_(
                True
            )
        ).count(),
        "hidden": SiteGalleryImage.query.filter(
            SiteGalleryImage.is_active.is_(
                False
            )
        ).count(),
    }

    return render_template(
        "admin/site_gallery.html",
        images=images,
        categories=categories,
        stats=stats,
        search=search,
        selected_category=category,
        selected_status=status,
    )


@admin_bp.route(
    "/gallery/upload",
    methods=["POST"],
)
@admin_required
def upload_site_gallery_images():
    uploaded_files = [
        image
        for image in request.files.getlist(
            "gallery_images"
        )
        if image and image.filename
    ]

    if not uploaded_files:
        flash(
            "Please select at least one gallery image.",
            "error",
        )

        return redirect(
            url_for("admin.site_gallery")
        )

    shared_title = _clean_text(
        "title",
        180,
    )

    category = _clean_text(
        "category",
        100,
    )

    location = _clean_text(
        "location",
        160,
    )

    caption = _clean_text(
        "caption",
        700,
    )

    alt_text = _clean_text(
        "alt_text",
        180,
    )

    is_featured = (
        request.form.get(
            "is_featured"
        )
        == "on"
    )

    saved_paths = []
    errors = []

    next_sort_order = (
        db.session.query(
            db.func.coalesce(
                db.func.max(
                    SiteGalleryImage.sort_order
                ),
                -1,
            )
        ).scalar()
        + 1
    )

    try:
        for uploaded_file in uploaded_files:
            try:
                (
                    image_path,
                    original_name,
                ) = save_uploaded_site_gallery_image(
                    uploaded_file
                )

                saved_paths.append(
                    image_path
                )

                image_title = (
                    shared_title
                    if len(uploaded_files) == 1
                    and shared_title
                    else _filename_title(
                        original_name
                    )
                )

                db.session.add(
                    SiteGalleryImage(
                        title=image_title or None,
                        caption=caption or None,
                        alt_text=(
                            alt_text
                            or image_title
                            or "Capture Pakistan gallery photo"
                        ),
                        category=category or None,
                        location=location or None,
                        image_path=image_path,
                        original_name=original_name,
                        is_featured=is_featured,
                        is_active=True,
                        sort_order=next_sort_order,
                    )
                )

                next_sort_order += 1

            except ValueError as error:
                errors.append(
                    str(error)
                )

        if not saved_paths:
            db.session.rollback()

            flash(
                errors[0]
                if errors
                else "No valid images were uploaded.",
                "error",
            )

            return redirect(
                url_for("admin.site_gallery")
            )

        db.session.flush()
        normalize_site_gallery_order()
        db.session.commit()

        flash(
            f"{len(saved_paths)} gallery image(s) uploaded "
            "successfully.",
            "success",
        )

        if errors:
            flash(
                errors[0],
                "error",
            )

    except SQLAlchemyError as error:
        db.session.rollback()

        for image_path in saved_paths:
            remove_site_gallery_file(
                image_path
            )

        print(
            "Website gallery upload error:"
        )
        print(error)

        flash(
            "Gallery images could not be saved.",
            "error",
        )

    return redirect(
        url_for("admin.site_gallery")
    )


@admin_bp.route(
    "/gallery/<int:image_id>/edit",
    methods=["GET", "POST"],
)
@admin_required
def edit_site_gallery_image(image_id):
    image = db.session.get(
        SiteGalleryImage,
        image_id,
    )

    if not image:
        abort(404)

    if request.method == "POST":
        try:
            image.title = (
                _clean_text(
                    "title",
                    180,
                )
                or None
            )

            image.caption = (
                _clean_text(
                    "caption",
                    700,
                )
                or None
            )

            image.alt_text = (
                _clean_text(
                    "alt_text",
                    180,
                )
                or image.title
                or "Capture Pakistan gallery photo"
            )

            image.category = (
                _clean_text(
                    "category",
                    100,
                )
                or None
            )

            image.location = (
                _clean_text(
                    "location",
                    160,
                )
                or None
            )

            image.is_active = (
                request.form.get(
                    "is_active"
                )
                == "on"
            )

            image.is_featured = (
                request.form.get(
                    "is_featured"
                )
                == "on"
            )

            db.session.commit()

            flash(
                "Gallery image updated successfully.",
                "success",
            )

            return redirect(
                url_for("admin.site_gallery")
            )

        except SQLAlchemyError as error:
            db.session.rollback()

            print(
                "Website gallery edit error:"
            )
            print(error)

            flash(
                "Gallery image could not be updated.",
                "error",
            )

    return render_template(
        "admin/site_gallery_edit.html",
        image=image,
    )


@admin_bp.route(
    "/gallery/<int:image_id>/toggle",
    methods=["POST"],
)
@admin_required
def toggle_site_gallery_image(image_id):
    image = db.session.get(
        SiteGalleryImage,
        image_id,
    )

    if not image:
        abort(404)

    try:
        image.is_active = not image.is_active
        db.session.commit()

        flash(
            "Gallery visibility updated.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()
        print(error)

        flash(
            "Gallery visibility could not be updated.",
            "error",
        )

    return redirect(
        request.referrer
        or url_for("admin.site_gallery")
    )


@admin_bp.route(
    "/gallery/<int:image_id>/feature",
    methods=["POST"],
)
@admin_required
def feature_site_gallery_image(image_id):
    image = db.session.get(
        SiteGalleryImage,
        image_id,
    )

    if not image:
        abort(404)

    try:
        image.is_featured = (
            not image.is_featured
        )

        db.session.commit()

        flash(
            "Featured status updated.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()
        print(error)

        flash(
            "Featured status could not be updated.",
            "error",
        )

    return redirect(
        request.referrer
        or url_for("admin.site_gallery")
    )


@admin_bp.route(
    "/gallery/<int:image_id>/move",
    methods=["POST"],
)
@admin_required
def move_site_gallery_image(image_id):
    direction = request.form.get(
        "direction",
        "",
    ).strip()

    if direction not in {
        "up",
        "down",
    }:
        abort(400)

    images = SiteGalleryImage.query.order_by(
        SiteGalleryImage.sort_order.asc(),
        SiteGalleryImage.id.asc(),
    ).all()

    current_index = next(
        (
            index
            for index, image in enumerate(images)
            if image.id == image_id
        ),
        None,
    )

    if current_index is None:
        abort(404)

    target_index = (
        current_index - 1
        if direction == "up"
        else current_index + 1
    )

    if (
        target_index < 0
        or target_index >= len(images)
    ):
        return redirect(
            url_for("admin.site_gallery")
        )

    current_image = images[
        current_index
    ]

    target_image = images[
        target_index
    ]

    try:
        (
            current_image.sort_order,
            target_image.sort_order,
        ) = (
            target_image.sort_order,
            current_image.sort_order,
        )

        db.session.commit()

    except SQLAlchemyError as error:
        db.session.rollback()
        print(error)

        flash(
            "Gallery order could not be changed.",
            "error",
        )

    return redirect(
        url_for("admin.site_gallery")
    )


@admin_bp.route(
    "/gallery/<int:image_id>/delete",
    methods=["POST"],
)
@admin_required
def delete_site_gallery_image(image_id):
    image = db.session.get(
        SiteGalleryImage,
        image_id,
    )

    if not image:
        abort(404)

    image_path = image.image_path

    try:
        db.session.delete(image)
        db.session.flush()
        normalize_site_gallery_order()
        db.session.commit()

        remove_site_gallery_file(
            image_path
        )

        flash(
            "Gallery image deleted.",
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()
        print(error)

        flash(
            "Gallery image could not be deleted.",
            "error",
        )

    return redirect(
        url_for("admin.site_gallery")
    )
