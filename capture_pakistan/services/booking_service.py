import secrets

from datetime import date
from decimal import Decimal

from capture_pakistan.models import Booking


def generate_booking_number():
    while True:
        reference = (
            f"CP-{date.today():%Y%m%d}-"
            f"{secrets.token_hex(3).upper()}"
        )

        exists = Booking.query.filter_by(
            booking_number=reference
        ).first()

        if not exists:
            return reference


def calculate_booking_summary(
    tour,
    form_data,
):
    pricing_type = form_data.get(
        "pricing_type",
        "person",
    ).strip()

    quantity_raw = form_data.get(
        "quantity",
        "1",
    ).strip()

    children_raw = form_data.get(
        "children",
        "0",
    ).strip()

    travel_date_raw = form_data.get(
        "travel_date",
        "",
    ).strip()

    special_request = form_data.get(
        "special_request",
        "",
    ).strip()

    if pricing_type not in {
        "person",
        "couple",
    }:
        raise ValueError(
            "Please select a valid pricing option."
        )

    try:
        quantity = int(quantity_raw)
        children = int(children_raw)

        selected_date = date.fromisoformat(
            travel_date_raw
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "Please enter valid travelers and travel date."
        ) from error

    if quantity < 1 or quantity > 20:
        raise ValueError(
            "Please select between 1 and 20 adults or couples."
        )

    if children < 0 or children > 20:
        raise ValueError(
            "Please select between 0 and 20 children."
        )

    if selected_date < date.today():
        raise ValueError(
            "Please select today or a future travel date."
        )

    if pricing_type == "couple":
        if (
            not tour.couple_price
            or tour.couple_price <= 0
        ):
            raise ValueError(
                "Couple pricing is not available for this tour."
            )

        unit_price = Decimal(
            tour.couple_price
        )

        adults = quantity * 2

        quantity_label = (
            "Couple"
            if quantity == 1
            else "Couples"
        )

    else:
        unit_price = Decimal(
            tour.base_price or 0
        )

        adults = quantity

        quantity_label = (
            "Adult"
            if quantity == 1
            else "Adults"
        )

    child_unit_price = Decimal(
        tour.child_price or 0
    )

    total_amount = (
        unit_price * quantity
        + child_unit_price * children
    )

    return {
        "pricing_type": pricing_type,
        "quantity": quantity,
        "quantity_label": quantity_label,
        "adults": adults,
        "children": children,
        "total_travelers": (
            adults + children
        ),
        "travel_date": selected_date,
        "travel_date_raw": travel_date_raw,
        "unit_price": unit_price,
        "child_unit_price": child_unit_price,
        "total_amount": total_amount,
        "special_request": special_request,
    }
