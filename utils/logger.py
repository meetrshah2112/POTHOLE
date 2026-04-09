import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(app):
    """Configure application-level logging to console and rotating file."""
    log_level = logging.DEBUG if app.debug else logging.INFO

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # File handler (rotating, max 5 MB × 3 backups)
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.setLevel(log_level)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    # Also configure root logger so our models/controllers log properly
    logging.basicConfig(handlers=[console_handler], level=log_level, force=True)

    app.logger.info("Logging configured.")
