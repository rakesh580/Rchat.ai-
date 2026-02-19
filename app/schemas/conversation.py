from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ConversationCreate(BaseModel):
    type: str = "direct"  # "direct" or "group"
    participant_ids: list[str]
    group_name: Optional[str] = None


class GroupMemberAdd(BaseModel):
    user_id: str


class LastMessage(BaseModel):
    content: str
    sender_id: str
    timestamp: datetime


class ConversationOut(BaseModel):
    id: str = Field(..., alias="_id")
    type: str
    participants: list[dict]  # list of UserProfile dicts
    group_name: Optional[str] = None
    last_message: Optional[LastMessage] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
