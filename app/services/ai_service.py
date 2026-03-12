from groq import Groq
from app.core.config import settings
from app.db.postgres import query
from app.services.message_service import save_message

AI_BOT_USER_ID = "00000000-0000-0000-0000-000000000001"

groq_client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are Rchat.ai, a helpful and friendly AI assistant. "
    "Keep responses concise and clear."
)


def get_ai_reply(conversation_id: str, user_content: str) -> dict:
    """Build context from conversation history and call Groq."""
    # Get last 20 messages for context
    rows = query(
        """SELECT sender_id, content FROM messages
           WHERE conversation_id = %s
           ORDER BY created_at DESC LIMIT 20""",
        (conversation_id,),
    )

    past_messages = []
    for doc in rows:
        role = "assistant" if str(doc["sender_id"]) == AI_BOT_USER_ID else "user"
        past_messages.append({"role": role, "content": doc["content"]})
    past_messages.reverse()

    # Build messages for Groq
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(past_messages)
    messages.append({"role": "user", "content": user_content})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content
    return save_message(conversation_id, AI_BOT_USER_ID, reply)
