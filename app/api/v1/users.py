import os
import uuid
from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, HTTPException

from app.api.deps import get_current_user
from app.services.contact_service import search_users
from app.services.user_service import update_user_profile
from app.schemas.user import UserProfileUpdate
from app.core.rate_limit import limiter
from app.utils.file_validation import validate_image_magic

router = APIRouter(prefix="/users", tags=["Users"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "avatars")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    user = current_user.copy()
    user["_id"] = str(user["_id"])
    user.pop("hashed_password", None)
    return user


@router.put("/me")
def update_me(body: UserProfileUpdate, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    updates = body.model_dump(exclude_none=True)
    updated = update_user_profile(user_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    updated["_id"] = str(updated["_id"])
    updated.pop("hashed_password", None)
    return updated


@router.post("/me/avatar")
@limiter.limit("10/minute")
def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")

    # Read in chunks to avoid OOM on large uploads
    chunks = []
    total_size = 0
    while True:
        chunk = file.file.read(1024 * 1024)  # 1MB chunks
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_AVATAR_SIZE:
            raise HTTPException(status_code=400, detail="Image must be under 5MB")
        chunks.append(chunk)
    contents = b"".join(chunks)

    if not validate_image_magic(contents):
        raise HTTPException(status_code=400, detail="File content does not match a valid image format")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    avatar_url = f"/uploads/avatars/{filename}"
    user_id = str(current_user["_id"])

    # Delete old avatar file if it exists
    old_url = current_user.get("avatar_url", "")
    if old_url and old_url.startswith("/uploads/avatars/"):
        old_path = os.path.join(UPLOAD_DIR, old_url.split("/")[-1])
        if os.path.exists(old_path):
            os.remove(old_path)

    updated = update_user_profile(user_id, {"avatar_url": avatar_url})
    updated["_id"] = str(updated["_id"])
    updated.pop("hashed_password", None)
    return updated


@router.get("/search")
@limiter.limit("30/minute")
def search(request: Request, q: str = Query(..., min_length=1), current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return search_users(q, user_id)
