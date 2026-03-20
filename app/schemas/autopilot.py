from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class AutopilotSettingsUpdate(BaseModel):
    is_active: bool = False
    away_message: Optional[str] = ""
    backup_person_id: Optional[str] = None
    auto_respond_enabled: bool = True
    expected_return_date: Optional[datetime] = None

    @field_validator("away_message")
    def validate_away_message(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("Away message cannot exceed 500 characters")
        return v


class AutopilotSettingsOut(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    is_active: bool
    away_message: str = ""
    backup_person_id: Optional[str] = None
    auto_respond_enabled: bool = True
    expected_return_date: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class AutopilotActivityOut(BaseModel):
    id: str = Field(..., alias="_id")
    conversation_id: str
    message_id: str
    sender_id: str
    sender_name: str = ""
    category: str
    action_taken: str
    auto_response_content: Optional[str] = None
    deadline: Optional[datetime] = None
    is_resolved: bool = False
    created_at: datetime

    class Config:
        populate_by_name = True


class AutopilotBriefingOut(BaseModel):
    urgent: list[AutopilotActivityOut] = []
    action_needed: list[AutopilotActivityOut] = []
    informational: list[AutopilotActivityOut] = []
    total_messages: int = 0
    auto_responses_sent: int = 0
    messages_forwarded: int = 0


class AutopilotStatusOut(BaseModel):
    is_autopilot: bool = False
    away_message: str = ""
    expected_return_date: Optional[datetime] = None
