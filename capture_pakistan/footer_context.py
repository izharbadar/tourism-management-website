import re

from types import SimpleNamespace

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.extensions import db


def _destination_slug(value):
    value = str(value or "").strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    return value.strip("-")


def register_public_footer_context(app):
    @app.context_processor
    def inject_public_footer_data():
        from capture_pakistan.models import Tour

        try:
            rows = (
                db.session.query(
                    Tour.destination,
                    func.count(
                        Tour.id
                    ).label(
                        "tour_count"
                    ),
                )
                .filter(
                    Tour.status
                    == "published",
                    Tour.destination.isnot(
                        None
                    ),
                    Tour.destination
                    != "",
                )
                .group_by(
                    Tour.destination
                )
                .order_by(
                    func.count(
                        Tour.id
                    ).desc(),
                    Tour.destination.asc(),
                )
                .limit(6)
                .all()
            )

            destinations = [
                SimpleNamespace(
                    name=destination,
                    slug=_destination_slug(
                        destination
                    ),
                    tour_count=int(
                        tour_count or 0
                    ),
                )
                for (
                    destination,
                    tour_count,
                ) in rows
            ]

        except SQLAlchemyError:
            db.session.rollback()
            destinations = []

        return {
            "footer_destinations": (
                destinations
            ),
        }
