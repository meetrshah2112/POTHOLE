from flask import Blueprint
from middleware import admin_required
from controllers import (
    admin_get_all_potholes,
    admin_update_status,
    admin_update_priority,
    admin_delete_pothole,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

admin_bp.get("/potholes")(admin_required(admin_get_all_potholes))
admin_bp.patch("/potholes/<pothole_id>/status")(admin_required(admin_update_status))
admin_bp.patch("/potholes/<pothole_id>/priority")(admin_required(admin_update_priority))
admin_bp.delete("/potholes/<pothole_id>")(admin_required(admin_delete_pothole))
