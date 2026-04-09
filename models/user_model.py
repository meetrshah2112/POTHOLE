from datetime import datetime, timezone
from bson import ObjectId
import bcrypt


class UserModel:
    COLLECTION = "users"
    ROLES = ["user", "admin"]

    def __init__(self, db):
        self.collection = db[self.COLLECTION]

    # ─── CREATE ───────────────────────────────────────────────────────────────

    def create(self, name: str, email: str, password: str, role: str = "user") -> dict:
        """Hash password and insert new user. Returns inserted doc."""
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = {
            "name": name,
            "email": email.lower().strip(),
            "password": hashed_pw,
            "role": role,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.collection.insert_one(user)
        user["_id"] = result.inserted_id
        return user

    # ─── READ ─────────────────────────────────────────────────────────────────

    def find_by_email(self, email: str) -> dict | None:
        return self.collection.find_one({"email": email.lower().strip()})

    def find_by_id(self, user_id: str) -> dict | None:
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    def email_exists(self, email: str) -> bool:
        return self.collection.count_documents({"email": email.lower().strip()}) > 0

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    @staticmethod
    def check_password(plain: str, hashed: bytes) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed)

    @staticmethod
    def serialize(user: dict) -> dict:
        """Return safe public-facing user dict (no password)."""
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"].isoformat(),
        }
