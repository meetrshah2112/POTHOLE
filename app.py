import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger

from config import get_config, DatabaseConfig
from routes import auth_bp, pothole_bp, admin_bp
from middleware import register_request_logging
from utils import setup_logging


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    cfg = get_config()
    app.config.from_object(cfg)

    # ── Logging ───────────────────────────────────────────────────────────────
    setup_logging(app)

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return jsonify({"success": False, "message": f"Unauthorized: {reason}"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"success": False, "message": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"success": False, "message": f"Invalid token: {reason}"}), 422

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )

    # Apply tighter limit to auth endpoints
    limiter.limit("10 per minute")(auth_bp)

    # ── Swagger / OpenAPI Docs ────────────────────────────────────────────────
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",
    }
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Smart Pothole Reporting & Management API",
            "description": (
                "RESTful backend for citizens to report potholes "
                "and admins to manage their resolution."
            ),
            "version": "1.0.0",
            "contact": {"email": "admin@potholeapi.com"},
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT token: `Bearer <token>`",
            }
        },
        "security": [{"BearerAuth": []}],
    }
    Swagger(app, config=swagger_config, template=swagger_template)

    # ── Request Logging Middleware ────────────────────────────────────────────
    register_request_logging(app)

    # ── DB connectivity check ─────────────────────────────────────────────────
    with app.app_context():
        try:
            DatabaseConfig.get_db()
            app.logger.info("Database ready.")
        except Exception as e:
            app.logger.error("Could not connect to MongoDB: %s", e)

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(pothole_bp)
    app.register_blueprint(admin_bp)

    # ── Global Error Handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"success": False, "message": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"success": False, "message": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Internal server error: %s", e)
        return jsonify({"success": False, "message": "Internal server error."}), 500

    @app.errorhandler(429)
    def rate_limit_exceeded(_):
        return jsonify({"success": False, "message": "Rate limit exceeded. Slow down."}), 429

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        return jsonify({"success": True, "message": "API is running.", "version": "1.0.0"})

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
