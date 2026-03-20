# Magic number signatures for allowed file types
MAGIC_NUMBERS = {
    # Images
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp",  # WebP starts with RIFF....WEBP
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    # Videos
    b"\x00\x00\x00\x18ftypmp4": "mp4",
    b"\x00\x00\x00\x1cftypmp4": "mp4",
    b"\x00\x00\x00\x20ftypmp4": "mp4",
    b"\x00\x00\x00\x18ftypisom": "mp4",
    b"\x00\x00\x00\x1cftypisom": "mp4",
    b"\x1aE\xdf\xa3": "webm",
}

IMAGE_SIGNATURES = {b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF", b"GIF87a", b"GIF89a"}
VIDEO_SIGNATURES = {
    b"\x00\x00\x00\x18ftypmp4", b"\x00\x00\x00\x1cftypmp4",
    b"\x00\x00\x00\x20ftypmp4", b"\x00\x00\x00\x18ftypisom",
    b"\x00\x00\x00\x1cftypisom", b"\x1aE\xdf\xa3",
}


def validate_image_magic(data: bytes) -> bool:
    """Check if file content starts with a known image magic number."""
    for sig in IMAGE_SIGNATURES:
        if data[:len(sig)] == sig:
            # Extra check for WebP: RIFF....WEBP
            if sig == b"RIFF":
                return len(data) >= 12 and data[8:12] == b"WEBP"
            return True
    return False


def validate_video_magic(data: bytes) -> bool:
    """Check if file content starts with a known video magic number."""
    if len(data) < 8:
        return False
    # MP4/MOV: ftyp box — box type must be at offset 4
    if data[4:8] == b"ftyp" and len(data) >= 12:
        return True
    # WebM: starts with EBML header
    if data[:4] == b"\x1aE\xdf\xa3":
        return True
    # MOV variants: moov, mdat, wide, free atoms at offset 4
    if data[4:8] in (b"moov", b"mdat", b"wide", b"free"):
        return True
    return False
