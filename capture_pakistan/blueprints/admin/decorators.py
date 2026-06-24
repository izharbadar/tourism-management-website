from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def admin_required(view_function):
    """Allow only authenticated administrator accounts."""

    @wraps(view_function)
    @login_required
    def protected_view(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)

        return view_function(*args, **kwargs)

    return protected_view
