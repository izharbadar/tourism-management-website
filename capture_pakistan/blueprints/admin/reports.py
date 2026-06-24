from urllib.parse import urlencode

from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import (
    admin_bp,
)

from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)

from capture_pakistan.services.report_service import (
    bookings_csv,
    build_admin_report,
    build_report_pdf,
    customers_csv,
    inquiries_csv,
    resolve_report_range,
)


def _filter_query(report_range):
    return urlencode(
        {
            "range": report_range[
                "preset"
            ],
            "start_date": report_range[
                "start_date"
            ].isoformat(),
            "end_date": report_range[
                "end_date"
            ].isoformat(),
        }
    )


def _csv_download(data, filename):
    return Response(
        data,
        mimetype=(
            "text/csv; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


@admin_bp.route("/reports")
@admin_required
def reports():
    report_range = (
        resolve_report_range(
            request.args
        )
    )

    try:
        report_data = (
            build_admin_report(
                report_range
            )
        )

    except SQLAlchemyError as error:
        print("Admin reports error:")
        print(error)

        flash(
            "Reports could not be loaded.",
            "error",
        )

        report_data = {
            "summary": {
                "total_bookings": 0,
                "pending_bookings": 0,
                "confirmed_bookings": 0,
                "cancelled_bookings": 0,
                "completed_bookings": 0,
                "paid_revenue": 0,
                "pending_payments": 0,
                "booking_value": 0,
                "travelers": 0,
                "new_customers": 0,
                "total_inquiries": 0,
                "new_inquiries": 0,
                "converted_inquiries": 0,
                "inquiry_conversion_rate": 0,
                "wishlist_activity": 0,
                "wishlist_users": 0,
                "wishlist_tours": 0,
                "average_booking_value": 0,
            },
            "series": {
                "labels": [],
                "bookings": [],
                "revenue": [],
                "grouping": "day",
            },
            "statuses": [],
            "payments": [],
            "top_tours": [],
            "top_destinations": [],
            "upcoming_bookings": [],
        }

    return render_template(
        "admin/reports.html",
        report_range=report_range,
        report_data=report_data,
        filter_query=_filter_query(
            report_range
        ),
    )


@admin_bp.route(
    "/reports/export/bookings.csv"
)
@admin_required
def export_bookings_csv():
    report_range = (
        resolve_report_range(
            request.args
        )
    )

    data, filename = bookings_csv(
        report_range
    )

    return _csv_download(
        data,
        filename,
    )


@admin_bp.route(
    "/reports/export/customers.csv"
)
@admin_required
def export_customers_csv():
    report_range = (
        resolve_report_range(
            request.args
        )
    )

    data, filename = customers_csv(
        report_range
    )

    return _csv_download(
        data,
        filename,
    )


@admin_bp.route(
    "/reports/export/inquiries.csv"
)
@admin_required
def export_inquiries_csv():
    report_range = (
        resolve_report_range(
            request.args
        )
    )

    data, filename = inquiries_csv(
        report_range
    )

    return _csv_download(
        data,
        filename,
    )


@admin_bp.route(
    "/reports/export/summary.pdf"
)
@admin_required
def export_report_pdf():
    report_range = (
        resolve_report_range(
            request.args
        )
    )

    try:
        report_data = (
            build_admin_report(
                report_range
            )
        )

        pdf_bytes = build_report_pdf(
            report_range,
            report_data,
        )

    except RuntimeError as error:
        flash(
            str(error),
            "error",
        )

        return redirect(
            url_for(
                "admin.reports",
                **{
                    "range": report_range[
                        "preset"
                    ],
                    "start_date": report_range[
                        "start_date"
                    ].isoformat(),
                    "end_date": report_range[
                        "end_date"
                    ].isoformat(),
                },
            )
        )

    except SQLAlchemyError as error:
        print("Admin report PDF error:")
        print(error)

        flash(
            "The report PDF could not be generated.",
            "error",
        )

        return redirect(
            url_for("admin.reports")
        )

    filename = (
        "capture-pakistan-report-"
        f"{report_range['start_date']}-"
        f"{report_range['end_date']}.pdf"
    )

    from io import BytesIO

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )
