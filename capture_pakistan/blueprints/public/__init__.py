from flask import Blueprint


public_bp = Blueprint(
    "public",
    __name__,
)


from capture_pakistan.blueprints.public import routes
from capture_pakistan.blueprints.public import live_search
from capture_pakistan.blueprints.public import extra_pages
from capture_pakistan.blueprints.public import seo_routes
