from flask import Blueprint
from middleware import jwt_required_custom
from controllers import (
    create_pothole,
    get_all_potholes,
    get_pothole_by_id,
    get_my_potholes,
    get_nearby_potholes,
    update_pothole,
    delete_pothole,
)

pothole_bp = Blueprint("potholes", __name__, url_prefix="/api/potholes")

# Order matters: specific paths before <pothole_id>
pothole_bp.get("/my")(jwt_required_custom(get_my_potholes))
pothole_bp.get("/nearby")(jwt_required_custom(get_nearby_potholes))

pothole_bp.post("/")(jwt_required_custom(create_pothole))
pothole_bp.get("/")(jwt_required_custom(get_all_potholes))
pothole_bp.get("/<pothole_id>")(jwt_required_custom(get_pothole_by_id))
pothole_bp.put("/<pothole_id>")(jwt_required_custom(update_pothole))
pothole_bp.delete("/<pothole_id>")(jwt_required_custom(delete_pothole))
