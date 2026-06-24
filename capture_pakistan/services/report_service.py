import csv
import io

from calendar import monthrange
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from decimal import Decimal
from pathlib import Path

from flask import current_app
from sqlalchemy import text

from capture_pakistan.extensions import db


ALLOWED_PRESETS = {
    "today",
    "7d",
    "30d",
    "month",
    "year",
    "custom",
}


def _as_number(value):
    if value is None:
        return 0

    if isinstance(value, Decimal):
        return float(value)

    return value


def _parse_iso_date(value):
    try:
        return date.fromisoformat(
            (value or "").strip()
        )
    except (TypeError, ValueError):
        return None


def resolve_report_range(args):
    today = date.today()

    preset = (
        args.get(
            "range",
            "30d",
        )
        .strip()
        .lower()
    )

    if preset not in ALLOWED_PRESETS:
        preset = "30d"

    if preset == "today":
        start_date = today
        end_date = today

    elif preset == "7d":
        start_date = today - timedelta(
            days=6
        )
        end_date = today

    elif preset == "month":
        start_date = today.replace(
            day=1
        )
        end_date = today

    elif preset == "year":
        start_date = today.replace(
            month=1,
            day=1,
        )
        end_date = today

    elif preset == "custom":
        start_date = _parse_iso_date(
            args.get("start_date")
        )

        end_date = _parse_iso_date(
            args.get("end_date")
        )

        if not start_date or not end_date:
            preset = "30d"
            start_date = today - timedelta(
                days=29
            )
            end_date = today

    else:
        preset = "30d"
        start_date = today - timedelta(
            days=29
        )
        end_date = today

    if end_date > today:
        end_date = today

    if start_date > end_date:
        start_date, end_date = (
            end_date,
            start_date,
        )

    maximum_start = end_date - timedelta(
        days=365
    )

    if start_date < maximum_start:
        start_date = maximum_start

    start_at = datetime.combine(
        start_date,
        time.min,
    )

    end_at = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
    )

    return {
        "preset": preset,
        "start_date": start_date,
        "end_date": end_date,
        "start_at": start_at,
        "end_at": end_at,
        "label": (
            f"{start_date:%d %b %Y} – "
            f"{end_date:%d %b %Y}"
        ),
        "days": (
            end_date - start_date
        ).days + 1,
    }


def _table_exists(table_name):
    result = db.session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
            """
        ),
        {
            "table_name": table_name,
        },
    ).scalar()

    return bool(result)


def _summary_data(report_range):
    params = {
        "start_at": report_range[
            "start_at"
        ],
        "end_at": report_range[
            "end_at"
        ],
    }

    booking_summary = (
        db.session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_bookings,

                    SUM(
                        CASE
                            WHEN booking_status = 'pending'
                            THEN 1 ELSE 0
                        END
                    ) AS pending_bookings,

                    SUM(
                        CASE
                            WHEN booking_status = 'confirmed'
                            THEN 1 ELSE 0
                        END
                    ) AS confirmed_bookings,

                    SUM(
                        CASE
                            WHEN booking_status = 'cancelled'
                            THEN 1 ELSE 0
                        END
                    ) AS cancelled_bookings,

                    SUM(
                        CASE
                            WHEN booking_status = 'completed'
                            THEN 1 ELSE 0
                        END
                    ) AS completed_bookings,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status != 'refunded'
                                THEN paid_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS paid_revenue,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status != 'refunded'
                                 AND booking_status != 'cancelled'
                                THEN balance_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS pending_payments,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN booking_status != 'cancelled'
                                THEN total_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS booking_value,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN booking_status != 'cancelled'
                                THEN total_travelers
                                ELSE 0
                            END
                        ),
                        0
                    ) AS travelers

                FROM bookings

                WHERE created_at >= :start_at
                  AND created_at < :end_at
                """
            ),
            params,
        )
        .mappings()
        .one()
    )

    customer_count = (
        db.session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM users
                WHERE role = 'customer'
                  AND created_at >= :start_at
                  AND created_at < :end_at
                """
            ),
            params,
        ).scalar()
        or 0
    )

    homepage_inquiries = (
        db.session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_count,

                    SUM(
                        CASE
                            WHEN status = 'new'
                            THEN 1 ELSE 0
                        END
                    ) AS new_count

                FROM inquiries

                WHERE created_at >= :start_at
                  AND created_at < :end_at
                """
            ),
            params,
        )
        .mappings()
        .one()
    )

    tour_inquiries = (
        db.session.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_count,

                    SUM(
                        CASE
                            WHEN inquiry_status = 'new'
                            THEN 1 ELSE 0
                        END
                    ) AS new_count,

                    SUM(
                        CASE
                            WHEN inquiry_status = 'converted'
                            THEN 1 ELSE 0
                        END
                    ) AS converted_count

                FROM tour_inquiries

                WHERE created_at >= :start_at
                  AND created_at < :end_at
                """
            ),
            params,
        )
        .mappings()
        .one()
    )

    total_inquiries = (
        int(
            homepage_inquiries[
                "total_count"
            ]
            or 0
        )
        + int(
            tour_inquiries[
                "total_count"
            ]
            or 0
        )
    )

    converted_inquiries = int(
        tour_inquiries[
            "converted_count"
        ]
        or 0
    )

    wishlist_activity = 0
    wishlist_users = 0
    wishlist_tours = 0

    if _table_exists("wishlists"):
        wishlist_summary = (
            db.session.execute(
                text(
                    """
                    SELECT
                        COUNT(*) AS total_saves,
                        COUNT(
                            DISTINCT user_id
                        ) AS unique_users,
                        COUNT(
                            DISTINCT tour_id
                        ) AS unique_tours

                    FROM wishlists

                    WHERE created_at >= :start_at
                      AND created_at < :end_at
                    """
                ),
                params,
            )
            .mappings()
            .one()
        )

        wishlist_activity = int(
            wishlist_summary[
                "total_saves"
            ]
            or 0
        )

        wishlist_users = int(
            wishlist_summary[
                "unique_users"
            ]
            or 0
        )

        wishlist_tours = int(
            wishlist_summary[
                "unique_tours"
            ]
            or 0
        )

    summary = {
        key: _as_number(value)
        for key, value
        in booking_summary.items()
    }

    summary.update(
        {
            "new_customers": int(
                customer_count
            ),
            "total_inquiries": (
                total_inquiries
            ),
            "new_inquiries": (
                int(
                    homepage_inquiries[
                        "new_count"
                    ]
                    or 0
                )
                + int(
                    tour_inquiries[
                        "new_count"
                    ]
                    or 0
                )
            ),
            "converted_inquiries": (
                converted_inquiries
            ),
            "inquiry_conversion_rate": (
                round(
                    (
                        converted_inquiries
                        / total_inquiries
                        * 100
                    ),
                    1,
                )
                if total_inquiries
                else 0
            ),
            "wishlist_activity": (
                wishlist_activity
            ),
            "wishlist_users": (
                wishlist_users
            ),
            "wishlist_tours": (
                wishlist_tours
            ),
        }
    )

    summary["average_booking_value"] = (
        round(
            summary["booking_value"]
            / summary["total_bookings"],
            2,
        )
        if summary["total_bookings"]
        else 0
    )

    return summary


def _daily_series(report_range):
    params = {
        "start_at": report_range[
            "start_at"
        ],
        "end_at": report_range[
            "end_at"
        ],
    }

    use_months = (
        report_range["days"] > 62
    )

    if use_months:
        date_expression = (
            "DATE_FORMAT(created_at, '%Y-%m')"
        )
    else:
        date_expression = "DATE(created_at)"

    rows = (
        db.session.execute(
            text(
                f"""
                SELECT
                    {date_expression} AS period_key,
                    COUNT(*) AS bookings,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_status != 'refunded'
                                THEN paid_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS revenue

                FROM bookings

                WHERE created_at >= :start_at
                  AND created_at < :end_at

                GROUP BY period_key
                ORDER BY period_key ASC
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    values_by_period = {
        str(row["period_key"]): {
            "bookings": int(
                row["bookings"]
                or 0
            ),
            "revenue": float(
                row["revenue"]
                or 0
            ),
        }
        for row in rows
    }

    labels = []
    bookings = []
    revenue = []

    if use_months:
        cursor = report_range[
            "start_date"
        ].replace(day=1)

        final_month = report_range[
            "end_date"
        ].replace(day=1)

        while cursor <= final_month:
            key = cursor.strftime(
                "%Y-%m"
            )

            values = values_by_period.get(
                key,
                {
                    "bookings": 0,
                    "revenue": 0,
                },
            )

            labels.append(
                cursor.strftime(
                    "%b %Y"
                )
            )

            bookings.append(
                values["bookings"]
            )

            revenue.append(
                values["revenue"]
            )

            if cursor.month == 12:
                cursor = cursor.replace(
                    year=cursor.year + 1,
                    month=1,
                )
            else:
                cursor = cursor.replace(
                    month=cursor.month + 1
                )

    else:
        cursor = report_range[
            "start_date"
        ]

        while (
            cursor
            <= report_range["end_date"]
        ):
            key = cursor.isoformat()

            values = values_by_period.get(
                key,
                {
                    "bookings": 0,
                    "revenue": 0,
                },
            )

            labels.append(
                cursor.strftime(
                    "%d %b"
                )
            )

            bookings.append(
                values["bookings"]
            )

            revenue.append(
                values["revenue"]
            )

            cursor += timedelta(days=1)

    return {
        "labels": labels,
        "bookings": bookings,
        "revenue": revenue,
        "grouping": (
            "month"
            if use_months
            else "day"
        ),
    }


def _status_breakdown(report_range):
    params = {
        "start_at": report_range[
            "start_at"
        ],
        "end_at": report_range[
            "end_at"
        ],
    }

    rows = (
        db.session.execute(
            text(
                """
                SELECT
                    booking_status AS label,
                    COUNT(*) AS total

                FROM bookings

                WHERE created_at >= :start_at
                  AND created_at < :end_at

                GROUP BY booking_status
                ORDER BY total DESC
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    return [
        {
            "label": row["label"],
            "total": int(
                row["total"]
                or 0
            ),
        }
        for row in rows
    ]


def _payment_breakdown(report_range):
    params = {
        "start_at": report_range[
            "start_at"
        ],
        "end_at": report_range[
            "end_at"
        ],
    }

    rows = (
        db.session.execute(
            text(
                """
                SELECT
                    payment_method AS label,
                    COUNT(*) AS total,
                    COALESCE(
                        SUM(paid_amount),
                        0
                    ) AS amount

                FROM bookings

                WHERE created_at >= :start_at
                  AND created_at < :end_at
                  AND booking_status != 'cancelled'

                GROUP BY payment_method
                ORDER BY total DESC
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    return [
        {
            "label": row["label"],
            "total": int(
                row["total"]
                or 0
            ),
            "amount": float(
                row["amount"]
                or 0
            ),
        }
        for row in rows
    ]


def _top_tours(report_range):
    params = {
        "start_at": report_range[
            "start_at"
        ],
        "end_at": report_range[
            "end_at"
        ],
    }

    rows = (
        db.session.execute(
            text(
                """
                SELECT
                    tours.id,
                    COALESCE(
                        tours.title,
                        bookings.custom_tour_name,
                        'Custom Tour'
                    ) AS title,
                    COALESCE(
                        tours.destination,
                        bookings.custom_destination,
                        'Pakistan'
                    ) AS destination,
                    COUNT(bookings.id) AS booking_count,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN bookings.payment_status != 'refunded'
                                THEN bookings.paid_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS paid_revenue,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN bookings.booking_status != 'cancelled'
                                THEN bookings.total_travelers
                                ELSE 0
                            END
                        ),
                        0
                    ) AS travelers

                FROM bookings

                LEFT JOIN tours
                    ON tours.id = bookings.tour_id

                WHERE bookings.created_at >= :start_at
                  AND bookings.created_at < :end_at

                GROUP BY
                    tours.id,
                    COALESCE(
                        tours.title,
                        bookings.custom_tour_name,
                        'Custom Tour'
                    ),
                    COALESCE(
                        tours.destination,
                        bookings.custom_destination,
                        'Pakistan'
                    )

                ORDER BY
                    booking_count DESC,
                    paid_revenue DESC

                LIMIT 8
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "destination": (
                row["destination"]
                or "Not set"
            ),
            "booking_count": int(
                row["booking_count"]
                or 0
            ),
            "paid_revenue": float(
                row["paid_revenue"]
                or 0
            ),
            "travelers": int(
                row["travelers"]
                or 0
            ),
        }
        for row in rows
    ]


def _top_destinations(report_range):
    params = {
        "start_at": report_range[
            "start_at"
        ],
        "end_at": report_range[
            "end_at"
        ],
    }

    rows = (
        db.session.execute(
            text(
                """
                SELECT
                    COALESCE(
                        tours.destination,
                        bookings.custom_destination,
                        'Pakistan'
                    ) AS destination,
                    COUNT(bookings.id) AS booking_count,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN bookings.booking_status != 'cancelled'
                                THEN bookings.total_travelers
                                ELSE 0
                            END
                        ),
                        0
                    ) AS travelers

                FROM bookings

                LEFT JOIN tours
                    ON tours.id = bookings.tour_id

                WHERE bookings.created_at >= :start_at
                  AND bookings.created_at < :end_at

                GROUP BY COALESCE(
                    tours.destination,
                    bookings.custom_destination,
                    'Pakistan'
                )

                ORDER BY
                    booking_count DESC,
                    travelers DESC

                LIMIT 6
                """
            ),
            params,
        )
        .mappings()
        .all()
    )

    return [
        {
            "destination": (
                row["destination"]
                or "Not set"
            ),
            "booking_count": int(
                row["booking_count"]
                or 0
            ),
            "travelers": int(
                row["travelers"]
                or 0
            ),
        }
        for row in rows
    ]


def _upcoming_bookings():
    rows = (
        db.session.execute(
            text(
                """
                SELECT
                    bookings.id,
                    bookings.booking_number,
                    bookings.customer_name,
                    bookings.travel_date,
                    bookings.total_travelers,
                    bookings.total_amount,
                    bookings.booking_status,
                    COALESCE(
                        tours.title,
                        bookings.custom_tour_name,
                        'Custom Tour'
                    ) AS tour_title

                FROM bookings

                LEFT JOIN tours
                    ON tours.id = bookings.tour_id

                WHERE bookings.travel_date >= CURDATE()
                  AND bookings.booking_status
                      IN ('pending', 'confirmed')

                ORDER BY
                    bookings.travel_date ASC,
                    bookings.created_at ASC

                LIMIT 8
                """
            )
        )
        .mappings()
        .all()
    )

    return [
        {
            **dict(row),
            "total_amount": float(
                row["total_amount"]
                or 0
            ),
        }
        for row in rows
    ]


def build_admin_report(report_range):
    return {
        "summary": _summary_data(
            report_range
        ),
        "series": _daily_series(
            report_range
        ),
        "statuses": _status_breakdown(
            report_range
        ),
        "payments": _payment_breakdown(
            report_range
        ),
        "top_tours": _top_tours(
            report_range
        ),
        "top_destinations": (
            _top_destinations(
                report_range
            )
        ),
        "upcoming_bookings": (
            _upcoming_bookings()
        ),
    }


def _csv_response(rows, filename):
    output = io.StringIO(
        newline=""
    )

    writer = csv.writer(output)

    for row in rows:
        writer.writerow(row)

    data = output.getvalue()

    return data, filename


def bookings_csv(report_range):
    rows = [
        [
            "Booking Number",
            "Created At",
            "Customer",
            "Email",
            "Phone",
            "Tour",
            "Destination",
            "Travel Date",
            "Travelers",
            "Booking Status",
            "Payment Status",
            "Payment Method",
            "Total Amount",
        ]
    ]

    database_rows = (
        db.session.execute(
            text(
                """
                SELECT
                    bookings.booking_number,
                    bookings.created_at,
                    bookings.customer_name,
                    bookings.customer_email,
                    bookings.customer_phone,
                    COALESCE(
                        tours.title,
                        bookings.custom_tour_name,
                        'Custom Tour'
                    ) AS tour_title,
                    COALESCE(
                        tours.destination,
                        bookings.custom_destination,
                        'Pakistan'
                    ) AS destination,
                    bookings.travel_date,
                    bookings.total_travelers,
                    bookings.booking_status,
                    bookings.payment_status,
                    bookings.payment_method,
                    bookings.total_amount

                FROM bookings

                LEFT JOIN tours
                    ON tours.id = bookings.tour_id

                WHERE bookings.created_at >= :start_at
                  AND bookings.created_at < :end_at

                ORDER BY bookings.created_at DESC
                """
            ),
            {
                "start_at": report_range[
                    "start_at"
                ],
                "end_at": report_range[
                    "end_at"
                ],
            },
        )
        .mappings()
        .all()
    )

    for row in database_rows:
        rows.append(
            [
                row["booking_number"],
                row["created_at"],
                row["customer_name"],
                row["customer_email"],
                row["customer_phone"],
                row["tour_title"],
                row["destination"],
                row["travel_date"],
                row["total_travelers"],
                row["booking_status"],
                row["payment_status"],
                row["payment_method"],
                row["total_amount"],
            ]
        )

    return _csv_response(
        rows,
        (
            "capture-pakistan-bookings-"
            f"{report_range['start_date']}-"
            f"{report_range['end_date']}.csv"
        ),
    )


def customers_csv(report_range):
    rows = [
        [
            "Customer ID",
            "Name",
            "Email",
            "Phone",
            "Registered At",
            "Total Bookings",
            "Paid Revenue",
        ]
    ]

    database_rows = (
        db.session.execute(
            text(
                """
                SELECT
                    users.id,
                    users.name,
                    users.email,
                    users.phone,
                    users.created_at,
                    COUNT(bookings.id) AS total_bookings,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN bookings.payment_status != 'refunded'
                                THEN bookings.paid_amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS paid_revenue

                FROM users

                LEFT JOIN bookings
                    ON bookings.user_id = users.id

                WHERE users.role = 'customer'
                  AND users.created_at >= :start_at
                  AND users.created_at < :end_at

                GROUP BY
                    users.id,
                    users.name,
                    users.email,
                    users.phone,
                    users.created_at

                ORDER BY users.created_at DESC
                """
            ),
            {
                "start_at": report_range[
                    "start_at"
                ],
                "end_at": report_range[
                    "end_at"
                ],
            },
        )
        .mappings()
        .all()
    )

    for row in database_rows:
        rows.append(
            [
                row["id"],
                row["name"],
                row["email"],
                row["phone"],
                row["created_at"],
                row["total_bookings"],
                row["paid_revenue"],
            ]
        )

    return _csv_response(
        rows,
        (
            "capture-pakistan-customers-"
            f"{report_range['start_date']}-"
            f"{report_range['end_date']}.csv"
        ),
    )


def inquiries_csv(report_range):
    rows = [
        [
            "Source",
            "Reference",
            "Created At",
            "Customer",
            "Email",
            "Phone",
            "Destination / Tour",
            "Travelers",
            "Status",
            "Message",
        ]
    ]

    database_rows = (
        db.session.execute(
            text(
                """
                SELECT *
                FROM (
                    SELECT
                        'Homepage' AS source,
                        CONCAT(
                            'HOME-',
                            inquiries.id
                        ) AS reference_number,
                        inquiries.created_at,
                        inquiries.name AS customer_name,
                        '' AS customer_email,
                        inquiries.phone AS customer_phone,
                        inquiries.destination AS destination,
                        inquiries.travelers,
                        inquiries.status,
                        inquiries.message

                    FROM inquiries

                    WHERE inquiries.created_at >= :start_at
                      AND inquiries.created_at < :end_at

                    UNION ALL

                    SELECT
                        'Tour' AS source,
                        tour_inquiries.inquiry_number,
                        tour_inquiries.created_at,
                        tour_inquiries.customer_name,
                        tour_inquiries.customer_email,
                        tour_inquiries.customer_phone,
                        tours.title AS destination,
                        tour_inquiries.travelers,
                        tour_inquiries.inquiry_status,
                        tour_inquiries.message

                    FROM tour_inquiries

                    INNER JOIN tours
                        ON tours.id = tour_inquiries.tour_id

                    WHERE tour_inquiries.created_at >= :start_at
                      AND tour_inquiries.created_at < :end_at
                ) AS combined

                ORDER BY combined.created_at DESC
                """
            ),
            {
                "start_at": report_range[
                    "start_at"
                ],
                "end_at": report_range[
                    "end_at"
                ],
            },
        )
        .mappings()
        .all()
    )

    for row in database_rows:
        rows.append(
            [
                row["source"],
                row["reference_number"],
                row["created_at"],
                row["customer_name"],
                row["customer_email"],
                row["customer_phone"],
                row["destination"],
                row["travelers"],
                row["status"],
                row["message"],
            ]
        )

    return _csv_response(
        rows,
        (
            "capture-pakistan-inquiries-"
            f"{report_range['start_date']}-"
            f"{report_range['end_date']}.csv"
        ),
    )


def build_report_pdf(
    report_range,
    report_data,
):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import (
            ParagraphStyle,
            getSampleStyleSheet,
        )
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Image,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as error:
        raise RuntimeError(
            "ReportLab is not installed. Run: "
            "pip install 'reportlab>=4.2,<5'"
        ) from error

    output = io.BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Capture Pakistan Admin Report",
        author="Capture Pakistan",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(
            "#064A3D"
        ),
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor(
            "#667085"
        ),
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor(
            "#10221D"
        ),
        spaceBefore=12,
        spaceAfter=7,
    )

    right_style = ParagraphStyle(
        "Right",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontSize=8,
        textColor=colors.HexColor(
            "#667085"
        ),
    )

    story = []

    logo_path = (
        Path(current_app.static_folder)
        / "images"
        / "logo.png"
    )

    brand = []

    if logo_path.exists():
        logo = Image(
            str(logo_path),
            width=28 * mm,
            height=14 * mm,
        )
        brand.append(logo)
    else:
        brand.append(
            Paragraph(
                "<b>CAPTURE PAKISTAN</b>",
                title_style,
            )
        )

    brand.append(
        Paragraph(
            (
                "Generated "
                f"{datetime.now():%d %b %Y, %I:%M %p}"
            ),
            right_style,
        )
    )

    brand_table = Table(
        [brand],
        colWidths=[
            90 * mm,
            85 * mm,
        ],
    )

    brand_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
                ),
            ]
        )
    )

    story.append(brand_table)
    story.append(Spacer(1, 6 * mm))

    story.append(
        Paragraph(
            "Admin Performance Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            report_range["label"],
            subtitle_style,
        )
    )

    story.append(Spacer(1, 5 * mm))

    summary = report_data["summary"]

    cards = [
        [
            "Bookings",
            summary["total_bookings"],
            "Paid Revenue",
            (
                "PKR "
                f"{summary['paid_revenue']:,.0f}"
            ),
        ],
        [
            "Confirmed",
            summary["confirmed_bookings"],
            "Pending Payments",
            (
                "PKR "
                f"{summary['pending_payments']:,.0f}"
            ),
        ],
        [
            "New Customers",
            summary["new_customers"],
            "Inquiries",
            summary["total_inquiries"],
        ],
        [
            "Travelers",
            summary["travelers"],
            "Wishlist Saves",
            summary["wishlist_activity"],
        ],
    ]

    summary_table = Table(
        cards,
        colWidths=[
            36 * mm,
            47 * mm,
            42 * mm,
            50 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F3F8F6"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#10221D"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (3, 0),
                    (3, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#DDE9E4"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(summary_table)

    story.append(
        Paragraph(
            "Top Tours",
            section_style,
        )
    )

    tour_rows = [
        [
            "Tour",
            "Destination",
            "Bookings",
            "Travelers",
            "Paid Revenue",
        ]
    ]

    for tour in report_data[
        "top_tours"
    ]:
        tour_rows.append(
            [
                tour["title"],
                tour["destination"],
                tour["booking_count"],
                tour["travelers"],
                (
                    "PKR "
                    f"{tour['paid_revenue']:,.0f}"
                ),
            ]
        )

    if len(tour_rows) == 1:
        tour_rows.append(
            [
                "No booking data",
                "",
                "",
                "",
                "",
            ]
        )

    tour_table = Table(
        tour_rows,
        repeatRows=1,
        colWidths=[
            61 * mm,
            34 * mm,
            24 * mm,
            23 * mm,
            33 * mm,
        ],
    )

    tour_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#064A3D"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor(
                        "#DDE9E4"
                    ),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor(
                            "#F7FAF9"
                        ),
                    ],
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(tour_table)

    story.append(
        Paragraph(
            "Booking Status",
            section_style,
        )
    )

    status_rows = [
        [
            "Status",
            "Bookings",
        ]
    ]

    for status in report_data[
        "statuses"
    ]:
        status_rows.append(
            [
                status["label"].replace(
                    "_",
                    " ",
                ).title(),
                status["total"],
            ]
        )

    if len(status_rows) == 1:
        status_rows.append(
            [
                "No booking data",
                0,
            ]
        )

    status_table = Table(
        status_rows,
        colWidths=[
            90 * mm,
            40 * mm,
        ],
    )

    status_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#F7B733"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#10221D"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#DDE9E4"
                    ),
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(status_table)
    story.append(Spacer(1, 7 * mm))

    story.append(
        Paragraph(
            (
                "This report is generated from "
                "Capture Pakistan booking and inquiry records."
            ),
            subtitle_style,
        )
    )

    document.build(story)

    output.seek(0)

    return output.getvalue()
