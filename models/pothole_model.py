from datetime import datetime, timezone
from bson import ObjectId
from math import radians, cos, sin, asin, sqrt


def _haversine(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


class PotholeModel:
    COLLECTION = "potholes"
    VALID_STATUSES = ["pending", "inprogress", "completed"]

    def __init__(self, db):
        self.collection = db[self.COLLECTION]

    # ─── CREATE ───────────────────────────────────────────────────────────────

    def create(
        self,
        user_id: str,
        name: str,
        latitude: float,
        longitude: float,
        photo_url: str = "",
        comment: str = "",
        priority: int = 3,
    ) -> dict:
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": ObjectId(user_id),
            "name": name,
            "location": {"latitude": latitude, "longitude": longitude},
            "photo_url": photo_url,
            "comment": comment,
            "priority": priority,
            "status": "pending",
            "deleted_at": None,          # soft-delete field
            "created_at": now,
            "updated_at": now,
        }
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    # ─── READ ─────────────────────────────────────────────────────────────────

    def find_by_id(self, pothole_id: str) -> dict | None:
        try:
            return self.collection.find_one(
                {"_id": ObjectId(pothole_id), "deleted_at": None}
            )
        except Exception:
            return None

    def find_all(
        self,
        status: str = None,
        priority: int = None,
        user_id: str = None,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list, int]:
        """Return (records, total_count) with optional filters and pagination."""
        query = {"deleted_at": None}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if user_id:
            try:
                query["user_id"] = ObjectId(user_id)
            except Exception:
                return [], 0

        total = self.collection.count_documents(query)
        skip = (page - 1) * limit
        docs = list(
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return docs, total

    def find_by_user(self, user_id: str, page: int = 1, limit: int = 10) -> tuple[list, int]:
        return self.find_all(user_id=user_id, page=page, limit=limit)

    def find_nearby(self, lat: float, lon: float, radius_km: float = 5.0) -> list:
        """Return potholes within radius_km of the given point (brute-force for simplicity)."""
        all_docs = list(self.collection.find({"deleted_at": None}))
        nearby = []
        for doc in all_docs:
            dlat = doc["location"]["latitude"]
            dlon = doc["location"]["longitude"]
            if _haversine(lat, lon, dlat, dlon) <= radius_km:
                nearby.append(doc)
        return nearby

    # ─── UPDATE ───────────────────────────────────────────────────────────────

    def update(self, pothole_id: str, update_fields: dict) -> bool:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"_id": ObjectId(pothole_id), "deleted_at": None},
            {"$set": update_fields},
        )
        return result.modified_count > 0

    # ─── DELETE ───────────────────────────────────────────────────────────────

    def soft_delete(self, pothole_id: str) -> bool:
        """Mark as deleted instead of removing from DB."""
        result = self.collection.update_one(
            {"_id": ObjectId(pothole_id), "deleted_at": None},
            {"$set": {"deleted_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count > 0

    def hard_delete(self, pothole_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(pothole_id)})
        return result.deleted_count > 0

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    @staticmethod
    def serialize(doc: dict) -> dict:
        return {
            "id": str(doc["_id"]),
            "user_id": str(doc["user_id"]),
            "name": doc["name"],
            "location": doc["location"],
            "photo_url": doc.get("photo_url", ""),
            "comment": doc.get("comment", ""),
            "priority": doc["priority"],
            "status": doc["status"],
            "created_at": doc["created_at"].isoformat(),
            "updated_at": doc["updated_at"].isoformat(),
        }
