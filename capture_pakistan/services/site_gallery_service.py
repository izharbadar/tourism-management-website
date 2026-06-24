import os
import secrets
from pathlib import Path

from PIL import Image
Image.MAX_IMAGE_PIXELS = 40_000_000

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename

from capture_pakistan.extensions import db
from capture_pakistan.models.site_gallery import (
    SiteGalleryImage,
)


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
}


def site_gallery_root():
    folder = (
        Path(current_app.static_folder)
        / "uploads"
        / "gallery"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return folder


def site_gallery_absolute_path(image_path):
    image_path = str(
        image_path or ""
    ).strip()

    if not image_path:
        return None

    static_root = Path(
        current_app.static_folder
    ).resolve()

    candidate = (
        static_root / image_path
    ).resolve()

    if (
        candidate == static_root
        or static_root not in candidate.parents
    ):
        return None

    return candidate


def remove_site_gallery_file(image_path):
    absolute_path = site_gallery_absolute_path(
        image_path
    )

    if (
        absolute_path
        and absolute_path.exists()
        and absolute_path.is_file()
    ):
        absolute_path.unlink()


def normalize_site_gallery_order():
    images = SiteGalleryImage.query.order_by(
        SiteGalleryImage.sort_order.asc(),
        SiteGalleryImage.id.asc(),
    ).all()

    for index, image in enumerate(images):
        image.sort_order = index

    db.session.flush()


def save_uploaded_site_gallery_image(
    uploaded_file,
):
    original_name = secure_filename(
        uploaded_file.filename or ""
    )

    if not original_name:
        raise ValueError(
            "An uploaded file has no valid filename."
        )

    extension = (
        original_name.rsplit(
            ".",
            1,
        )[-1].lower()
        if "." in original_name
        else ""
    )

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"{original_name}: only JPG, PNG and WEBP "
            "files are allowed."
        )

    uploaded_file.stream.seek(
        0,
        os.SEEK_END,
    )

    file_size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)

    maximum_file_size = current_app.config.get(
        "SITE_GALLERY_MAX_FILE_SIZE",
        8 * 1024 * 1024,
    )

    if (
        file_size <= 0
        or file_size > maximum_file_size
    ):
        raise ValueError(
            f"{original_name}: image must be smaller "
            "than 8 MB."
        )

    try:
        with Image.open(
            uploaded_file.stream
        ) as source_image:
            source_image.load()

            if getattr(
                source_image,
                "is_animated",
                False,
            ):
                raise ValueError(
                    f"{original_name}: animated images "
                    "are not supported."
                )

            processed_image = (
                ImageOps.exif_transpose(
                    source_image
                )
            )

            processed_image.thumbnail(
                (2600, 2000),
                Image.Resampling.LANCZOS,
            )

            if (
                processed_image.mode
                in {"RGBA", "LA"}
                or (
                    processed_image.mode == "P"
                    and "transparency"
                    in processed_image.info
                )
            ):
                processed_image = (
                    processed_image.convert(
                        "RGBA"
                    )
                )
            else:
                processed_image = (
                    processed_image.convert(
                        "RGB"
                    )
                )

            filename = (
                f"{secrets.token_hex(16)}.webp"
            )

            destination = (
                site_gallery_root()
                / filename
            )

            processed_image.save(
                destination,
                format="WEBP",
                quality=87,
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
            f"{original_name}: this is not a valid "
            "supported image."
        ) from error

    relative_path = (
        Path("uploads")
        / "gallery"
        / filename
    ).as_posix()

    return (
        relative_path,
        original_name,
    )
