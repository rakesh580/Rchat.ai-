from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 72:
            raise ValueError("Password cannot exceed 72 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain a special character")
        return v


class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    username: str
    display_name: str = ""

    class Config:
        populate_by_name = True


class UserProfile(BaseModel):
    id: str = Field(..., alias="_id")
    username: str
    display_name: str = ""
    avatar_url: str = ""
    bio: str = ""
    is_online: bool = False
    last_seen: Optional[datetime] = None
    is_bot: bool = False

    class Config:
        populate_by_name = True


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None

    @field_validator("bio")
    def validate_bio(cls, v):
        if v is not None and len(v) > 150:
            raise ValueError("Bio cannot exceed 150 characters")
        return v

    @field_validator("display_name")
    def validate_display_name(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("Display name cannot exceed 50 characters")
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Display name cannot be empty")
        return v


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
