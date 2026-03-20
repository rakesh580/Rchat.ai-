from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.schemas.conversation import ConversationCreate, GroupMemberAdd
from app.services.conversation_service import (
    get_or_create_direct,
    create_group,
    get_user_conversations,
    get_conversation_by_id,
    get_conversation_with_profiles,
    add_member_to_group,
    remove_member_from_group,
)
from app.services.message_service import get_messages
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("")
@limiter.limit("30/minute")
def list_conversations(request: Request, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return get_user_conversations(user_id)


@router.post("")
@limiter.limit("10/minute")
def create_conversation(request: Request, body: ConversationCreate, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])

    if body.type == "direct":
        if len(body.participant_ids) != 1:
            raise HTTPException(status_code=400, detail="Direct chat needs exactly 1 other participant")
        other_id = body.participant_ids[0]
        # Verify the other user exists
        other_user = get_user_by_id(other_id)
        if not other_user:
            raise HTTPException(status_code=404, detail="User not found")
        return get_or_create_direct(user_id, other_id)

    elif body.type == "group":
        if not body.group_name:
            raise HTTPException(status_code=400, detail="Group name is required")
        if len(body.participant_ids) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 participants allowed")
        return create_group(user_id, body.participant_ids, body.group_name)

    raise HTTPException(status_code=400, detail="Invalid type")


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, current_user=Depends(get_current_user)):
    convo = get_conversation_by_id(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    user_id = str(current_user["_id"])
    if user_id not in convo["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant")
    return convo


@router.get("/{conversation_id}/messages")
@limiter.limit("60/minute")
def get_conversation_messages(
    request: Request,
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    convo = get_conversation_by_id(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    user_id = str(current_user["_id"])
    if user_id not in convo["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant")
    return get_messages(conversation_id, skip, limit)


@router.post("/{conversation_id}/members")
def add_group_member(
    conversation_id: str,
    body: GroupMemberAdd,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    convo = get_conversation_by_id(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo["type"] != "group":
        raise HTTPException(status_code=400, detail="Not a group conversation")
    if user_id not in convo.get("admins", []):
        raise HTTPException(status_code=403, detail="Only admins can add members")

    # Verify the user being added actually exists
    target_user = get_user_by_id(body.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    added = add_member_to_group(conversation_id, body.user_id)
    if not added:
        raise HTTPException(status_code=400, detail="User already a member or not found")
    return get_conversation_with_profiles(conversation_id)


@router.delete("/{conversation_id}/members/{member_id}")
def remove_group_member(
    conversation_id: str,
    member_id: str,
    current_user=Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    convo = get_conversation_by_id(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo["type"] != "group":
        raise HTTPException(status_code=400, detail="Not a group conversation")
    # Admin can remove anyone, or user can leave themselves
    if user_id not in convo.get("admins", []) and user_id != member_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    removed = remove_member_from_group(conversation_id, member_id)
    if not removed:
        raise HTTPException(status_code=400, detail="User not a member")
    return get_conversation_with_profiles(conversation_id)
