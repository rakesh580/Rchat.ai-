from pydantic import BaseModel, Field
from datetime import datetime


class MessageOut(BaseModel):
    id: str = Field(..., alias="_id")
    conversation_id: str
    sender_id: str
    content: str
    message_type: str = "text"
    status: str = "sent"
    read_by: list[str] = []
    created_at: datetime

    class Config:
        populate_by_name = True
