import logging
from flask import request, g
from marshmallow import ValidationError

from models import PotholeModel
from config import DatabaseConfig
from utils import (
    CreatePotholeSchema, UpdatePotholeSchema, NearbySchema,
    success_response, error_response, paginated_response,
    upload_image, is_cloudinary_configured,
)

logger = logging.getLogger(__name__)
create_schema = CreatePotholeSchema()
update_schema = UpdatePotholeSchema()
nearby_schema = NearbySchema()


def _get_pagination():
    """Parse page & limit from query string with safe defaults."""
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(50, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        page, limit = 1, 10
    return page, limit


# ─── CREATE ───────────────────────────────────────────────────────────────────

def create_pothole():
    """
    POST /api/potholes
    ---
    tags: [Potholes]
    summary: Report a new pothole
    security: [{BearerAuth: []}]
    """
    # Support multipart (with image) or plain JSON
    if request.content_type and "multipart" in request.content_type:
        raw = request.form.to_dict()
        for f in ("latitude", "longitude", "priority"):
            if f in raw:
                try:
                    raw[f] = float(raw[f]) if f != "priority" else int(raw[f])
                except ValueError:
                    pass
    else:
        raw = request.get_json() or {}

    try:
        data = create_schema.load(raw)
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    # Handle optional image upload
    photo_url = data.get("photo_url", "")
    image_file = request.files.get("photo")
    if image_file:
        if not is_cloudinary_configured():
            return error_response("Image upload is not configured on this server.", 503)
        try:
            photo_url = upload_image(image_file)
        except ValueError as e:
            return error_response(str(e), 422)

    db = DatabaseConfig.get_db()
    pothole_model = PotholeModel(db)

    pothole = pothole_model.create(
        user_id=g.current_user_id,
        name=data["name"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        photo_url=photo_url,
        comment=data.get("comment", ""),
        priority=data.get("priority", 3),
    )
    logger.info("Pothole created by user %s", g.current_user_id)
    return success_response(
        data=PotholeModel.serialize(pothole),
        message="Pothole reported successfully.",
        status_code=201,
    )


# ─── READ ─────────────────────────────────────────────────────────────────────

def get_all_potholes():
    """
    GET /api/potholes
    ---
    tags: [Potholes]
    summary: Get all potholes (with filters & pagination)
    security: [{BearerAuth: []}]
    parameters:
      - {in: query, name: page,     schema: {type: integer, default: 1}}
      - {in: query, name: limit,    schema: {type: integer, default: 10}}
      - {in: query, name: status,   schema: {type: string, enum: [pending,inprogress,completed]}}
      - {in: query, name: priority, schema: {type: integer, minimum: 1, maximum: 5}}
    """
    page, limit = _get_pagination()
    status = request.args.get("status")
    priority = request.args.get("priority")

    if status and status not in PotholeModel.VALID_STATUSES:
        return error_response(f"Invalid status. Choose from: {PotholeModel.VALID_STATUSES}", 400)
    if priority:
        try:
            priority = int(priority)
            if not 1 <= priority <= 5:
                raise ValueError
        except ValueError:
            return error_response("Priority must be an integer between 1 and 5.", 400)

    db = DatabaseConfig.get_db()
    pothole_model = PotholeModel(db)
    docs, total = pothole_model.find_all(status=status, priority=priority, page=page, limit=limit)
    return paginated_response(
        data=[PotholeModel.serialize(d) for d in docs],
        total=total, page=page, limit=limit,
    )


def get_pothole_by_id(pothole_id):
    """
    GET /api/potholes/{id}
    ---
    tags: [Potholes]
    summary: Get a single pothole by ID
    security: [{BearerAuth: []}]
    """
    db = DatabaseConfig.get_db()
    pothole = PotholeModel(db).find_by_id(pothole_id)
    if not pothole:
        return error_response("Pothole not found.", 404)
    return success_response(data=PotholeModel.serialize(pothole))


def get_my_potholes():
    """
    GET /api/potholes/my
    ---
    tags: [Potholes]
    summary: Get all potholes reported by the logged-in user
    security: [{BearerAuth: []}]
    """
    page, limit = _get_pagination()
    db = DatabaseConfig.get_db()
    docs, total = PotholeModel(db).find_by_user(g.current_user_id, page=page, limit=limit)
    return paginated_response(
        data=[PotholeModel.serialize(d) for d in docs],
        total=total, page=page, limit=limit,
    )


def get_nearby_potholes():
    """
    GET /api/potholes/nearby
    ---
    tags: [Potholes]
    summary: Get potholes near a location (bonus geo feature)
    security: [{BearerAuth: []}]
    parameters:
      - {in: query, name: latitude,  required: true,  schema: {type: number}}
      - {in: query, name: longitude, required: true,  schema: {type: number}}
      - {in: query, name: radius_km, schema: {type: number, default: 5}}
    """
    try:
        params = nearby_schema.load(request.args.to_dict())
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    db = DatabaseConfig.get_db()
    docs = PotholeModel(db).find_nearby(
        lat=params["latitude"],
        lon=params["longitude"],
        radius_km=params.get("radius_km", 5.0),
    )
    return success_response(
        data=[PotholeModel.serialize(d) for d in docs],
        message=f"Found {len(docs)} pothole(s) nearby.",
    )


# ─── UPDATE ───────────────────────────────────────────────────────────────────

def update_pothole(pothole_id):
    """
    PUT /api/potholes/{id}
    ---
    tags: [Potholes]
    summary: Update own pothole report
    security: [{BearerAuth: []}]
    """
    try:
        data = update_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    if not data:
        return error_response("No fields to update.", 400)

    db = DatabaseConfig.get_db()
    pothole_model = PotholeModel(db)
    pothole = pothole_model.find_by_id(pothole_id)

    if not pothole:
        return error_response("Pothole not found.", 404)
    if str(pothole["user_id"]) != g.current_user_id and g.current_user_role != "admin":
        return error_response("Forbidden: You can only edit your own reports.", 403)

    # Rebuild location if lat/lon provided
    update_fields = {}
    if "latitude" in data or "longitude" in data:
        loc = pothole["location"].copy()
        if "latitude" in data:
            loc["latitude"] = data.pop("latitude")
        if "longitude" in data:
            loc["longitude"] = data.pop("longitude")
        update_fields["location"] = loc
    update_fields.update(data)

    pothole_model.update(pothole_id, update_fields)
    updated = pothole_model.find_by_id(pothole_id)
    return success_response(data=PotholeModel.serialize(updated), message="Pothole updated.")


# ─── DELETE ───────────────────────────────────────────────────────────────────

def delete_pothole(pothole_id):
    """
    DELETE /api/potholes/{id}
    ---
    tags: [Potholes]
    summary: Soft-delete own pothole report
    security: [{BearerAuth: []}]
    """
    db = DatabaseConfig.get_db()
    pothole_model = PotholeModel(db)
    pothole = pothole_model.find_by_id(pothole_id)

    if not pothole:
        return error_response("Pothole not found.", 404)
    if str(pothole["user_id"]) != g.current_user_id and g.current_user_role != "admin":
        return error_response("Forbidden: You can only delete your own reports.", 403)

    pothole_model.soft_delete(pothole_id)
    logger.info("Pothole %s soft-deleted by user %s", pothole_id, g.current_user_id)
    return success_response(message="Pothole deleted successfully.")
