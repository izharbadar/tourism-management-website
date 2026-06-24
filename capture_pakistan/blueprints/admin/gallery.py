from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import admin_bp
from capture_pakistan.blueprints.admin.decorators import admin_required
from capture_pakistan.extensions import db
from capture_pakistan.models import Tour, TourImage
from capture_pakistan.services.gallery_service import (
    normalize_tour_gallery,
    remove_gallery_file,
    save_uploaded_tour_image,
)


@admin_bp.app_errorhandler(413)
def upload_too_large(error):
    flash(
        "The selected upload is too large. Upload fewer images at one time.",
        "error",
    )

    return redirect(request.referrer or url_for("admin.tours"))


@admin_bp.route("/tours/<int:tour_id>/gallery")
@admin_required
def tour_gallery(tour_id):
    tour = db.session.get(Tour, tour_id)

    if not tour:
        abort(404)

    images = TourImage.query.filter_by(
        tour_id=tour.id
    ).order_by(
        TourImage.sort_order.asc(),
        TourImage.id.asc(),
    ).all()

    return render_template(
        "admin/tour_gallery.html",
        tour=tour,
        images=images,
        maximum_images=current_app.config["TOUR_GALLERY_MAX_IMAGES"],
    )


@admin_bp.route(
    "/tours/<int:tour_id>/gallery/upload",
    methods=["POST"],
)
@admin_required
def upload_tour_images(tour_id):
    tour = db.session.get(Tour, tour_id)

    if not tour:
        abort(404)

    uploaded_files = [
        image
        for image in request.files.getlist("gallery_images")
        if image and image.filename
    ]

    if not uploaded_files:
        flash("Please select at least one image.", "error")
        return redirect(
            url_for("admin.tour_gallery", tour_id=tour.id)
        )

    existing_count = TourImage.query.filter_by(
        tour_id=tour.id
    ).count()

    available_slots = max(
        0,
        current_app.config["TOUR_GALLERY_MAX_IMAGES"] - existing_count,
    )

    if available_slots == 0:
        flash(
            "This tour already has the maximum number of gallery images.",
            "error",
        )
        return redirect(
            url_for("admin.tour_gallery", tour_id=tour.id)
        )

    files_to_process = uploaded_files[:available_slots]
    saved_paths = []
    upload_errors = []

    next_sort_order = (
        db.session.query(
            db.func.coalesce(db.func.max(TourImage.sort_order), -1)
        )
        .filter(TourImage.tour_id == tour.id)
        .scalar()
        + 1
    )

    try:
        for uploaded_file in files_to_process:
            try:
                image_path, original_name = save_uploaded_tour_image(
                    uploaded_file,
                    tour,
                )

                saved_paths.append(image_path)

                db.session.add(
                    TourImage(
                        tour_id=tour.id,
                        image_path=image_path,
                        original_name=original_name,
                        alt_text=f"{tour.title} photo",
                        is_cover=False,
                        sort_order=next_sort_order,
                    )
                )

                next_sort_order += 1

            except ValueError as error:
                upload_errors.append(str(error))

        if not saved_paths:
            db.session.rollback()
            flash(
                upload_errors[0]
                if upload_errors
                else "No valid images were uploaded.",
                "error",
            )
            return redirect(
                url_for("admin.tour_gallery", tour_id=tour.id)
            )

        db.session.flush()
        normalize_tour_gallery(tour)
        db.session.commit()

        message = f"{len(saved_paths)} gallery image(s) uploaded successfully."

        if len(uploaded_files) > available_slots:
            message += " Some images were skipped because the gallery limit was reached."

        flash(message, "success")

        if upload_errors:
            flash(upload_errors[0], "error")

    except SQLAlchemyError as error:
        db.session.rollback()

        for image_path in saved_paths:
            remove_gallery_file(image_path)

        print("Gallery upload error:")
        print(error)
        flash("Gallery images could not be saved.", "error")

    return redirect(
        url_for("admin.tour_gallery", tour_id=tour.id)
    )


@admin_bp.route(
    "/tours/<int:tour_id>/gallery/<int:image_id>/cover",
    methods=["POST"],
)
@admin_required
def set_gallery_cover(tour_id, image_id):
    tour = db.session.get(Tour, tour_id)
    image = TourImage.query.filter_by(
        id=image_id,
        tour_id=tour_id,
    ).first()

    if not tour or not image:
        abort(404)

    try:
        TourImage.query.filter_by(tour_id=tour.id).update(
            {TourImage.is_cover: False},
            synchronize_session=False,
        )

        image.is_cover = True
        image.sort_order = -1
        db.session.flush()
        normalize_tour_gallery(tour)
        db.session.commit()
        flash("Gallery cover image updated.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Set gallery cover error:")
        print(error)
        flash("Cover image could not be updated.", "error")

    return redirect(
        url_for("admin.tour_gallery", tour_id=tour.id)
    )


@admin_bp.route(
    "/tours/<int:tour_id>/gallery/<int:image_id>/alt",
    methods=["POST"],
)
@admin_required
def update_gallery_alt(tour_id, image_id):
    image = TourImage.query.filter_by(
        id=image_id,
        tour_id=tour_id,
    ).first_or_404()

    alt_text = request.form.get("alt_text", "").strip()

    try:
        image.alt_text = alt_text[:180] or None
        db.session.commit()
        flash("Image alternative text updated.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Update gallery alt error:")
        print(error)
        flash("Image text could not be updated.", "error")

    return redirect(
        url_for("admin.tour_gallery", tour_id=tour_id)
    )


@admin_bp.route(
    "/tours/<int:tour_id>/gallery/<int:image_id>/move",
    methods=["POST"],
)
@admin_required
def move_gallery_image(tour_id, image_id):
    direction = request.form.get("direction", "").strip()

    if direction not in {"up", "down"}:
        abort(400)

    image = TourImage.query.filter_by(
        id=image_id,
        tour_id=tour_id,
    ).first_or_404()

    if image.is_cover:
        flash("The cover image always remains first in the gallery.", "error")
        return redirect(
            url_for("admin.tour_gallery", tour_id=tour_id)
        )

    images = TourImage.query.filter_by(
        tour_id=tour_id,
        is_cover=False,
    ).order_by(
        TourImage.sort_order.asc(),
        TourImage.id.asc(),
    ).all()

    current_index = next(
        (
            index
            for index, item in enumerate(images)
            if item.id == image.id
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

    if target_index < 0 or target_index >= len(images):
        return redirect(
            url_for("admin.tour_gallery", tour_id=tour_id)
        )

    target_image = images[target_index]

    try:
        image.sort_order, target_image.sort_order = (
            target_image.sort_order,
            image.sort_order,
        )

        db.session.flush()
        tour = db.session.get(Tour, tour_id)
        normalize_tour_gallery(tour)
        db.session.commit()

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Move gallery image error:")
        print(error)
        flash("Gallery order could not be changed.", "error")

    return redirect(
        url_for("admin.tour_gallery", tour_id=tour_id)
    )


@admin_bp.route(
    "/tours/<int:tour_id>/gallery/<int:image_id>/delete",
    methods=["POST"],
)
@admin_required
def delete_gallery_image(tour_id, image_id):
    tour = db.session.get(Tour, tour_id)
    image = TourImage.query.filter_by(
        id=image_id,
        tour_id=tour_id,
    ).first()

    if not tour or not image:
        abort(404)

    image_path = image.image_path

    try:
        db.session.delete(image)
        db.session.flush()
        normalize_tour_gallery(tour)
        db.session.commit()
        remove_gallery_file(image_path)
        flash("Gallery image deleted.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Delete gallery image error:")
        print(error)
        flash("Gallery image could not be deleted.", "error")

    return redirect(
        url_for("admin.tour_gallery", tour_id=tour.id)
    )
