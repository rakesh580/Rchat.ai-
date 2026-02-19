from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class StatusCreate(BaseModel):
    type: str  # "text", "image", "video"
    content: Optional[str] = None  # text content for text type
    caption: Optional[str] = None  # caption for image/video
    background_color: Optional[str] = "#6C5CE7"  # for text type

    @field_validator("type")
    def validate_type(cls, v):
        if v not in ("text", "image", "video"):
            raise ValueError("Status type must be text, image, or video")
        return v

    @field_validator("content")
    def validate_content(cls, v):
        if v is not None and len(v) > 500:
            raise ValueError("Status text cannot exceed 500 characters")
        return v

    @field_validator("caption")
    def validate_caption(cls, v):
        if v is not None and len(v) > 200:
            raise ValueError("Caption cannot exceed 200 characters")
        return v


class StatusOut(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    type: str
    content: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    background_color: Optional[str] = None
    viewed_by: list[str] = []
    created_at: datetime
    expires_at: datetime

    class Config:
        populate_by_name = True


class StatusUserGroup(BaseModel):
    """A user's collection of active statuses."""
    user_id: str
    username: str
    display_name: str
    avatar_url: str = ""
    statuses: list[StatusOut] = []
    has_unseen: bool = False
