from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.schemas.autopilot import (
    AutopilotSettingsUpdate,
    AutopilotSettingsOut,
    AutopilotBriefingOut,
    AutopilotStatusOut,
)
from app.services.autopilot_service import (
    get_autopilot_settings,
    upsert_autopilot_settings,
    get_briefing,
    mark_briefing_resolved,
)
from app.db.postgres import query_one

router = APIRouter(prefix="/autopilot", tags=["Autopilot"])


@router.get("/settings", response_model=AutopilotSettingsOut)
def read_settings(request: Request, user: dict = Depends(get_current_user)):
    settings = get_autopilot_settings(user["_id"])
    if not settings:
        # Return defaults
        return AutopilotSettingsOut(
            _id="",
            user_id=user["_id"],
            is_active=False,
            away_message="",
            auto_respond_enabled=True,
        )
    return AutopilotSettingsOut(**settings)


@router.put("/settings", response_model=AutopilotSettingsOut)
@limiter.limit("10/minute")
def update_settings(
    request: Request,
    body: AutopilotSettingsUpdate,
    user: dict = Depends(get_current_user),
):
    # Validate backup person exists and is a contact
    if body.backup_person_id:
        contact = query_one(
            "SELECT 1 FROM contacts WHERE user_id = %s AND contact_id = %s",
            (user["_id"], body.backup_person_id),
        )
        if not contact:
            raise HTTPException(status_code=400, detail="Backup person must be in your contacts")

    updates = body.model_dump(exclude_none=False)
    result = upsert_autopilot_settings(user["_id"], updates)
    return AutopilotSettingsOut(**result)


@router.get("/briefing", response_model=AutopilotBriefingOut)
def read_briefing(request: Request, user: dict = Depends(get_current_user)):
    return get_briefing(user["_id"])


@router.post("/briefing/dismiss")
def dismiss_briefing(request: Request, user: dict = Depends(get_current_user)):
    count = mark_briefing_resolved(user["_id"])
    return {"ok": True, "resolved": count}


@router.get("/status/{user_id}", response_model=AutopilotStatusOut)
def check_autopilot_status(
    request: Request,
    user_id: str,
    user: dict = Depends(get_current_user),
):
    row = query_one(
        "SELECT is_active, away_message, expected_return_date FROM autopilot_settings WHERE user_id = %s",
        (user_id,),
    )
    if not row or not row["is_active"]:
        return AutopilotStatusOut(is_autopilot=False)
    return AutopilotStatusOut(
        is_autopilot=True,
        away_message=row.get("away_message", ""),
        expected_return_date=row.get("expected_return_date"),
    )
