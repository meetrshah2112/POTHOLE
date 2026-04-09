import logging
from flask import request
from marshmallow import ValidationError

from models import PotholeModel
from config import DatabaseConfig
from utils import (
    UpdateStatusSchema, UpdatePrioritySchema,
    success_response, error_response, paginated_response,
)

logger = logging.getLogger(__name__)
status_schema = UpdateStatusSchema()
priority_schema = UpdatePrioritySchema()


def _get_pagination():
    try:
        page = max(1, int(request.args.get("page", 1)))
        limit = min(50, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        page, limit = 1, 10
    return page, limit


def admin_get_all_potholes():
    """
    GET /api/admin/potholes
    ---
    tags: [Admin]
    summary: Get all potholes (admin view, includes filters)
    security: [{BearerAuth: []}]
    parameters:
      - {in: query, name: page,     schema: {type: integer, default: 1}}
      - {in: query, name: limit,    schema: {type: integer, default: 10}}
      - {in: query, name: status,   schema: {type: string}}
      - {in: query, name: priority, schema: {type: integer}}
      - {in: query, name: user_id,  schema: {type: string}}
    """
    page, limit = _get_pagination()
    status   = request.args.get("status")
    priority = request.args.get("priority")
    user_id  = request.args.get("user_id")

    if status and status not in PotholeModel.VALID_STATUSES:
        return error_response(f"Invalid status. Choose from: {PotholeModel.VALID_STATUSES}", 400)
    if priority:
        try:
            priority = int(priority)
            if not 1 <= priority <= 5:
                raise ValueError
        except ValueError:
            return error_response("Priority must be between 1 and 5.", 400)

    db = DatabaseConfig.get_db()
    docs, total = PotholeModel(db).find_all(
        status=status, priority=priority, user_id=user_id, page=page, limit=limit
    )
    return paginated_response(
        data=[PotholeModel.serialize(d) for d in docs],
        total=total, page=page, limit=limit,
        message="All potholes retrieved.",
    )


def admin_update_status(pothole_id):
    """
    PATCH /api/admin/potholes/{id}/status
    ---
    tags: [Admin]
    summary: Update the status of a pothole
    security: [{BearerAuth: []}]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [status]
            properties:
              status: {type: string, enum: [pending, inprogress, completed]}
    """
    try:
        data = status_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    db = DatabaseConfig.get_db()
    model = PotholeModel(db)

    pothole = model.find_by_id(pothole_id)
    if not pothole:
        return error_response("Pothole not found.", 404)

    model.update(pothole_id, {"status": data["status"]})
    logger.info("Admin updated status of pothole %s → %s", pothole_id, data["status"])
    updated = model.find_by_id(pothole_id)
    return success_response(data=PotholeModel.serialize(updated), message="Status updated.")


def admin_update_priority(pothole_id):
    """
    PATCH /api/admin/potholes/{id}/priority
    ---
    tags: [Admin]
    summary: Update the priority of a pothole
    security: [{BearerAuth: []}]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [priority]
            properties:
              priority: {type: integer, minimum: 1, maximum: 5}
    """
    try:
        data = priority_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    db = DatabaseConfig.get_db()
    model = PotholeModel(db)

    pothole = model.find_by_id(pothole_id)
    if not pothole:
        return error_response("Pothole not found.", 404)

    model.update(pothole_id, {"priority": data["priority"]})
    logger.info("Admin updated priority of pothole %s → %s", pothole_id, data["priority"])
    updated = model.find_by_id(pothole_id)
    return success_response(data=PotholeModel.serialize(updated), message="Priority updated.")


def admin_delete_pothole(pothole_id):
    """
    DELETE /api/admin/potholes/{id}
    ---
    tags: [Admin]
    summary: Hard-delete any pothole report
    security: [{BearerAuth: []}]
    """
    db = DatabaseConfig.get_db()
    model = PotholeModel(db)

    pothole = model.find_by_id(pothole_id)
    if not pothole:
        return error_response("Pothole not found.", 404)

    model.hard_delete(pothole_id)
    logger.info("Admin hard-deleted pothole %s", pothole_id)
    return success_response(message="Pothole permanently deleted.")
