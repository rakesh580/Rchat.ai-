from datetime import datetime
from app.db.postgres import query, query_one, execute_returning, execute


def create_status(user_id: str, status_type: str, content: str | None = None,
                  media_url: str | None = None, caption: str | None = None,
                  background_color: str | None = None) -> dict:
    doc = execute_returning(
        """INSERT INTO statuses (user_id, type, content, media_url, caption, background_color, created_at, expires_at)
           VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW() + INTERVAL '24 hours')
           RETURNING *""",
        (user_id, status_type, content, media_url, caption, background_color),
    )
    doc["_id"] = str(doc.pop("id"))
    doc["user_id"] = str(doc["user_id"])
    doc["viewed_by"] = []
    return doc


def get_my_statuses(user_id: str) -> list[dict]:
    rows = query(
        """SELECT s.*,
                  COALESCE(
                      (SELECT array_agg(sv.viewer_id::text) FROM status_views sv WHERE sv.status_id = s.id),
                      ARRAY[]::text[]
                  ) AS viewed_by
           FROM statuses s
           WHERE s.user_id = %s AND s.expires_at > NOW()
           ORDER BY s.created_at ASC""",
        (user_id,),
    )
    for s in rows:
        s["_id"] = str(s.pop("id"))
        s["user_id"] = str(s["user_id"])
    return rows


def get_status_feed(user_id: str) -> list[dict]:
    """Get active statuses from all contacts, grouped by user."""
    rows = query(
        """SELECT s.*,
                  u.username, u.display_name, u.avatar_url,
                  COALESCE(
                      (SELECT array_agg(sv.viewer_id::text) FROM status_views sv WHERE sv.status_id = s.id),
                      ARRAY[]::text[]
                  ) AS viewed_by
           FROM statuses s
           JOIN contacts c ON c.contact_id::uuid = s.user_id AND c.user_id = %s
           JOIN users u ON u.id = s.user_id
           WHERE s.expires_at > NOW()
           ORDER BY s.created_at ASC""",
        (user_id,),
    )

    if not rows:
        return []

    # Group by user
    user_statuses = {}
    user_profiles = {}
    for s in rows:
        uid = str(s["user_id"])
        s["_id"] = str(s.pop("id"))
        s["user_id"] = uid

        if uid not in user_profiles:
            user_profiles[uid] = {
                "username": s.pop("username"),
                "display_name": s.pop("display_name"),
                "avatar_url": s.pop("avatar_url"),
            }
        else:
            s.pop("username", None)
            s.pop("display_name", None)
            s.pop("avatar_url", None)

        if uid not in user_statuses:
            user_statuses[uid] = []
        user_statuses[uid].append(s)

    result = []
    for uid, statuses in user_statuses.items():
        profile = user_profiles[uid]
        has_unseen = any(user_id not in s.get("viewed_by", []) for s in statuses)
        result.append({
            "user_id": uid,
            "username": profile["username"],
            "display_name": profile["display_name"],
            "avatar_url": profile["avatar_url"],
            "statuses": statuses,
            "has_unseen": has_unseen,
        })

    # Sort: unseen first, then by latest status time
    result.sort(key=lambda x: (
        not x["has_unseen"],
        -(x["statuses"][-1]["created_at"].timestamp() if isinstance(x["statuses"][-1]["created_at"], datetime) else 0),
    ))
    return result


def mark_status_viewed(status_id: str, viewer_id: str) -> bool:
    rowcount = execute(
        "INSERT INTO status_views (status_id, viewer_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (status_id, viewer_id),
    )
    return rowcount > 0


def delete_status(status_id: str, user_id: str) -> bool:
    rowcount = execute(
        "DELETE FROM statuses WHERE id = %s AND user_id = %s",
        (status_id, user_id),
    )
    return rowcount > 0
