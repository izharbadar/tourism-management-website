import os
import secrets
import shutil
from pathlib import Path

from PIL import Image
Image.MAX_IMAGE_PIXELS = 40_000_000

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename

from capture_pakistan.models import TourImage


ALLOWED_GALLERY_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
}


def gallery_root():
    folder = Path(current_app.static_folder) / "uploads" / "tours"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def gallery_folder_for_tour(tour_id):
    folder = gallery_root() / str(tour_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def remove_tour_gallery_folder(tour_id):
    folder = gallery_root() / str(tour_id)

    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)


def gallery_file_absolute_path(image_path):
    static_root = Path(current_app.static_folder).resolve()
    candidate = (static_root / image_path).resolve()

    if candidate == static_root or static_root not in candidate.parents:
        return None

    return candidate


def remove_gallery_file(image_path):
    absolute_path = gallery_file_absolute_path(image_path)

    if absolute_path and absolute_path.exists() and absolute_path.is_file():
        absolute_path.unlink()


def normalize_tour_gallery(tour):
    images = TourImage.query.filter_by(
        tour_id=tour.id
    ).order_by(
        TourImage.sort_order.asc(),
        TourImage.id.asc(),
    ).all()

    if not images:
        if tour.main_image and tour.main_image.startswith(
            "/static/uploads/tours/"
        ):
            tour.main_image = None

        return

    cover = next(
        (image for image in images if image.is_cover),
        images[0],
    )

    ordered_images = [
        cover,
        *[image for image in images if image.id != cover.id],
    ]

    for index, image in enumerate(ordered_images):
        image.is_cover = image.id == cover.id
        image.sort_order = index

    tour.main_image = f"/static/{cover.image_path}"


def save_uploaded_tour_image(uploaded_file, tour):
    original_name = secure_filename(uploaded_file.filename or "")

    if not original_name:
        raise ValueError("An uploaded file has no valid filename.")

    extension = (
        original_name.rsplit(".", 1)[-1].lower()
        if "." in original_name
        else ""
    )

    if extension not in ALLOWED_GALLERY_EXTENSIONS:
        raise ValueError(
            f"{original_name}: only JPG, PNG and WEBP files are allowed."
        )

    uploaded_file.stream.seek(0, os.SEEK_END)
    file_size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)

    if (
        file_size <= 0
        or file_size > current_app.config["TOUR_GALLERY_MAX_FILE_SIZE"]
    ):
        raise ValueError(
            f"{original_name}: image must be smaller than 8 MB."
        )

    try:
        with Image.open(uploaded_file.stream) as source_image:
            source_image.load()

            if getattr(source_image, "is_animated", False):
                raise ValueError(
                    f"{original_name}: animated images are not supported."
                )

            processed_image = ImageOps.exif_transpose(source_image)
            processed_image.thumbnail(
                (2400, 1800),
                Image.Resampling.LANCZOS,
            )

            if processed_image.mode in {"RGBA", "LA"} or (
                processed_image.mode == "P"
                and "transparency" in processed_image.info
            ):
                processed_image = processed_image.convert("RGBA")
            else:
                processed_image = processed_image.convert("RGB")

            filename = f"{secrets.token_hex(16)}.webp"
            destination = gallery_folder_for_tour(tour.id) / filename

            processed_image.save(
                destination,
                format="WEBP",
                quality=86,
                method=6,
            )

    except ValueError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ) as error:
        raise ValueError(
            f"{original_name}: this is not a valid supported image."
        ) from error

    relative_path = (
        Path("uploads")
        / "tours"
        / str(tour.id)
        / filename
    ).as_posix()

    return relative_path, original_name
