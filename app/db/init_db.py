from datetime import datetime
from bson import ObjectId
from app.db.mongo import (
    users_collection,
    conversations_collection,
    messages_collection,
    contacts_collection,
    statuses_collection,
)

AI_BOT_ID = ObjectId("000000000000000000000001")


def init_db() -> None:
    """Create MongoDB indexes and seed the AI bot user."""

    # Users indexes
    users_collection.create_index("email", unique=True)
    users_collection.create_index("username", unique=True)
    users_collection.create_index("is_bot")

    # Conversations indexes
    conversations_collection.create_index("participants")
    conversations_collection.create_index([("updated_at", -1)])

    # Messages indexes
    messages_collection.create_index([("conversation_id", 1), ("created_at", 1)])

    # Contacts indexes
    contacts_collection.create_index(
        [("user_id", 1), ("contact_id", 1)], unique=True
    )

    # Statuses indexes
    statuses_collection.create_index([("user_id", 1), ("created_at", -1)])
    statuses_collection.create_index("expires_at", expireAfterSeconds=0)  # TTL auto-delete

    # Seed AI bot user if not present
    if not users_collection.find_one({"_id": AI_BOT_ID}):
        users_collection.insert_one({
            "_id": AI_BOT_ID,
            "email": "ai@rchat.ai",
            "username": "rchat_ai",
            "display_name": "Rchat.ai Bot",
            "hashed_password": "",
            "avatar_url": "",
            "is_online": True,
            "last_seen": datetime.utcnow(),
            "is_bot": True,
            "created_at": datetime.utcnow(),
        })
