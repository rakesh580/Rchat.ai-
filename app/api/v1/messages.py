# app/api/v1/messages.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.message import MessageCreate, MessageOut
from app.services.message_service import send_message, get_history
from app.api.deps import get_db, get_current_user

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/send", response_model=MessageOut)
def send_message_route(
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return send_message(db, current_user.id, message_in)

@router.get("/history/{user_id}", response_model=list[MessageOut])
def get_message_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_history(db, user_id)