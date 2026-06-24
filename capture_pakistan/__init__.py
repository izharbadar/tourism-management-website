from pathlib import Path

from flask import Flask

from capture_pakistan.config import (
    Config,
    validate_production_config,
)
from capture_pakistan.extensions import (
    csrf,
    db,
    limiter,
    login_manager,
)


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_object(Config)
    validate_production_config(app)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Import all models before routes so relationships resolve correctly.
    from capture_pakistan import models  # noqa: F401

    from capture_pakistan.blueprints.admin import admin_bp
    from capture_pakistan.blueprints.auth import auth_bp
    from capture_pakistan.blueprints.customer import customer_bp
    from capture_pakistan.blueprints.public import public_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    from capture_pakistan.site_context import register_site_context
    from capture_pakistan.footer_context import (
        register_public_footer_context,
    )
    from capture_pakistan.seo import register_seo
    from capture_pakistan.security import register_security

    register_site_context(app)
    register_public_footer_context(app)
    register_seo(app)
    register_security(app)

    writable_directories = (
        Path(app.static_folder) / "uploads" / "tours",
        Path(app.static_folder) / "uploads" / "gallery",
        Path(app.static_folder) / "uploads" / "settings",
        Path(app.static_folder) / "documents",
        Path(app.root_path).parent / "logs",
    )

    for directory in writable_directories:
        directory.mkdir(parents=True, exist_ok=True)

    if (
        app.config.get("IS_PRODUCTION")
        and app.config.get("RATELIMIT_STORAGE_URI") == "memory://"
    ):
        app.logger.warning(
            "RATELIMIT_STORAGE_URI uses memory:// in production. "
            "Use Redis when the hosting environment supports it."
        )

    return app
