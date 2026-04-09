from flask import Blueprint
from controllers import register, login

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

auth_bp.post("/register")(register)
auth_bp.post("/login")(login)
