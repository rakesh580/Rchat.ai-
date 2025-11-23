from pydantic import BaseModel, EmailStr, field_validator
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

# ---------------------------
# What we return after registration
# ---------------------------
class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True


# ---------------------------
# Incoming login request
# ---------------------------
class UserLogin(BaseModel):
    username_or_email: str
    password: str


# ---------------------------
# JWT response model
# ---------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"