from flask import flash, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import admin_bp
from capture_pakistan.blueprints.admin.decorators import admin_required
from capture_pakistan.extensions import db


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    try:
        stats = db.session.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM tours) AS total_tours,

                    (
                        SELECT COUNT(*)
                        FROM tours
                        WHERE status = 'published'
                    ) AS published_tours,

                    (SELECT COUNT(*) FROM bookings) AS total_bookings,

                    (
                        SELECT COUNT(*)
                        FROM bookings
                        WHERE booking_status = 'pending'
                    ) AS pending_bookings,

                    (
                        (
                            SELECT COUNT(*)
                            FROM inquiries
                            WHERE status = 'new'
                        )
                        +
                        (
                            SELECT COUNT(*)
                            FROM tour_inquiries
                            WHERE inquiry_status = 'new'
                        )
                    ) AS new_inquiries,

                    (
                        SELECT COUNT(*)
                        FROM users
                        WHERE role = 'customer'
                    ) AS total_customers,

                    (
                        SELECT COALESCE(SUM(paid_amount), 0)
                        FROM bookings
                        WHERE payment_status != 'refunded'
                    ) AS total_revenue
                """
            )
        ).mappings().one()

        recent_bookings = db.session.execute(
            text(
                """
                SELECT
                    bookings.id,
                    bookings.booking_number,
                    bookings.customer_name,
                    bookings.total_amount,
                    bookings.booking_status,
                    bookings.payment_status,
                    bookings.created_at,
                    COALESCE(
                        tours.title,
                        bookings.custom_tour_name,
                        'Custom Tour'
                    ) AS tour_title

                FROM bookings

                LEFT JOIN tours
                    ON tours.id = bookings.tour_id

                ORDER BY bookings.created_at DESC

                LIMIT 5
                """
            )
        ).mappings().all()

        recent_inquiries = db.session.execute(
            text(
                """
                SELECT
                    combined.id,
                    combined.name,
                    combined.phone,
                    combined.destination,
                    combined.status,
                    combined.created_at

                FROM (
                    SELECT
                        inquiries.id AS id,
                        inquiries.name AS name,
                        inquiries.phone AS phone,
                        inquiries.destination AS destination,
                        inquiries.status AS status,
                        inquiries.created_at AS created_at

                    FROM inquiries

                    UNION ALL

                    SELECT
                        tour_inquiries.id AS id,
                        tour_inquiries.customer_name AS name,
                        tour_inquiries.customer_phone AS phone,
                        tours.title AS destination,
                        tour_inquiries.inquiry_status AS status,
                        tour_inquiries.created_at AS created_at

                    FROM tour_inquiries

                    INNER JOIN tours
                        ON tours.id = tour_inquiries.tour_id
                ) AS combined

                ORDER BY combined.created_at DESC

                LIMIT 5
                """
            )
        ).mappings().all()

    except SQLAlchemyError as error:
        print("Admin dashboard database error:")
        print(error)

        flash(
            "Dashboard data could not be loaded.",
            "error",
        )

        stats = {
            "total_tours": 0,
            "published_tours": 0,
            "total_bookings": 0,
            "pending_bookings": 0,
            "new_inquiries": 0,
            "total_customers": 0,
            "total_revenue": 0,
        }

        recent_bookings = []
        recent_inquiries = []

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_bookings=recent_bookings,
        recent_inquiries=recent_inquiries,
    )
