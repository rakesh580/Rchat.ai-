from app.db.postgres import query, query_one, execute_returning, execute


def add_contact(user_id: str, contact_id: str) -> dict:
    doc = execute_returning(
        """INSERT INTO contacts (user_id, contact_id, added_at)
           VALUES (%s, %s, NOW()) RETURNING *""",
        (user_id, contact_id),
    )
    doc["_id"] = str(doc.pop("id"))
    doc["user_id"] = str(doc["user_id"])
    doc["contact_id"] = str(doc["contact_id"])

    # Fetch contact user profile
    contact_user = query_one(
        "SELECT id, username, display_name, avatar_url, is_online, last_seen, is_bot FROM users WHERE id = %s",
        (contact_id,),
    )
    if contact_user:
        contact_user["_id"] = str(contact_user.pop("id"))
        doc["contact"] = contact_user
    else:
        doc["contact"] = {}
    return doc


def remove_contact(user_id: str, contact_id: str) -> bool:
    rowcount = execute(
        "DELETE FROM contacts WHERE user_id = %s AND contact_id = %s",
        (user_id, contact_id),
    )
    return rowcount > 0


def get_contacts(user_id: str) -> list[dict]:
    rows = query(
        """SELECT c.id, c.user_id, c.contact_id, c.added_at,
                  u.username, u.display_name, u.avatar_url, u.is_online, u.last_seen, u.is_bot
           FROM contacts c
           JOIN users u ON u.id = c.contact_id::uuid
           WHERE c.user_id = %s""",
        (user_id,),
    )
    contacts = []
    for row in rows:
        doc = {
            "_id": str(row["id"]),
            "user_id": str(row["user_id"]),
            "contact_id": str(row["contact_id"]),
            "added_at": row["added_at"],
            "contact": {
                "_id": str(row["contact_id"]),
                "username": row["username"],
                "display_name": row.get("display_name", row["username"]),
                "avatar_url": row.get("avatar_url", ""),
                "is_online": row.get("is_online", False),
                "last_seen": row.get("last_seen"),
                "is_bot": row.get("is_bot", False),
            },
        }
        contacts.append(doc)
    return contacts


def search_users(query_str: str, exclude_user_id: str) -> list[dict]:
    # Escape ILIKE special characters to prevent wildcard abuse
    escaped = query_str.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    rows = query(
        """SELECT id, username, display_name, avatar_url, is_online
           FROM users
           WHERE id != %s
           AND is_bot IS NOT TRUE
           AND (username ILIKE %s OR display_name ILIKE %s)
           LIMIT 20""",
        (exclude_user_id, pattern, pattern),
    )
    results = []
    for user in rows:
        results.append({
            "_id": str(user["id"]),
            "username": user["username"],
            "display_name": user.get("display_name", user["username"]),
            "avatar_url": user.get("avatar_url", ""),
            "is_online": user.get("is_online", False),
            "is_bot": False,
        })
    return results
