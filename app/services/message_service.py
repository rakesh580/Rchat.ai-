from sqlalchemy.orm import Session
from app.models.message import Message
from app.schemas.message import MessageCreate


def send_message(db: Session, sender_id: int, message_in: MessageCreate):
    msg = Message(
        sender_id=sender_id,
        receiver_id=message_in.receiver_id,
        content=message_in.content
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_history(db: Session, user_id: int):
    return (
        db.query(Message)
        .filter((Message.sender_id == user_id) | (Message.receiver_id == user_id))
        .order_by(Message.timestamp.asc())
        .all()
    )