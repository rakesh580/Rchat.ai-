from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal, Optional


class ConversationCreate(BaseModel):
    type: Literal["direct", "group"] = "direct"
    participant_ids: list[str] = Field(..., min_length=1, max_length=50)
    group_name: Optional[str] = Field(None, max_length=100)

    @field_validator("participant_ids")
    @classmethod
    def validate_participant_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate participant IDs")
        return v


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
