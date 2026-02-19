from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user
from app.services.contact_service import add_contact, remove_contact, get_contacts

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("")
def list_contacts(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return get_contacts(user_id)


@router.post("")
def create_contact(body: dict, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    contact_id = body.get("contact_id")
    if not contact_id:
        raise HTTPException(status_code=400, detail="contact_id is required")
    if contact_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    try:
        return add_contact(user_id, contact_id)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Contact already exists")


@router.delete("/{contact_id}")
def delete_contact(contact_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    removed = remove_contact(user_id, contact_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"detail": "Contact removed"}
