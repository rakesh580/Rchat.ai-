from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from app.db.mongo import statuses_collection, contacts_collection, users_collection


def _safe_oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid ID: {value}")


def create_status(user_id: str, status_type: str, content: str | None = None,
                  media_url: str | None = None, caption: str | None = None,
                  background_color: str | None = None) -> dict:
    now = datetime.utcnow()
    doc = {
        "user_id": user_id,
        "type": status_type,
        "content": content,
        "media_url": media_url,
        "caption": caption,
        "background_color": background_color,
        "viewed_by": [],
        "created_at": now,
        "expires_at": now + timedelta(hours=24),
    }
    result = statuses_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def get_my_statuses(user_id: str) -> list[dict]:
    now = datetime.utcnow()
    cursor = statuses_collection.find({
        "user_id": user_id,
        "expires_at": {"$gt": now},
    }).sort("created_at", 1)
    results = []
    for s in cursor:
        s["_id"] = str(s["_id"])
        results.append(s)
    return results


def get_status_feed(user_id: str) -> list[dict]:
    """Get active statuses from all contacts, grouped by user."""
    # Get contact IDs
    contacts = contacts_collection.find({"user_id": user_id})
    contact_ids = [c["contact_id"] for c in contacts]

    if not contact_ids:
        return []

    now = datetime.utcnow()
    # Fetch all active statuses from contacts
    cursor = statuses_collection.find({
        "user_id": {"$in": contact_ids},
        "expires_at": {"$gt": now},
    }).sort("created_at", 1)

    # Group by user
    user_statuses = {}
    for s in cursor:
        s["_id"] = str(s["_id"])
        uid = s["user_id"]
        if uid not in user_statuses:
            user_statuses[uid] = []
        user_statuses[uid].append(s)

    if not user_statuses:
        return []

    # Fetch user profiles
    user_oids = [_safe_oid(uid) for uid in user_statuses]
    users = {str(u["_id"]): u for u in users_collection.find({"_id": {"$in": user_oids}})}

    result = []
    for uid, statuses in user_statuses.items():
        u = users.get(uid, {})
        has_unseen = any(user_id not in s.get("viewed_by", []) for s in statuses)
        result.append({
            "user_id": uid,
            "username": u.get("username", ""),
            "display_name": u.get("display_name", ""),
            "avatar_url": u.get("avatar_url", ""),
            "statuses": statuses,
            "has_unseen": has_unseen,
        })

    # Sort: unseen first, then by latest status time
    result.sort(key=lambda x: (not x["has_unseen"], -x["statuses"][-1]["created_at"].timestamp() if isinstance(x["statuses"][-1]["created_at"], datetime) else 0))
    return result


def mark_status_viewed(status_id: str, viewer_id: str) -> bool:
    result = statuses_collection.update_one(
        {"_id": _safe_oid(status_id)},
        {"$addToSet": {"viewed_by": viewer_id}},
    )
    return result.modified_count > 0


def delete_status(status_id: str, user_id: str) -> bool:
    result = statuses_collection.delete_one({
        "_id": _safe_oid(status_id),
        "user_id": user_id,
    })
    return result.deleted_count > 0
