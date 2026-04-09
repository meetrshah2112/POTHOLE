from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from utils.responses import error_response


def jwt_required_custom(fn):
    """Require a valid JWT. Injects current_user_id into flask.g."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            g.current_user_id = get_jwt_identity()
            g.current_user_role = get_jwt().get("role", "user")
        except Exception as e:
            return error_response(f"Unauthorized: {str(e)}", 401)
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    """Require a valid JWT AND admin role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != "admin":
                return error_response("Forbidden: Admin access required.", 403)
            g.current_user_id = get_jwt_identity()
            g.current_user_role = "admin"
        except Exception as e:
            return error_response(f"Unauthorized: {str(e)}", 401)
        return fn(*args, **kwargs)
    return wrapper
