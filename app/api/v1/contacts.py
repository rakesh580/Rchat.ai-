from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from psycopg2.errors import UniqueViolation

from app.api.deps import get_current_user
from app.services.contact_service import add_contact, remove_contact, get_contacts
from app.core.rate_limit import limiter

router = APIRouter(prefix="/contacts", tags=["Contacts"])


class ContactCreate(BaseModel):
    contact_id: str

    @field_validator("contact_id")
    def validate_uuid(cls, v):
        try:
            UUID(v)
        except ValueError:
            raise ValueError("contact_id must be a valid UUID")
        return v


@router.get("")
@limiter.limit("30/minute")
def list_contacts(request: Request, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return get_contacts(user_id)


@router.post("")
@limiter.limit("20/minute")
def create_contact(request: Request, body: ContactCreate, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    if body.contact_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    try:
        return add_contact(user_id, body.contact_id)
    except Exception as e:
        if isinstance(e, UniqueViolation) or "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail="Contact already exists")
        raise


@router.delete("/{contact_id}")
def delete_contact(contact_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    removed = remove_contact(user_id, contact_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Contact removed"}
