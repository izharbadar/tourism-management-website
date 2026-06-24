import secrets

from datetime import date

from urllib.parse import (
    urljoin,
    urlparse,
)

from flask import request

from capture_pakistan.models import (
    TourInquiry,
)


def is_safe_redirect_target(target):
    """
    Login ke baad user ko sirf apni website
    ke safe URL par redirect karta hai.
    """

    if not target:
        return False

    host_url = urlparse(
        request.host_url
    )

    redirect_url = urlparse(
        urljoin(
            request.host_url,
            target,
        )
    )

    return (
        redirect_url.scheme
        in {"http", "https"}
        and host_url.netloc
        == redirect_url.netloc
    )


def generate_inquiry_number():
    """
    Unique tour inquiry reference generate karta hai.
    Example: INQ-20260608-A8F37C12
    """

    while True:
        reference = (
            f"INQ-{date.today():%Y%m%d}-"
            f"{secrets.token_hex(4).upper()}"
        )

        existing_inquiry = (
            TourInquiry.query.filter_by(
                inquiry_number=reference
            ).first()
        )

        if not existing_inquiry:
            return reference