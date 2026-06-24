import re

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import (
    admin_bp,
)
from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)
from capture_pakistan.extensions import db
from capture_pakistan.services.site_setting_service import (
    DEFAULT_SETTINGS,
    ensure_default_settings,
    get_site_settings,
    remove_setting_asset,
    save_setting_upload,
    set_many_settings,
)


EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)

URL_FIELDS = {
    "facebook_url",
    "instagram_url",
    "youtube_url",
    "tiktok_url",
    "linkedin_url",
    "google_profile_url",
    "google_reviews_embed_url",
    "tripadvisor_url",
    "getyourguide_url",
}

EMAIL_FIELDS = {
    "primary_email",
    "booking_email",
    "support_email",
    "invoice_company_email",
}


@admin_bp.route(
    "/settings",
    methods=["GET", "POST"],
)
@admin_required
def site_settings():
    try:
        ensure_default_settings()

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Site settings table error:"
        )
        print(error)

        flash(
            "Site settings table is missing. "
            "Run site_settings_schema.sql first.",
            "error",
        )

        return render_template(
            "admin/settings.html",
            settings=get_site_settings(),
        )

    if request.method == "POST":
        values = {}

        for key in DEFAULT_SETTINGS:
            if key in {
                "logo_path",
                "favicon_path",
                "maintenance_mode",
            }:
                continue

            values[key] = request.form.get(
                key,
                "",
            ).strip()

        values["maintenance_mode"] = (
            "true"
            if request.form.get(
                "maintenance_mode"
            ) == "on"
            else "false"
        )

        for field in EMAIL_FIELDS:
            value = values.get(
                field,
                "",
            )

            if (
                value
                and not EMAIL_PATTERN.match(
                    value
                )
            ):
                flash(
                    f"Please enter a valid email for "
                    f"{field.replace('_', ' ')}.",
                    "error",
                )

                return render_template(
                    "admin/settings.html",
                    settings={
                        **get_site_settings(),
                        **values,
                    },
                )

        for field in URL_FIELDS:
            value = values.get(
                field,
                "",
            )

            if (
                value
                and not value.startswith(
                    (
                        "http://",
                        "https://",
                    )
                )
            ):
                flash(
                    f"{field.replace('_', ' ').title()} "
                    "must start with http:// or https://.",
                    "error",
                )

                return render_template(
                    "admin/settings.html",
                    settings={
                        **get_site_settings(),
                        **values,
                    },
                )

        current_settings = (
            get_site_settings()
        )

        try:
            logo_file = request.files.get(
                "site_logo"
            )

            favicon_file = request.files.get(
                "site_favicon"
            )

            if request.form.get(
                "remove_logo"
            ) == "on":
                remove_setting_asset(
                    current_settings.get(
                        "logo_path"
                    )
                )

                values["logo_path"] = ""

            elif (
                logo_file
                and logo_file.filename
            ):
                new_logo_path = (
                    save_setting_upload(
                        logo_file,
                        "logo",
                    )
                )

                remove_setting_asset(
                    current_settings.get(
                        "logo_path"
                    )
                )

                values["logo_path"] = (
                    new_logo_path
                )

            if request.form.get(
                "remove_favicon"
            ) == "on":
                remove_setting_asset(
                    current_settings.get(
                        "favicon_path"
                    )
                )

                values["favicon_path"] = ""

            elif (
                favicon_file
                and favicon_file.filename
            ):
                new_favicon_path = (
                    save_setting_upload(
                        favicon_file,
                        "favicon",
                    )
                )

                remove_setting_asset(
                    current_settings.get(
                        "favicon_path"
                    )
                )

                values["favicon_path"] = (
                    new_favicon_path
                )

            set_many_settings(values)

            flash(
                "Site settings updated successfully.",
                "success",
            )

            return redirect(
                url_for(
                    "admin.site_settings"
                )
            )

        except ValueError as error:
            db.session.rollback()

            flash(
                str(error),
                "error",
            )

        except SQLAlchemyError as error:
            db.session.rollback()

            print(
                "Site settings update error:"
            )
            print(error)

            flash(
                "Site settings could not be updated.",
                "error",
            )

    return render_template(
        "admin/settings.html",
        settings=get_site_settings(),
    )
