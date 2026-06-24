from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

csrf = CSRFProtect()

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)

login_manager = LoginManager()

login_manager.login_view = "auth.login"

login_manager.login_message = (
    "Please login to continue."
)

login_manager.login_message_category = "error"