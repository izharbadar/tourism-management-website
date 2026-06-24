from flask import abort, flash, redirect, render_template, request, url_for
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import admin_bp
from capture_pakistan.blueprints.admin.decorators import admin_required
from capture_pakistan.extensions import db
from capture_pakistan.models import Tour, TourInquiry

from capture_pakistan.services.email_service import (
    send_inquiry_status_notification,
)


VALID_INQUIRY_STATUSES = {
    "new",
    "contacted",
    "quotation_sent",
    "converted",
    "closed",
}

VALID_INQUIRY_TYPES = {
    "general",
    "private_tour",
    "customized_tour",
    "group_tour",
    "price_quotation",
}


@admin_bp.route("/inquiries")
@admin_required
def inquiries():
    status_filter = request.args.get("status", "").strip()
    type_filter = request.args.get("type", "").strip()
    search = request.args.get("search", "").strip()

    query = TourInquiry.query

    if status_filter in VALID_INQUIRY_STATUSES:
        query = query.filter(
            TourInquiry.inquiry_status == status_filter
        )

    if type_filter in VALID_INQUIRY_TYPES:
        query = query.filter(
            TourInquiry.inquiry_type == type_filter
        )

    if search:
        search_term = f"%{search}%"
        query = query.join(Tour).filter(
            or_(
                TourInquiry.inquiry_number.ilike(search_term),
                TourInquiry.customer_name.ilike(search_term),
                TourInquiry.customer_email.ilike(search_term),
                TourInquiry.customer_phone.ilike(search_term),
                Tour.title.ilike(search_term),
            )
        )

    inquiry_rows = query.order_by(
        TourInquiry.created_at.desc()
    ).all()

    return render_template(
        "admin/inquiries.html",
        inquiries=inquiry_rows,
        selected_status=status_filter,
        selected_type=type_filter,
        search=search,
    )


@admin_bp.route("/inquiries/<int:inquiry_id>")
@admin_required
def inquiry_detail(inquiry_id):
    inquiry = db.session.get(TourInquiry, inquiry_id)

    if not inquiry:
        abort(404)

    return render_template(
        "admin/inquiry_detail.html",
        inquiry=inquiry,
    )


@admin_bp.route(
    "/inquiries/<int:inquiry_id>/update",
    methods=["POST"],
)
@admin_required
def update_inquiry(inquiry_id):
    inquiry = db.session.get(TourInquiry, inquiry_id)

    if not inquiry:
        abort(404)

    inquiry_status = request.form.get(
        "inquiry_status",
        inquiry.inquiry_status,
    ).strip()

    admin_notes = request.form.get("admin_notes", "").strip()

    if inquiry_status not in VALID_INQUIRY_STATUSES:
        flash("Invalid inquiry status.", "error")
        return redirect(
            url_for("admin.inquiry_detail", inquiry_id=inquiry.id)
        )

    previous_status = inquiry.inquiry_status

    try:
        inquiry.inquiry_status = inquiry_status
        inquiry.admin_notes = admin_notes or None
        db.session.commit()

        if previous_status != inquiry.inquiry_status:
            send_inquiry_status_notification(
                inquiry,
                previous_status=previous_status,
            )

        flash("Inquiry updated successfully.", "success")

    except SQLAlchemyError as error:
        db.session.rollback()
        print("Inquiry update error:")
        print(error)
        flash("Inquiry could not be updated.", "error")

    return redirect(
        url_for("admin.inquiry_detail", inquiry_id=inquiry.id)
    )
