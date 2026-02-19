from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from app.db.mongo import contacts_collection, users_collection
import re


def _safe_oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid ID: {value}")


def add_contact(user_id: str, contact_id: str) -> dict:
    doc = {
        "user_id": user_id,
        "contact_id": contact_id,
        "added_at": datetime.utcnow(),
    }
    result = contacts_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    contact_user = users_collection.find_one({"_id": _safe_oid(contact_id)})
    if contact_user:
        contact_user["_id"] = str(contact_user["_id"])
    doc["contact"] = contact_user or {}
    return doc


def remove_contact(user_id: str, contact_id: str) -> bool:
    result = contacts_collection.delete_one({"user_id": user_id, "contact_id": contact_id})
    return result.deleted_count > 0


def get_contacts(user_id: str) -> list[dict]:
    cursor = contacts_collection.find({"user_id": user_id})
    contacts = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        contact_user = users_collection.find_one({"_id": ObjectId(doc["contact_id"])})
        if contact_user:
            contact_user["_id"] = str(contact_user["_id"])
            doc["contact"] = {
                "_id": contact_user["_id"],
                "username": contact_user["username"],
                "display_name": contact_user.get("display_name", contact_user["username"]),
                "avatar_url": contact_user.get("avatar_url", ""),
                "is_online": contact_user.get("is_online", False),
                "last_seen": contact_user.get("last_seen"),
                "is_bot": contact_user.get("is_bot", False),
            }
        else:
            doc["contact"] = {}
        contacts.append(doc)
    return contacts


def search_users(query: str, exclude_user_id: str) -> list[dict]:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    cursor = users_collection.find({
        "$and": [
            {"_id": {"$ne": _safe_oid(exclude_user_id)}},
            {"is_bot": {"$ne": True}},
            {"$or": [
                {"username": {"$regex": pattern}},
                {"email": {"$regex": pattern}},
            ]},
        ]
    }).limit(20)

    results = []
    for user in cursor:
        user["_id"] = str(user["_id"])
        results.append({
            "_id": user["_id"],
            "username": user["username"],
            "display_name": user.get("display_name", user["username"]),
            "avatar_url": user.get("avatar_url", ""),
            "is_online": user.get("is_online", False),
            "is_bot": False,
        })
    return results
