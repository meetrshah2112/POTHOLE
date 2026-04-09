import logging
from flask import request
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError

from models import UserModel
from config import DatabaseConfig
from utils import (
    RegisterSchema, LoginSchema,
    success_response, error_response,
)

logger = logging.getLogger(__name__)
register_schema = RegisterSchema()
login_schema = LoginSchema()


def register():
    """
    POST /api/auth/register
    ---
    tags: [Auth]
    summary: Register a new user
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [name, email, password]
            properties:
              name:   {type: string, example: "Alice"}
              email:  {type: string, example: "alice@example.com"}
              password: {type: string, example: "secret123"}
              role:   {type: string, enum: [user, admin], default: user}
    responses:
      201: {description: User registered successfully}
      400: {description: Validation error or email already exists}
    """
    try:
        data = register_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    db = DatabaseConfig.get_db()
    user_model = UserModel(db)

    if user_model.email_exists(data["email"]):
        return error_response("Email already registered.", 409)

    user = user_model.create(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        role=data.get("role", "user"),
    )
    logger.info("New user registered: %s", data["email"])
    return success_response(
        data=UserModel.serialize(user),
        message="User registered successfully.",
        status_code=201,
    )


def login():
    """
    POST /api/auth/login
    ---
    tags: [Auth]
    summary: Login and receive JWT
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [email, password]
            properties:
              email:    {type: string}
              password: {type: string}
    responses:
      200: {description: Login successful, JWT returned}
      401: {description: Invalid credentials}
    """
    try:
        data = login_schema.load(request.get_json() or {})
    except ValidationError as ve:
        return error_response("Validation failed.", 400, errors=ve.messages)

    db = DatabaseConfig.get_db()
    user_model = UserModel(db)

    user = user_model.find_by_email(data["email"])
    if not user or not UserModel.check_password(data["password"], user["password"]):
        return error_response("Invalid email or password.", 401)

    additional_claims = {"role": user["role"]}
    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims=additional_claims,
    )
    logger.info("User logged in: %s", data["email"])
    return success_response(
        data={"access_token": token, "user": UserModel.serialize(user)},
        message="Login successful.",
    )
