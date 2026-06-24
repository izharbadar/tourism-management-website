from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from flask import current_app
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as ReportLabImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from capture_pakistan.services.site_setting_service import (
    get_setting,
)


PILImage.MAX_IMAGE_PIXELS = 40_000_000


PRIMARY = colors.HexColor("#064F40")
PRIMARY_DARK = colors.HexColor("#043C31")
PRIMARY_LIGHT = colors.HexColor("#EAF5F1")
GOLD = colors.HexColor("#F7B733")
TEXT = colors.HexColor("#10221D")
MUTED = colors.HexColor("#667085")
BORDER = colors.HexColor("#DDE8E3")
LIGHT_BG = colors.HexColor("#F7FAF8")
DANGER = colors.HexColor("#B42318")
DANGER_BG = colors.HexColor("#FEE4E2")
SUCCESS = colors.HexColor("#067647")
SUCCESS_BG = colors.HexColor("#DCFAE6")
WARNING = colors.HexColor("#854D0E")
WARNING_BG = colors.HexColor("#FEF3C7")


def _safe(value):
    if value is None:
        return ""

    return escape(str(value))


def _money(value, currency):
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0

    return f"{currency} {amount:,.0f}"


def _label(value):
    return str(value or "").replace("_", " ").title()


def _payment_method(value):
    if value == "online_card":
        return "Online Card Payment"

    return "Cash on Pickup"


def _status_palette(value):
    value = str(value or "").lower()

    if value in {"paid", "confirmed", "completed"}:
        return SUCCESS, SUCCESS_BG

    if value in {"cancelled", "refunded"}:
        return DANGER, DANGER_BG

    return WARNING, WARNING_BG


def invoice_filename(booking):
    return (
        "capture-pakistan-"
        f"{booking.booking_number}.pdf"
    )


def _company_details():
    return {
        "name": get_setting(
            "invoice_company_name",
            current_app.config.get(
                "INVOICE_COMPANY_NAME",
                "Capture Pakistan",
            ),
        ),
        "email": get_setting(
            "invoice_company_email",
            current_app.config.get(
                "INVOICE_COMPANY_EMAIL",
                current_app.config.get(
                    "MAIL_DEFAULT_SENDER",
                    "",
                ),
            ),
        ),
        "phone": get_setting(
            "invoice_company_phone",
            current_app.config.get(
                "INVOICE_COMPANY_PHONE",
                "",
            ),
        ),
        "address": get_setting(
            "invoice_company_address",
            current_app.config.get(
                "INVOICE_COMPANY_ADDRESS",
                "Pakistan",
            ),
        ),
        "currency": get_setting(
            "currency_code",
            current_app.config.get(
                "INVOICE_CURRENCY",
                "PKR",
            ),
        ),
    }


def _logo_flowable():
    configured_logo = get_setting(
        "logo_path",
        "",
    ).strip()

    if configured_logo:
        logo_path = (
            Path(current_app.static_folder)
            / configured_logo
        )
    else:
        logo_path = (
            Path(current_app.static_folder)
            / "images"
            / "logo.png"
        )

    if not logo_path.exists():
        return None

    try:
        source = PILImage.open(
            logo_path
        ).convert("L")

        source.thumbnail(
            (900, 480),
            PILImage.Resampling.LANCZOS,
        )

        alpha = source.point(
            lambda pixel: (
                255
                if pixel >= 248
                else 0
            )
        )

        clean_logo = PILImage.new(
            "RGBA",
            source.size,
            (255, 255, 255, 0),
        )
        clean_logo.putalpha(alpha)

        image_buffer = BytesIO()
        clean_logo.save(
            image_buffer,
            format="PNG",
            optimize=True,
        )
        image_buffer.seek(0)

        logo = ReportLabImage(
            image_buffer
        )
        logo._restrictSize(
            43 * mm,
            18 * mm,
        )
        return logo

    except Exception:
        return None


def generate_booking_invoice_pdf(booking):
    company = _company_details()
    currency = company["currency"]

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=19 * mm,
        title=(
            "Capture Pakistan Booking Invoice "
            f"{booking.booking_number}"
        ),
        author=company["name"],
        subject="Tour booking invoice",
    )

    styles = getSampleStyleSheet()

    body = ParagraphStyle(
        "InvoiceBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.7,
        leading=12.5,
        textColor=TEXT,
    )

    small = ParagraphStyle(
        "InvoiceSmall",
        parent=body,
        fontSize=7.5,
        leading=10.5,
        textColor=MUTED,
    )

    white_small = ParagraphStyle(
        "InvoiceWhiteSmall",
        parent=small,
        textColor=colors.white,
    )

    white_title = ParagraphStyle(
        "InvoiceWhiteTitle",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=colors.white,
        alignment=TA_RIGHT,
    )

    section_title = ParagraphStyle(
        "InvoiceSection",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=PRIMARY,
        spaceAfter=5,
    )

    right_small = ParagraphStyle(
        "InvoiceRightSmall",
        parent=small,
        alignment=TA_RIGHT,
    )

    center_small = ParagraphStyle(
        "InvoiceCenterSmall",
        parent=small,
        alignment=TA_CENTER,
    )

    story = []

    logo = _logo_flowable()

    contact_lines = [
        f"<b>{_safe(company['name'])}</b>",
        _safe(company["address"]),
    ]

    if company["email"]:
        contact_lines.append(
            _safe(company["email"])
        )

    if company["phone"]:
        contact_lines.append(
            _safe(company["phone"])
        )

    company_paragraph = Paragraph(
        "<br/>".join(contact_lines),
        white_small,
    )

    if logo:
        brand_cell = Table(
            [[logo, company_paragraph]],
            colWidths=[46 * mm, 58 * mm],
        )
        brand_cell.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
    else:
        brand_cell = company_paragraph

    invoice_header = Paragraph(
        "BOOKING INVOICE"
        f"<br/><font size='8'>Reference: "
        f"{_safe(booking.booking_number)}</font>",
        white_title,
    )

    header = Table(
        [[brand_cell, invoice_header]],
        colWidths=[108 * mm, 72 * mm],
        rowHeights=[32 * mm],
    )

    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.8, PRIMARY_DARK),
            ]
        )
    )

    story.append(header)
    story.append(Spacer(1, 7 * mm))

    booking_color, booking_bg = _status_palette(
        booking.booking_status
    )

    payment_color, payment_bg = _status_palette(
        booking.payment_status
    )

    invoice_date = (
        getattr(
            booking,
            "invoice_date",
            None,
        )
        or (
            booking.created_at.date()
            if getattr(
                booking,
                "created_at",
                None,
            )
            else None
        )
    )

    created_text = (
        invoice_date.strftime("%d %B %Y")
        if invoice_date
        else "-"
    )

    status_table = Table(
        [
            [
                Paragraph(
                    f"<b>Booking Status</b><br/>"
                    f"{_safe(_label(booking.booking_status))}",
                    center_small,
                ),
                Paragraph(
                    f"<b>Payment Status</b><br/>"
                    f"{_safe(_label(booking.payment_status))}",
                    center_small,
                ),
                Paragraph(
                    f"<b>Invoice Date</b><br/>"
                    f"{_safe(created_text)}",
                    center_small,
                ),
            ]
        ],
        colWidths=[60 * mm, 60 * mm, 60 * mm],
    )

    status_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), booking_bg),
                ("TEXTCOLOR", (0, 0), (0, 0), booking_color),
                ("BACKGROUND", (1, 0), (1, 0), payment_bg),
                ("TEXTCOLOR", (1, 0), (1, 0), payment_color),
                ("BACKGROUND", (2, 0), (2, 0), LIGHT_BG),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(status_table)
    story.append(Spacer(1, 7 * mm))

    customer_block = [
        Paragraph("CUSTOMER DETAILS", section_title),
        Table(
            [
                [
                    Paragraph("Full Name", small),
                    Paragraph(_safe(booking.customer_name), body),
                    Paragraph("Email", small),
                    Paragraph(_safe(booking.customer_email), body),
                ],
                [
                    Paragraph("Phone / WhatsApp", small),
                    Paragraph(
                        _safe(
                            booking.customer_phone
                            or "Not provided"
                        ),
                        body,
                    ),
                    Paragraph("Booking Reference", small),
                    Paragraph(_safe(booking.booking_number), body),
                ],
            ],
            colWidths=[31 * mm, 59 * mm, 31 * mm, 59 * mm],
        ),
    ]

    customer_block[1].setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PRIMARY_LIGHT),
                ("BACKGROUND", (2, 0), (2, -1), PRIMARY_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(KeepTogether(customer_block))
    story.append(Spacer(1, 7 * mm))

    tour_details = Table(
        [
            [
                Paragraph("Tour", small),
                Paragraph(_safe(booking.tour_name), body),
                Paragraph("Destination", small),
                Paragraph(
                    _safe(
                        booking.tour_destination
                    ),
                    body,
                ),
            ],
            [
                Paragraph("Travel Date", small),
                Paragraph(
                    _safe(
                        booking.travel_date.strftime(
                            "%d %B %Y"
                        )
                    ),
                    body,
                ),
                Paragraph("Total Travelers", small),
                Paragraph(
                    _safe(booking.total_travelers),
                    body,
                ),
            ],
            [
                Paragraph("Adults", small),
                Paragraph(_safe(booking.adults), body),
                Paragraph("Children", small),
                Paragraph(_safe(booking.children), body),
            ],
            [
                Paragraph("Pricing Option", small),
                Paragraph(
                    _safe(
                        "Couple Package"
                        if booking.pricing_type
                        == "couple"
                        else "Per Person"
                    ),
                    body,
                ),
                Paragraph("Payment Method", small),
                Paragraph(
                    _safe(
                        _payment_method(
                            booking
                        )
                    ),
                    body,
                ),
            ],
        ],
        colWidths=[31 * mm, 59 * mm, 31 * mm, 59 * mm],
    )

    tour_details.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), PRIMARY_LIGHT),
                ("BACKGROUND", (2, 0), (2, -1), PRIMARY_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(
        KeepTogether(
            [
                Paragraph("TOUR DETAILS", section_title),
                tour_details,
            ]
        )
    )
    story.append(Spacer(1, 7 * mm))

    pricing_description = (
        "Couple Package"
        if booking.pricing_type == "couple"
        else "Adult / Per Person Package"
    )

    pricing_rows = [
        [
            Paragraph("Description", small),
            Paragraph("Quantity", small),
            Paragraph("Unit Price", right_small),
            Paragraph("Amount", right_small),
        ],
        [
            Paragraph(_safe(pricing_description), body),
            Paragraph(_safe(booking.package_quantity), body),
            Paragraph(
                _safe(
                    _money(
                        booking.unit_price,
                        currency,
                    )
                ),
                right_small,
            ),
            Paragraph(
                _safe(
                    _money(
                        float(booking.unit_price or 0)
                        * int(
                            booking.package_quantity
                            or 0
                        ),
                        currency,
                    )
                ),
                right_small,
            ),
        ],
    ]

    if int(booking.children or 0) > 0:
        pricing_rows.append(
            [
                Paragraph("Children", body),
                Paragraph(_safe(booking.children), body),
                Paragraph(
                    _safe(
                        _money(
                            booking.child_unit_price,
                            currency,
                        )
                    ),
                    right_small,
                ),
                Paragraph(
                    _safe(
                        _money(
                            float(
                                booking.child_unit_price
                                or 0
                            )
                            * int(
                                booking.children
                                or 0
                            ),
                            currency,
                        )
                    ),
                    right_small,
                ),
            ]
        )

    pricing_rows.append(
        [
            "",
            "",
            Paragraph("TOTAL", right_small),
            Paragraph(
                f"<b>{_safe(_money(booking.total_amount, currency))}</b>",
                right_small,
            ),
        ]
    )

    pricing_rows.append(
        [
            "",
            "",
            Paragraph("PAID / ADVANCE", right_small),
            Paragraph(
                f"<b>{_safe(_money(booking.paid_amount, currency))}</b>",
                right_small,
            ),
        ]
    )

    pricing_rows.append(
        [
            "",
            "",
            Paragraph("BALANCE DUE", right_small),
            Paragraph(
                f"<b>{_safe(_money(booking.balance_amount, currency))}</b>",
                right_small,
            ),
        ]
    )

    pricing_table = Table(
        pricing_rows,
        colWidths=[78 * mm, 26 * mm, 38 * mm, 38 * mm],
        repeatRows=1,
    )

    last_row = len(pricing_rows) - 1
    summary_start_row = max(
        last_row - 2,
        1,
    )

    pricing_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -2), 0.4, BORDER),
                ("BACKGROUND", (2, summary_start_row), (-1, last_row), PRIMARY_LIGHT),
                ("SPAN", (0, summary_start_row), (1, summary_start_row)),
                ("SPAN", (0, summary_start_row + 1), (1, summary_start_row + 1)),
                ("SPAN", (0, last_row), (1, last_row)),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(
        KeepTogether(
            [
                Paragraph("PAYMENT SUMMARY", section_title),
                pricing_table,
            ]
        )
    )

    if booking.special_request:
        story.append(Spacer(1, 7 * mm))
        story.append(
            KeepTogether(
                [
                    Paragraph("SPECIAL REQUEST", section_title),
                    Table(
                        [
                            [
                                Paragraph(
                                    _safe(
                                        booking.special_request
                                    ),
                                    body,
                                )
                            ]
                        ],
                        colWidths=[180 * mm],
                        style=TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                ("TOPPADDING", (0, 0), (-1, -1), 8),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ]
                        ),
                    ),
                ]
            )
        )

    story.append(Spacer(1, 7 * mm))

    notice_text = (
        "This invoice confirms that Capture Pakistan has received "
        "the booking request. It is not proof of payment unless the "
        "payment status above is marked Paid. Final pickup, hotel, "
        "transport and payment arrangements are confirmed separately "
        "by the Capture Pakistan team."
    )

    notice = Table(
        [[Paragraph(notice_text, small)]],
        colWidths=[180 * mm],
    )

    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF8E7")),
                ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(notice)

    footer_text = (
        f"{company['name']} | "
        f"{company['email'] or 'capturepakistan.com'}"
    )

    def draw_footer(canvas, doc):
        canvas.saveState()
        width, _ = A4
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(
            15 * mm,
            12 * mm,
            width - 15 * mm,
            12 * mm,
        )
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(
            15 * mm,
            7.5 * mm,
            footer_text,
        )
        canvas.drawRightString(
            width - 15 * mm,
            7.5 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    return buffer.getvalue()
