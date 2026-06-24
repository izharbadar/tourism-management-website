from flask import Blueprint


auth_bp = Blueprint(
    "auth",
    __name__,
)


# Routes ko blueprint ke saath register karta hai
from capture_pakistan.blueprints.auth import routes