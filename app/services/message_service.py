from datetime import datetime
from bson import ObjectId
from app.db.mongo import messages_collection, conversations_collection


def save_message(conversation_id: str, sender_id: str, content: str, message_type: str = "text") -> dict:
    doc = {
        "conversation_id": conversation_id,
        "sender_id": sender_id,
        "content": content,
        "message_type": message_type,
        "status": "sent",
        "read_by": [sender_id],
        "created_at": datetime.utcnow(),
    }
    result = messages_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    # Update conversation's last_message
    conversations_collection.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {
            "last_message": {
                "content": content,
                "sender_id": sender_id,
                "timestamp": doc["created_at"],
            },
            "updated_at": doc["created_at"],
        }},
    )
    return doc


def get_messages(conversation_id: str, skip: int = 0, limit: int = 50) -> list[dict]:
    cursor = messages_collection.find(
        {"conversation_id": conversation_id}
    ).sort("created_at", 1).skip(skip).limit(limit)

    messages = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(doc)
    return messages


def mark_messages_read(conversation_id: str, reader_id: str) -> int:
    result = messages_collection.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": reader_id},
            "read_by": {"$nin": [reader_id]},
        },
        {"$addToSet": {"read_by": reader_id}, "$set": {"status": "read"}},
    )
    return result.modified_count


def get_unread_count(conversation_id: str, user_id: str) -> int:
    return messages_collection.count_documents({
        "conversation_id": conversation_id,
        "sender_id": {"$ne": user_id},
        "read_by": {"$nin": [user_id]},
    })
