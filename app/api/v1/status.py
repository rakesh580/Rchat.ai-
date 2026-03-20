import os
import uuid
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from typing import Optional

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.utils.file_validation import validate_image_magic, validate_video_magic
from app.services.status_service import (
    create_status,
    get_my_statuses,
    get_status_feed,
    mark_status_viewed,
    delete_status,
)

router = APIRouter(prefix="/status", tags=["Status"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "status")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_VIDEO_EXTS = {"mp4", "webm", "mov"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10MB
MAX_VIDEO_SIZE = 30 * 1024 * 1024   # 30MB


@router.post("")
@limiter.limit("10/minute")
def post_status(
    request: Request,
    type: str = Form(...),
    content: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    background_color: Optional[str] = Form("#6C5CE7"),
    file: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user),
):
    user_id = str(current_user["_id"])

    if type == "text":
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="Text status requires content")
        status = create_status(
            user_id=user_id,
            status_type="text",
            content=content.strip(),
            background_color=background_color,
        )
        return status

    if type in ("image", "video"):
        if not file:
            raise HTTPException(status_code=400, detail=f"{type.title()} status requires a file")

        if type == "image":
            if file.content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed")
            max_size = MAX_IMAGE_SIZE
        else:
            if file.content_type not in ALLOWED_VIDEO_TYPES:
                raise HTTPException(status_code=400, detail="Only MP4, WebM, and MOV videos are allowed")
            max_size = MAX_VIDEO_SIZE

        # Read in chunks to avoid OOM on large uploads
        chunks = []
        total_size = 0
        while True:
            chunk = file.file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_size:
                raise HTTPException(status_code=400, detail=f"File must be under {max_size // (1024*1024)}MB")
            chunks.append(chunk)
        contents = b"".join(chunks)

        # Validate file magic numbers
        if type == "image" and not validate_image_magic(contents):
            raise HTTPException(status_code=400, detail="File content does not match a valid image format")
        if type == "video" and not validate_video_magic(contents):
            raise HTTPException(status_code=400, detail="File content does not match a valid video format")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ("jpg" if type == "image" else "mp4")
        allowed_exts = ALLOWED_IMAGE_EXTS if type == "image" else ALLOWED_VIDEO_EXTS
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail="Invalid file extension")
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(contents)

        media_url = f"/uploads/status/{filename}"
        status = create_status(
            user_id=user_id,
            status_type=type,
            media_url=media_url,
            caption=caption.strip() if caption else None,
        )
        return status

    raise HTTPException(status_code=400, detail="Invalid status type")


@router.get("/me")
def my_statuses(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return get_my_statuses(user_id)


@router.get("/feed")
def status_feed(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return get_status_feed(user_id)


@router.post("/{status_id}/view")
def view_status(status_id: str, current_user=Depends(get_current_user)):
    viewer_id = str(current_user["_id"])
    mark_status_viewed(status_id, viewer_id)
    return {"ok": True}


@router.delete("/{status_id}")
def remove_status(status_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    deleted = delete_status(status_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Status not found")
    return {"ok": True}
