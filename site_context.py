from datetime import datetime

from flask import (
    render_template,
    request,
)
from flask_login import current_user

from capture_pakistan.services.site_setting_service import (
    get_site_settings,
    setting_is_true,
)


def register_site_context(app):
    @app.context_processor
    def inject_site_settings():
        return {
            "site_settings": (
                get_site_settings(
                    public_only=True
                )
            ),
            "current_year": (
                datetime.now().year
            ),
        }

    @app.before_request
    def handle_maintenance_mode():
        if request.endpoint == "static":
            return None

        settings = get_site_settings(
            public_only=True
        )

        if not setting_is_true(
            settings.get(
                "maintenance_mode"
            )
        ):
            return None

        if request.blueprint in {
            "admin",
            "auth",
        }:
            return None

        if (
            current_user.is_authenticated
            and current_user.role == "admin"
        ):
            return None

        return (
            render_template(
                "public/maintenance.html",
            ),
            503,
        )
