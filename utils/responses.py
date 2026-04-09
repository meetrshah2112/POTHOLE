from flask import jsonify


def success_response(data=None, message="Success", status_code=200, **extras):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(extras)
    return jsonify(payload), status_code


def error_response(message="An error occurred", status_code=400, errors=None):
    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    return jsonify(payload), status_code


def paginated_response(data, total, page, limit, message="Success"):
    return jsonify({
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        },
    }), 200
