import math

from datetime import date

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.admin import (
    admin_bp,
)
from capture_pakistan.blueprints.admin.decorators import (
    admin_required,
)
from capture_pakistan.extensions import db
from capture_pakistan.models import (
    Booking,
    TourInquiry,
    User,
)


VALID_CUSTOMER_STATUSES = {
    "active",
    "inactive",
}

VALID_CUSTOMER_SORTS = {
    "newest",
    "oldest",
    "name",
    "bookings",
    "revenue",
}


def _customer_aggregate_columns():
    booking_count = (
        select(
            func.count(Booking.id)
        )
        .where(
            Booking.user_id == User.id
        )
        .correlate(User)
        .scalar_subquery()
    )

    paid_revenue = (
        select(
            func.coalesce(
                func.sum(
                    Booking.total_amount
                ),
                0,
            )
        )
        .where(
            Booking.user_id == User.id,
            Booking.payment_status == "paid",
        )
        .correlate(User)
        .scalar_subquery()
    )

    inquiry_count = (
        select(
            func.count(TourInquiry.id)
        )
        .where(
            TourInquiry.user_id == User.id
        )
        .correlate(User)
        .scalar_subquery()
    )

    return (
        booking_count,
        paid_revenue,
        inquiry_count,
    )


@admin_bp.route("/customers")
@admin_required
def customers():
    search = request.args.get(
        "search",
        "",
    ).strip()

    status_filter = request.args.get(
        "status",
        "",
    ).strip().lower()

    sort_by = request.args.get(
        "sort",
        "newest",
    ).strip().lower()

    page = request.args.get(
        "page",
        1,
        type=int,
    )

    if page < 1:
        page = 1

    if (
        status_filter
        not in VALID_CUSTOMER_STATUSES
    ):
        status_filter = ""

    if sort_by not in VALID_CUSTOMER_SORTS:
        sort_by = "newest"

    filters = [
        User.role == "customer",
    ]

    if status_filter == "active":
        filters.append(
            User.is_active.is_(True)
        )

    elif status_filter == "inactive":
        filters.append(
            User.is_active.is_(False)
        )

    if search:
        search_term = f"%{search}%"

        filters.append(
            or_(
                User.name.ilike(
                    search_term
                ),
                User.email.ilike(
                    search_term
                ),
                User.phone.ilike(
                    search_term
                ),
            )
        )

    (
        booking_count,
        paid_revenue,
        inquiry_count,
    ) = _customer_aggregate_columns()

    query = (
        db.session.query(
            User,
            booking_count.label(
                "booking_count"
            ),
            paid_revenue.label(
                "paid_revenue"
            ),
            inquiry_count.label(
                "inquiry_count"
            ),
        )
        .filter(*filters)
    )

    if sort_by == "oldest":
        query = query.order_by(
            User.created_at.asc()
        )

    elif sort_by == "name":
        query = query.order_by(
            User.name.asc()
        )

    elif sort_by == "bookings":
        query = query.order_by(
            booking_count.desc(),
            User.created_at.desc(),
        )

    elif sort_by == "revenue":
        query = query.order_by(
            paid_revenue.desc(),
            User.created_at.desc(),
        )

    else:
        query = query.order_by(
            User.created_at.desc()
        )

    per_page = 20

    total_customers = (
        User.query.filter(
            *filters
        ).count()
    )

    total_pages = max(
        1,
        math.ceil(
            total_customers / per_page
        ),
    )

    if page > total_pages:
        page = total_pages

    rows = (
        query.limit(per_page)
        .offset(
            (page - 1) * per_page
        )
        .all()
    )

    customer_rows = [
        {
            "customer": customer,
            "booking_count": int(
                booking_total or 0
            ),
            "paid_revenue": float(
                revenue_total or 0
            ),
            "inquiry_count": int(
                inquiry_total or 0
            ),
        }
        for (
            customer,
            booking_total,
            revenue_total,
            inquiry_total,
        ) in rows
    ]

    month_start = date.today().replace(
        day=1
    )

    customer_stats = {
        "total": (
            User.query.filter_by(
                role="customer"
            ).count()
        ),
        "active": (
            User.query.filter_by(
                role="customer",
                is_active=True,
            ).count()
        ),
        "inactive": (
            User.query.filter_by(
                role="customer",
                is_active=False,
            ).count()
        ),
        "new_this_month": (
            User.query.filter(
                User.role == "customer",
                User.created_at
                >= month_start,
            ).count()
        ),
    }

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total_customers,
        "pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "previous_page": page - 1,
        "next_page": page + 1,
    }

    return render_template(
        "admin/customers.html",
        customers=customer_rows,
        customer_stats=customer_stats,
        pagination=pagination,
        search=search,
        selected_status=status_filter,
        selected_sort=sort_by,
    )


@admin_bp.route(
    "/customers/<int:customer_id>"
)
@admin_required
def customer_detail(customer_id):
    customer = User.query.filter_by(
        id=customer_id,
        role="customer",
    ).first()

    if not customer:
        abort(404)

    customer_bookings = (
        Booking.query.filter_by(
            user_id=customer.id
        )
        .order_by(
            Booking.created_at.desc()
        )
        .all()
    )

    customer_inquiries = (
        TourInquiry.query.filter_by(
            user_id=customer.id
        )
        .order_by(
            TourInquiry.created_at.desc()
        )
        .all()
    )

    total_paid = (
        db.session.query(
            func.coalesce(
                func.sum(
                    Booking.total_amount
                ),
                0,
            )
        )
        .filter(
            Booking.user_id
            == customer.id,
            Booking.payment_status
            == "paid",
        )
        .scalar()
        or 0
    )

    upcoming_bookings = (
        Booking.query.filter(
            Booking.user_id
            == customer.id,
            Booking.travel_date
            >= date.today(),
            Booking.booking_status.in_(
                [
                    "pending",
                    "confirmed",
                ]
            ),
        ).count()
    )

    customer_stats = {
        "total_bookings": len(
            customer_bookings
        ),
        "upcoming_bookings": (
            upcoming_bookings
        ),
        "total_inquiries": len(
            customer_inquiries
        ),
        "paid_revenue": float(
            total_paid
        ),
    }

    return render_template(
        "admin/customer_detail.html",
        customer=customer,
        customer_bookings=customer_bookings,
        customer_inquiries=customer_inquiries,
        customer_stats=customer_stats,
    )


@admin_bp.route(
    "/customers/<int:customer_id>/status",
    methods=["POST"],
)
@admin_required
def update_customer_status(customer_id):
    customer = User.query.filter_by(
        id=customer_id,
        role="customer",
    ).first()

    if not customer:
        abort(404)

    action = request.form.get(
        "action",
        "",
    ).strip().lower()

    if action not in {
        "activate",
        "deactivate",
    }:
        flash(
            "Invalid customer status action.",
            "error",
        )

        return redirect(
            url_for(
                "admin.customer_detail",
                customer_id=customer.id,
            )
        )

    try:
        customer.is_active = (
            action == "activate"
        )

        db.session.commit()

        if customer.is_active:
            message = (
                "Customer account activated successfully."
            )
        else:
            message = (
                "Customer account deactivated successfully."
            )

        flash(
            message,
            "success",
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print(
            "Customer status update error:"
        )
        print(error)

        flash(
            "Customer status could not be updated.",
            "error",
        )

    return redirect(
        url_for(
            "admin.customer_detail",
            customer_id=customer.id,
        )
    )
