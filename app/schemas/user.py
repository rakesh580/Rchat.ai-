from pydantic import BaseModel, EmailStr


# ---------------------------
# Incoming request for register
# ---------------------------
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


# ---------------------------
# What we return to the client after registration
# ---------------------------
class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True


# ---------------------------
# NEW: Incoming login request
# ---------------------------
class UserLogin(BaseModel):
    username_or_email: str
    password: str


# ---------------------------
# NEW: JWT response model
# ---------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"