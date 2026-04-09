import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    _client = None
    _db = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/pothole_db")
                cls._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                cls._client.admin.command("ping")
                logger.info("✅ Connected to MongoDB Atlas successfully.")
            except ConnectionFailure as e:
                logger.error(f"❌ MongoDB connection failed: {e}")
                raise
        return cls._client

    @classmethod
    def get_db(cls):
        if cls._db is None:
            client = cls.get_client()
            db_name = os.getenv("MONGO_DB_NAME", "pothole_db")
            cls._db = client[db_name]
            # Create indexes for performance
            cls._create_indexes()
        return cls._db

    @classmethod
    def _create_indexes(cls):
        db = cls._db
        # Users: unique email index
        db.users.create_index("email", unique=True)
        # Potholes: index on user_id, status, priority for fast queries
        db.potholes.create_index("user_id")
        db.potholes.create_index("status")
        db.potholes.create_index("priority")
        db.potholes.create_index("deleted_at")
        # Geo index for nearby potholes (bonus feature)
        db.potholes.create_index(
            [("location.latitude", 1), ("location.longitude", 1)]
        )
        logger.info("✅ Database indexes created.")
