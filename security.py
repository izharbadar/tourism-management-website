import logging
import os

from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import (
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    session,
)
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

from capture_pakistan.extensions import db, limiter


SENSITIVE_PREFIXES = (
    "/admin",
    "/dashboard",
    "/login",
    "/register",
)


RATE_LIMITS = {
    "auth.login": "5 per minute",
    "auth.register": "3 per hour",
    "public.quote": "5 per 10 minutes",
    "public.submit_tour_inquiry": "5 per 10 minutes",
    "public.tour_search_api": "120 per minute",
    "customer.booking_checkout": "20 per hour",
    "customer.book_tour": "5 per hour",
    "customer.booking_review": "5 per hour",
    "customer.submit_review": "5 per hour",
    "admin.test_email_recipient": "5 per minute",
}


def _is_json_request():
    return (
        request.path.startswith("/api/")
        or request.is_json
        or request.accept_mimetypes.best
        == "application/json"
    )


def _render_error(code, title, message):
    if _is_json_request():
        return (
            jsonify(
                {
                    "error": title,
                    "message": message,
                    "status": code,
                }
            ),
            code,
        )

    return (
        render_template(
            "errors/security_error.html",
            error_code=code,
            error_title=title,
            error_message=message,
        ),
        code,
    )


def _configure_security_logger(app):
    log_folder = Path(app.root_path).parent / "logs"
    log_folder.mkdir(parents=True, exist_ok=True)

    log_path = log_folder / "security.log"

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    handler.setLevel(logging.WARNING)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"
        )
    )

    security_logger = logging.getLogger(
        "capture_pakistan.security"
    )
    security_logger.setLevel(logging.WARNING)

    if not security_logger.handlers:
        security_logger.addHandler(handler)

    security_logger.propagate = False
    app.extensions["security_logger"] = security_logger


def _security_logger():
    return current_app.extensions.get(
        "security_logger",
        current_app.logger,
    )


def _apply_rate_limits(app):
    applied = []

    for endpoint, limit_value in RATE_LIMITS.items():
        view_function = app.view_functions.get(endpoint)

        if view_function is None:
            continue

        if getattr(
            view_function,
            "_capture_security_limited",
            False,
        ):
            continue

        wrapped = limiter.limit(limit_value)(
            view_function
        )
        wrapped._capture_security_limited = True
        app.view_functions[endpoint] = wrapped
        applied.append(endpoint)

    app.extensions["security_rate_limits"] = applied


def register_security(app):
    if app.config.get("SECURITY_BEHIND_PROXY"):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
        )

    _configure_security_logger(app)
    _apply_rate_limits(app)

    @app.before_request
    def security_before_request():
        session.permanent = True


    @app.after_request
    def security_headers(response):
        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )
        response.headers.setdefault(
            "X-Frame-Options",
            "SAMEORIGIN",
        )
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault(
            "Cross-Origin-Opener-Policy",
            "same-origin",
        )
        response.headers.setdefault(
            "Cross-Origin-Resource-Policy",
            "same-site",
        )
        response.headers.setdefault(
            "Content-Security-Policy-Report-Only",
            (
                "default-src 'self'; "
                "base-uri 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'self'; "
                "form-action 'self'; "
                "img-src 'self' data: blob: https:; "
                "font-src 'self' data: "
                "https://fonts.gstatic.com "
                "https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com "
                "https://cdnjs.cloudflare.com; "
                "script-src 'self' 'unsafe-inline' "
                "https://cdnjs.cloudflare.com; "
                "connect-src 'self'; "
                "frame-src 'self' https://www.google.com "
                "https://www.google.com/maps;"
            ),
        )

        if request.path.startswith(SENSITIVE_PREFIXES):
            response.headers.setdefault(
                "Cache-Control",
                "no-store, max-age=0",
            )
            response.headers.setdefault(
                "Pragma",
                "no-cache",
            )

        if (
            app.config.get("SECURITY_ENABLE_HSTS")
            and request.is_secure
        ):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        if response.status_code in {401, 403, 429}:
            _security_logger().warning(
                "status=%s method=%s path=%s ip=%s user=%s",
                response.status_code,
                request.method,
                request.path,
                request.remote_addr,
                (
                    current_user.get_id()
                    if current_user.is_authenticated
                    else "anonymous"
                ),
            )

        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        _security_logger().warning(
            "csrf_failure method=%s path=%s ip=%s reason=%s",
            request.method,
            request.path,
            request.remote_addr,
            error.description,
        )

        return _render_error(
            400,
            "Security Check Failed",
            (
                "This form expired or could not be verified. "
                "Refresh the page and submit it again."
            ),
        )

    @app.errorhandler(403)
    def forbidden_error(error):
        return _render_error(
            403,
            "Access Denied",
            "You do not have permission to access this page.",
        )

    @app.errorhandler(404)
    def not_found_error(error):
        return _render_error(
            404,
            "Page Not Found",
            "The page you requested could not be found.",
        )

    @app.errorhandler(413)
    def request_too_large(error):
        return _render_error(
            413,
            "Upload Too Large",
            "The selected upload exceeds the allowed size.",
        )

    @app.errorhandler(429)
    def rate_limit_error(error):
        return _render_error(
            429,
            "Too Many Requests",
            (
                "Too many requests were received. "
                "Please wait briefly and try again."
            ),
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        try:
            db.session.rollback()
        except Exception:
            pass

        _security_logger().error(
            "server_error method=%s path=%s ip=%s",
            request.method,
            request.path,
            request.remote_addr,
        )

        return _render_error(
            500,
            "Something Went Wrong",
            (
                "The request could not be completed. "
                "Please try again later."
            ),
        )
