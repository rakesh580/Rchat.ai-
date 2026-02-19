from groq import Groq
from app.core.config import settings
from app.db.mongo import messages_collection
from app.services.message_service import save_message
from app.db.init_db import AI_BOT_ID

groq_client = Groq(api_key=settings.GROQ_API_KEY)
BOT_USER_ID = str(AI_BOT_ID)

SYSTEM_PROMPT = (
    "You are Rchat.ai, a helpful and friendly AI assistant. "
    "Keep responses concise and clear."
)


def get_ai_reply(conversation_id: str, user_content: str) -> dict:
    """Build context from conversation history and call Groq."""
    # Get last 20 messages for context
    cursor = messages_collection.find(
        {"conversation_id": conversation_id}
    ).sort("created_at", -1).limit(20)

    past_messages = []
    for doc in cursor:
        role = "assistant" if doc["sender_id"] == BOT_USER_ID else "user"
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
    return save_message(conversation_id, BOT_USER_ID, reply)
