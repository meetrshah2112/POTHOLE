from .auth_controller import register, login
from .pothole_controller import (
    create_pothole,
    get_all_potholes,
    get_pothole_by_id,
    get_my_potholes,
    get_nearby_potholes,
    update_pothole,
    delete_pothole,
)
from .admin_controller import (
    admin_get_all_potholes,
    admin_update_status,
    admin_update_priority,
    admin_delete_pothole,
)

__all__ = [
    "register", "login",
    "create_pothole", "get_all_potholes", "get_pothole_by_id",
    "get_my_potholes", "get_nearby_potholes",
    "update_pothole", "delete_pothole",
    "admin_get_all_potholes", "admin_update_status",
    "admin_update_priority", "admin_delete_pothole",
]
