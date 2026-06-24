from flask import Blueprint


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
)


# Import route modules after creating the blueprint.
from capture_pakistan.blueprints.admin import bookings
from capture_pakistan.blueprints.admin import categories
from capture_pakistan.blueprints.admin import dashboard
from capture_pakistan.blueprints.admin import email_notifications
from capture_pakistan.blueprints.admin import gallery
from capture_pakistan.blueprints.admin import inquiries
from capture_pakistan.blueprints.admin import invoice
from capture_pakistan.blueprints.admin import tours
from capture_pakistan.blueprints.admin import reports
from capture_pakistan.blueprints.admin import customers
from capture_pakistan.blueprints.admin import settings
from capture_pakistan.blueprints.admin import site_gallery
from capture_pakistan.blueprints.admin import reviews
