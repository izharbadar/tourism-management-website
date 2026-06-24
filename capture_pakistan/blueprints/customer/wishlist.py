from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
)

from sqlalchemy.exc import SQLAlchemyError

from capture_pakistan.blueprints.customer import (
    customer_bp,
)

from capture_pakistan.extensions import db

from capture_pakistan.models import (
    Tour,
    Wishlist,
)

from capture_pakistan.services.helpers import (
    is_safe_redirect_target,
)


def _is_ajax_request():
    return (
        request.headers.get(
            "X-Requested-With"
        )
        == "XMLHttpRequest"
        or request.accept_mimetypes.best
        == "application/json"
    )


def _redirect_target(tour):
    requested_target = request.form.get(
        "next",
        "",
    ).strip()

    if is_safe_redirect_target(
        requested_target
    ):
        return requested_target

    if is_safe_redirect_target(
        request.referrer
    ):
        return request.referrer

    return url_for(
        "public.tour_detail",
        slug=tour.slug,
    )


@customer_bp.route("/dashboard/wishlist")
@login_required
def wishlist():
    if current_user.role == "admin":
        return redirect(
            url_for("admin.dashboard")
        )

    wishlist_items = (
        Wishlist.query
        .join(
            Tour,
            Tour.id == Wishlist.tour_id,
        )
        .filter(
            Wishlist.user_id
            == current_user.id,
            Tour.status == "published",
        )
        .order_by(
            Wishlist.created_at.desc()
        )
        .all()
    )

    return render_template(
        "customer/wishlist.html",
        wishlist_items=wishlist_items,
    )


@customer_bp.route(
    "/tours/<int:tour_id>/wishlist/toggle",
    methods=["POST"],
)
def toggle_wishlist(tour_id):
    tour = Tour.query.filter_by(
        id=tour_id,
        status="published",
    ).first_or_404()

    redirect_target = _redirect_target(
        tour
    )

    if not current_user.is_authenticated:
        login_url = url_for(
            "auth.login",
            next=redirect_target,
        )

        if _is_ajax_request():
            return jsonify(
                {
                    "ok": False,
                    "authentication_required": True,
                    "login_url": login_url,
                }
            ), 401

        return redirect(login_url)

    if current_user.role != "customer":
        message = (
            "Wishlist is available for "
            "customer accounts only."
        )

        if _is_ajax_request():
            return jsonify(
                {
                    "ok": False,
                    "message": message,
                }
            ), 403

        flash(message, "error")
        return redirect(redirect_target)

    existing_item = Wishlist.query.filter_by(
        user_id=current_user.id,
        tour_id=tour.id,
    ).first()

    try:
        if existing_item:
            db.session.delete(existing_item)
            saved = False
            message = (
                "Tour removed from your wishlist."
            )

        else:
            db.session.add(
                Wishlist(
                    user_id=current_user.id,
                    tour_id=tour.id,
                )
            )

            saved = True
            message = (
                "Tour saved to your wishlist."
            )

        db.session.commit()

        wishlist_count = (
            Wishlist.query.filter_by(
                user_id=current_user.id
            ).count()
        )

    except SQLAlchemyError as error:
        db.session.rollback()

        print("Wishlist update error:")
        print(error)

        message = (
            "Wishlist could not be updated. "
            "Please try again."
        )

        if _is_ajax_request():
            return jsonify(
                {
                    "ok": False,
                    "message": message,
                }
            ), 500

        flash(message, "error")
        return redirect(redirect_target)

    if _is_ajax_request():
        return jsonify(
            {
                "ok": True,
                "saved": saved,
                "tour_id": tour.id,
                "wishlist_count": (
                    wishlist_count
                ),
                "message": message,
            }
        )

    flash(message, "success")
    return redirect(redirect_target)
