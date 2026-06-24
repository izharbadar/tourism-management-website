from flask import Blueprint


customer_bp = Blueprint(
    "customer",
    __name__,
)


from capture_pakistan.blueprints.customer import routes
from capture_pakistan.blueprints.customer import profile
from capture_pakistan.blueprints.customer import invoice
from capture_pakistan.blueprints.customer import wishlist
from capture_pakistan.blueprints.customer import reviews
