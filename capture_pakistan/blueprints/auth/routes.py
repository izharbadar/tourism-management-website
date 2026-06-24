from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from capture_pakistan.blueprints.auth import (
    auth_bp,
)

from capture_pakistan.extensions import db
from capture_pakistan.models import User

from capture_pakistan.services.helpers import (
    is_safe_redirect_target,
)




@auth_bp.route(
    "/register",
    methods=["GET", "POST"],
)
def register():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(
                url_for("admin.dashboard")
            )

        return redirect(
            url_for("customer.dashboard")
        )

    if request.method == "POST":
        name = request.form.get(
            "name",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        phone = request.form.get(
            "phone",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        confirm_password = request.form.get(
            "confirm_password",
            "",
        )

        if not name or not email or not phone:
            flash(
                "Please fill in all required fields.",
                "error",
            )

            return render_template(
                "register.html"
            )

        if len(name) < 2:
            flash(
                "Please enter your complete name.",
                "error",
            )

            return render_template(
                "register.html"
            )

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error",
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "error",
            )

            return render_template(
                "register.html"
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash(
                "An account with this email already exists.",
                "error",
            )

            return render_template(
                "register.html"
            )

        try:
            customer = User(
                name=name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(
                    password
                ),
                role="customer",
                is_active=True,
            )

            db.session.add(customer)
            db.session.commit()

            session.clear()

            login_user(customer)

            flash(
                (
                    "Welcome to Capture Pakistan, "
                    f"{customer.name}!"
                ),
                "success",
            )

            return redirect(
                url_for(
                    "customer.dashboard"
                )
            )

        except IntegrityError:
            db.session.rollback()

            flash(
                "This email address is already registered.",
                "error",
            )

        except SQLAlchemyError as error:
            db.session.rollback()

            print("Customer registration error:")
            print(error)

            flash(
                (
                    "Account could not be created. "
                    "Please try again."
                ),
                "error",
            )

    return render_template(
        "register.html"
    )


@auth_bp.route(
    "/login",
    methods=["GET", "POST"],
)
def login():
    next_url = (
        request.args.get(
            "next",
            "",
        ).strip()
        or request.form.get(
            "next",
            "",
        ).strip()
    )

    if current_user.is_authenticated:
        if is_safe_redirect_target(
            next_url
        ):
            return redirect(next_url)

        if current_user.role == "admin":
            return redirect(
                url_for("admin.dashboard")
            )

        return redirect(
            url_for("customer.dashboard")
        )

    if request.method == "POST":
        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        password = request.form.get(
            "password",
            "",
        )

        remember = (
            request.form.get("remember")
            == "on"
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if (
            user
            and user.is_active
            and check_password_hash(
                user.password_hash,
                password,
            )
        ):
            session.clear()

            login_user(
                user,
                remember=remember,
            )

            flash(
                f"Welcome back, {user.name}!",
                "success",
            )

            if is_safe_redirect_target(
                next_url
            ):
                return redirect(next_url)

            if user.role == "admin":
                return redirect(
                    url_for(
                        "admin.dashboard"
                    )
                )

            return redirect(
                url_for(
                    "customer.dashboard"
                )
            )

        flash(
            "Invalid email or password.",
            "error",
        )

    return render_template(
        "login.html",
        next_url=next_url,
    )


@auth_bp.route("/admin/login")
def old_admin_login():
    return redirect(
        url_for("auth.login")
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()

    flash(
        "You have been logged out successfully.",
        "success",
    )

    return redirect(
        url_for("auth.login")
    )
