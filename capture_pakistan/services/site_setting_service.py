from pathlib import Path
from uuid import uuid4

from flask import (
    current_app,
    g,
    has_request_context,
)
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from capture_pakistan.extensions import db
from capture_pakistan.models.site_setting import (
    SiteSetting,
)


DEFAULT_SETTINGS = {
    "site_name": {
        "value": "Capture Pakistan",
        "group": "general",
        "type": "text",
        "public": True,
        "order": 10,
    },
    "site_tagline": {
        "value": "Explore beyond the ordinary",
        "group": "general",
        "type": "text",
        "public": True,
        "order": 20,
    },
    "footer_tagline": {
        "value": "Unseen. Untouched. Unforgettable.",
        "group": "general",
        "type": "text",
        "public": True,
        "order": 30,
    },
    "footer_description": {
        "value": (
            "Carefully planned tours, trekking adventures "
            "and customized journeys across Pakistan."
        ),
        "group": "general",
        "type": "textarea",
        "public": True,
        "order": 40,
    },
    "primary_email": {
        "value": "info@capturepakistan.com",
        "group": "contact",
        "type": "email",
        "public": True,
        "order": 10,
    },
    "booking_email": {
        "value": "info@capturepakistan.com",
        "group": "contact",
        "type": "email",
        "public": True,
        "order": 20,
    },
    "support_email": {
        "value": "info@capturepakistan.com",
        "group": "contact",
        "type": "email",
        "public": True,
        "order": 30,
    },
    "phone_display": {
        "value": "+92 327 1125667",
        "group": "contact",
        "type": "phone",
        "public": True,
        "order": 40,
    },
    "phone_link": {
        "value": "+923271125667",
        "group": "contact",
        "type": "phone",
        "public": True,
        "order": 50,
    },
    "whatsapp_number": {
        "value": "923271125667",
        "group": "contact",
        "type": "phone",
        "public": True,
        "order": 60,
    },
    "office_address": {
        "value": "Pakistan",
        "group": "contact",
        "type": "textarea",
        "public": True,
        "order": 70,
    },
    "facebook_url": {
        "value": "",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 10,
    },
    "instagram_url": {
        "value": "",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 20,
    },
    "youtube_url": {
        "value": "",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 30,
    },
    "tiktok_url": {
        "value": "",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 40,
    },
    "linkedin_url": {
        "value": "",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 50,
    },
    "google_profile_url": {
        "value": "https://share.google/itoWmWFA9XMoo80iP",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 60,
    },
    "google_reviews_embed_url": {
        "value": "https://www.google.com/maps?q=Capture%20Pakistan%20Tourism%20Lahore&output=embed",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 70,
    },
    "tripadvisor_url": {
        "value": "https://www.tripadvisor.com/Attraction_Review-g295413-d26732537-Reviews-Capture_Pakistan_Tourism-Lahore_Punjab_Province.html",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 80,
    },
    "getyourguide_url": {
        "value": "",
        "group": "social",
        "type": "url",
        "public": True,
        "order": 90,
    },
    "email_sender_name": {
        "value": "Capture Pakistan",
        "group": "communication",
        "type": "text",
        "public": False,
        "order": 10,
    },
    "default_cancellation_policy": {
        "value": (
            "Free cancellation up to 24 hours before "
            "the scheduled departure time."
        ),
        "group": "communication",
        "type": "textarea",
        "public": True,
        "order": 20,
    },
    "booking_confirmation_message": {
        "value": (
            "Your booking has been received. Our team will "
            "contact you shortly and share the final tour details."
        ),
        "group": "communication",
        "type": "textarea",
        "public": True,
        "order": 30,
    },
    "invoice_company_name": {
        "value": "Capture Pakistan",
        "group": "invoice",
        "type": "text",
        "public": False,
        "order": 10,
    },
    "invoice_company_email": {
        "value": "info@capturepakistan.com",
        "group": "invoice",
        "type": "email",
        "public": False,
        "order": 20,
    },
    "invoice_company_phone": {
        "value": "+92 327 1125667",
        "group": "invoice",
        "type": "phone",
        "public": False,
        "order": 30,
    },
    "invoice_company_address": {
        "value": "Pakistan",
        "group": "invoice",
        "type": "textarea",
        "public": False,
        "order": 40,
    },
    "currency_code": {
        "value": "PKR",
        "group": "invoice",
        "type": "text",
        "public": True,
        "order": 50,
    },
    "currency_symbol": {
        "value": "PKR",
        "group": "invoice",
        "type": "text",
        "public": True,
        "order": 60,
    },
    "logo_path": {
        "value": "",
        "group": "branding",
        "type": "image",
        "public": True,
        "order": 10,
    },
    "favicon_path": {
        "value": "",
        "group": "branding",
        "type": "image",
        "public": True,
        "order": 20,
    },
    "maintenance_mode": {
        "value": "false",
        "group": "maintenance",
        "type": "boolean",
        "public": True,
        "order": 10,
    },
    "maintenance_message": {
        "value": (
            "We are improving the website and will be back shortly. "
            "Please contact our team for urgent booking assistance."
        ),
        "group": "maintenance",
        "type": "textarea",
        "public": True,
        "order": 20,
    },
}


def default_setting_values():
    return {
        key: metadata["value"]
        for key, metadata
        in DEFAULT_SETTINGS.items()
    }


def clear_settings_cache():
    if has_request_context():
        g.pop(
            "_capture_pakistan_settings",
            None,
        )


def setting_is_true(value):
    return str(
        value or ""
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def ensure_default_settings():
    existing_keys = {
        row.setting_key
        for row in SiteSetting.query.with_entities(
            SiteSetting.setting_key
        ).all()
    }

    created = 0

    for key, metadata in DEFAULT_SETTINGS.items():
        if key in existing_keys:
            continue

        db.session.add(
            SiteSetting(
                setting_key=key,
                setting_value=metadata["value"],
                setting_group=metadata["group"],
                value_type=metadata["type"],
                is_public=metadata["public"],
                sort_order=metadata["order"],
            )
        )

        created += 1

    if created:
        db.session.commit()
        clear_settings_cache()

    return created


def get_site_settings(public_only=False):
    cache_key = (
        "public"
        if public_only
        else "all"
    )

    if has_request_context():
        cache = getattr(
            g,
            "_capture_pakistan_settings",
            {},
        )

        if cache_key in cache:
            return cache[cache_key]

    values = default_setting_values()

    try:
        query = SiteSetting.query

        if public_only:
            query = query.filter(
                SiteSetting.is_public.is_(True)
            )

        rows = query.all()

        for row in rows:
            values[row.setting_key] = (
                row.setting_value or ""
            )

    except SQLAlchemyError:
        db.session.rollback()

    if has_request_context():
        cache = getattr(
            g,
            "_capture_pakistan_settings",
            {},
        )

        cache[cache_key] = values

        g._capture_pakistan_settings = cache

    return values


def get_setting(
    setting_key,
    default=None,
):
    values = get_site_settings(
        public_only=False
    )

    if setting_key in values:
        return values[setting_key]

    return default


def set_setting(
    setting_key,
    setting_value,
):
    metadata = DEFAULT_SETTINGS.get(
        setting_key,
        {
            "group": "general",
            "type": "text",
            "public": True,
            "order": 999,
        },
    )

    row = SiteSetting.query.filter_by(
        setting_key=setting_key
    ).first()

    if not row:
        row = SiteSetting(
            setting_key=setting_key,
        )

        db.session.add(row)

    row.setting_value = (
        ""
        if setting_value is None
        else str(setting_value).strip()
    )

    row.setting_group = metadata["group"]
    row.value_type = metadata["type"]
    row.is_public = metadata["public"]
    row.sort_order = metadata["order"]

    clear_settings_cache()

    return row


def set_many_settings(values):
    for key, value in values.items():
        if key not in DEFAULT_SETTINGS:
            continue

        set_setting(
            key,
            value,
        )

    db.session.commit()
    clear_settings_cache()


def _allowed_extension(
    filename,
    allowed_extensions,
):
    if "." not in filename:
        return False

    extension = (
        filename.rsplit(
            ".",
            1,
        )[1]
        .lower()
    )

    return extension in allowed_extensions


def save_setting_upload(
    uploaded_file,
    asset_type,
):
    if not uploaded_file:
        return None

    original_name = secure_filename(
        uploaded_file.filename or ""
    )

    if not original_name:
        return None

    if asset_type == "favicon":
        allowed_extensions = {
            "png",
            "jpg",
            "jpeg",
            "webp",
            "ico",
        }
    else:
        allowed_extensions = {
            "png",
            "jpg",
            "jpeg",
            "webp",
        }

    if not _allowed_extension(
        original_name,
        allowed_extensions,
    ):
        raise ValueError(
            "Please upload a PNG, JPG, JPEG, WEBP"
            + (
                " or ICO file."
                if asset_type == "favicon"
                else " file."
            )
        )

    extension = original_name.rsplit(
        ".",
        1,
    )[1].lower()

    filename = (
        f"{asset_type}-"
        f"{uuid4().hex}."
        f"{extension}"
    )

    upload_directory = (
        Path(current_app.static_folder)
        / "uploads"
        / "settings"
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        upload_directory
        / filename
    )

    uploaded_file.save(
        destination
    )

    return (
        "uploads/settings/"
        f"{filename}"
    )


def remove_setting_asset(
    relative_path,
):
    relative_path = str(
        relative_path or ""
    ).strip()

    if not relative_path.startswith(
        "uploads/settings/"
    ):
        return

    file_path = (
        Path(current_app.static_folder)
        / relative_path
    )

    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        pass
