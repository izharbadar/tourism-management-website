from io import BytesIO

from flask import (
    abort,
    flash,
    redirect,
    send_file,
    url_for,
)

from capture_pakistan.blueprints.admin import (
    admin_bp,
)

from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)

from capture_pakistan.extensions import db
from capture_pakistan.models import Booking

from capture_pakistan.services.invoice_service import (
    generate_booking_invoice_pdf,
    invoice_filename,
)


@admin_bp.route(
    "/bookings/<int:booking_id>/invoice"
)
@admin_required
def booking_invoice(booking_id):
    booking = db.session.get(
        Booking,
        booking_id,
    )

    if not booking:
        abort(404)

    try:
        pdf_bytes = (
            generate_booking_invoice_pdf(
                booking
            )
        )

        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=(
                invoice_filename(booking)
            ),
            max_age=0,
        )

    except Exception as error:
        print("Admin invoice error:")
        print(error)

        flash(
            "The booking invoice could not be generated.",
            "error",
        )

        return redirect(
            url_for(
                "admin.booking_detail",
                booking_id=booking.id,
            )
        )
