from io import BytesIO

from flask import (
    flash,
    redirect,
    send_file,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
)

from capture_pakistan.blueprints.customer import (
    customer_bp,
)

from capture_pakistan.models import Booking

from capture_pakistan.services.invoice_service import (
    generate_booking_invoice_pdf,
    invoice_filename,
)


@customer_bp.route(
    "/dashboard/bookings/"
    "<string:booking_number>/invoice"
)
@login_required
def booking_invoice(booking_number):
    booking = Booking.query.filter_by(
        booking_number=booking_number,
        user_id=current_user.id,
    ).first_or_404()

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
        print("Customer invoice error:")
        print(error)

        flash(
            "Your invoice could not be generated.",
            "error",
        )

        return redirect(
            url_for(
                "customer.booking_detail",
                booking_number=(
                    booking.booking_number
                ),
            )
        )
