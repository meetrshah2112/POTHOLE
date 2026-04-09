import os
import cloudinary
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

_configured = False


def _configure():
    global _configured
    if not _configured:
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        )
        _configured = True


def upload_image(file_storage) -> str:
    """
    Upload a FileStorage object to Cloudinary.
    Returns the secure URL string, or raises on failure.
    """
    _configure()
    try:
        result = cloudinary.uploader.upload(
            file_storage,
            folder="potholes",
            allowed_formats=["jpg", "jpeg", "png", "webp"],
            transformation={"quality": "auto", "fetch_format": "auto"},
        )
        return result["secure_url"]
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise ValueError(f"Image upload failed: {str(e)}")


def is_cloudinary_configured() -> bool:
    return all([
        os.getenv("CLOUDINARY_CLOUD_NAME"),
        os.getenv("CLOUDINARY_API_KEY"),
        os.getenv("CLOUDINARY_API_SECRET"),
    ])
