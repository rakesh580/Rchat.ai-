from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from app.db.mongo import conversations_collection, messages_collection, users_collection


def _safe_oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid ID: {value}")


def get_or_create_direct(user_id: str, other_user_id: str) -> dict:
    """Find existing direct conversation or create one."""
    convo = conversations_collection.find_one({
        "type": "direct",
        "participants": {"$all": [user_id, other_user_id], "$size": 2},
    })
    if convo:
        convo["_id"] = str(convo["_id"])
        return convo

    doc = {
        "type": "direct",
        "participants": [user_id, other_user_id],
        "group_name": None,
        "admins": [],
        "last_message": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = conversations_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def create_group(creator_id: str, participant_ids: list[str], group_name: str) -> dict:
    all_participants = list(set([creator_id] + participant_ids))
    doc = {
        "type": "group",
        "participants": all_participants,
        "group_name": group_name,
        "admins": [creator_id],
        "created_by": creator_id,
        "last_message": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = conversations_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def get_user_conversations(user_id: str) -> list[dict]:
    cursor = conversations_collection.find(
        {"participants": user_id}
    ).sort("updated_at", -1)

    conversations = []
    for convo in cursor:
        convo["_id"] = str(convo["_id"])

        # Resolve participant profiles
        participants = []
        for pid in convo["participants"]:
            user = users_collection.find_one({"_id": _safe_oid(pid)})
            if user:
                user["_id"] = str(user["_id"])
                participants.append({
                    "_id": user["_id"],
                    "username": user["username"],
                    "display_name": user.get("display_name", user["username"]),
                    "avatar_url": user.get("avatar_url", ""),
                    "is_online": user.get("is_online", False),
                    "last_seen": user.get("last_seen"),
                    "is_bot": user.get("is_bot", False),
                })
        convo["participants"] = participants

        # Unread count
        unread = messages_collection.count_documents({
            "conversation_id": convo["_id"],
            "sender_id": {"$ne": user_id},
            "read_by": {"$nin": [user_id]},
        })
        convo["unread_count"] = unread

        conversations.append(convo)

    return conversations


def get_conversation_by_id(conversation_id: str) -> dict | None:
    convo = conversations_collection.find_one({"_id": _safe_oid(conversation_id)})
    if convo:
        convo["_id"] = str(convo["_id"])
    return convo


def get_conversation_with_profiles(conversation_id: str) -> dict | None:
    """Get conversation with resolved participant profiles."""
    convo = conversations_collection.find_one({"_id": _safe_oid(conversation_id)})
    if not convo:
        return None
    convo["_id"] = str(convo["_id"])

    participants = []
    for pid in convo["participants"]:
        user = users_collection.find_one({"_id": _safe_oid(pid)})
        if user:
            user["_id"] = str(user["_id"])
            participants.append({
                "_id": user["_id"],
                "username": user["username"],
                "display_name": user.get("display_name", user["username"]),
                "avatar_url": user.get("avatar_url", ""),
                "is_online": user.get("is_online", False),
                "last_seen": user.get("last_seen"),
                "is_bot": user.get("is_bot", False),
            })
    convo["participants"] = participants
    return convo


def add_member_to_group(conversation_id: str, user_id: str) -> bool:
    result = conversations_collection.update_one(
        {"_id": _safe_oid(conversation_id), "type": "group"},
        {"$addToSet": {"participants": user_id}},
    )
    return result.modified_count > 0


def remove_member_from_group(conversation_id: str, user_id: str) -> bool:
    result = conversations_collection.update_one(
        {"_id": _safe_oid(conversation_id), "type": "group"},
        {
            "$pull": {"participants": user_id, "admins": user_id},
        },
    )
    return result.modified_count > 0
