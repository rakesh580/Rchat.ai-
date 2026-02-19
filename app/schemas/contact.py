from pydantic import BaseModel, Field
from datetime import datetime


class ContactAdd(BaseModel):
    contact_id: str


class ContactOut(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    contact_id: str
    contact: dict  # UserProfile dict
    added_at: datetime

    class Config:
        populate_by_name = True
