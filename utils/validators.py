from marshmallow import Schema, fields, validate, validates, ValidationError


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class RegisterSchema(Schema):
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "Name is required."},
    )
    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "validator_failed": "Invalid email format."},
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=128),
        error_messages={"required": "Password is required."},
    )
    role = fields.Str(
        load_default="user",
        validate=validate.OneOf(["user", "admin"]),
    )


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


# ─── Pothole Schemas ──────────────────────────────────────────────────────────

class LocationSchema(Schema):
    latitude = fields.Float(
        required=True,
        validate=validate.Range(min=-90.0, max=90.0),
        error_messages={"validator_failed": "Latitude must be between -90 and 90."},
    )
    longitude = fields.Float(
        required=True,
        validate=validate.Range(min=-180.0, max=180.0),
        error_messages={"validator_failed": "Longitude must be between -180 and 180."},
    )


class CreatePotholeSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    latitude = fields.Float(
        required=True,
        validate=validate.Range(min=-90.0, max=90.0),
    )
    longitude = fields.Float(
        required=True,
        validate=validate.Range(min=-180.0, max=180.0),
    )
    photo_url = fields.Str(load_default="", validate=validate.Length(max=500))
    comment = fields.Str(load_default="", validate=validate.Length(max=1000))
    priority = fields.Int(
        load_default=3,
        validate=validate.Range(min=1, max=5),
        error_messages={"validator_failed": "Priority must be between 1 and 5."},
    )


class UpdatePotholeSchema(Schema):
    name = fields.Str(validate=validate.Length(min=3, max=200))
    latitude = fields.Float(validate=validate.Range(min=-90.0, max=90.0))
    longitude = fields.Float(validate=validate.Range(min=-180.0, max=180.0))
    photo_url = fields.Str(validate=validate.Length(max=500))
    comment = fields.Str(validate=validate.Length(max=1000))
    priority = fields.Int(validate=validate.Range(min=1, max=5))


class UpdateStatusSchema(Schema):
    status = fields.Str(
        required=True,
        validate=validate.OneOf(
            ["pending", "inprogress", "completed"],
            error="Status must be one of: pending, inprogress, completed.",
        ),
    )


class UpdatePrioritySchema(Schema):
    priority = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=5),
        error_messages={"validator_failed": "Priority must be between 1 and 5."},
    )


class NearbySchema(Schema):
    latitude = fields.Float(required=True, validate=validate.Range(min=-90.0, max=90.0))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180.0, max=180.0))
    radius_km = fields.Float(load_default=5.0, validate=validate.Range(min=0.1, max=100.0))
