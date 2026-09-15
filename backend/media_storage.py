"""Private local storage for report media assets.

Files are never mounted as static files: every read must pass the report RBAC
check in the FastAPI route.  Client names and content types are metadata only;
the server derives the storage extension after checking file signatures.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from .config import get_media_storage_root


IMAGE_ASSET_TYPES = {"stone_photo", "plotting_diagram", "instrument_image"}
ASSET_TYPES = IMAGE_ASSET_TYPES | {"supporting_document"}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_SIZE_BYTES = 20 * 1024 * 1024
SAFE_REPORT_ID = re.compile(r"^[A-Za-z0-9-]{1,20}$")


def _detect_media_type(prefix: bytes) -> tuple[str, str] | None:
    if prefix.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if prefix.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if prefix.startswith(b"%PDF-"):
        return "application/pdf", ".pdf"
    return None


def _max_size_for(asset_type: str) -> int:
    return MAX_IMAGE_SIZE_BYTES if asset_type in IMAGE_ASSET_TYPES else MAX_DOCUMENT_SIZE_BYTES


def _validate_asset_kind(asset_type: str, mime_type: str) -> None:
    if asset_type not in ASSET_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported media asset type")
    if asset_type in IMAGE_ASSET_TYPES and not mime_type.startswith("image/"):
        raise HTTPException(status_code=422, detail="This media asset type requires an image")
    if asset_type == "supporting_document" and mime_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Supporting documents must be PDF files")


def store_upload(*, report_id: str, asset_type: str, upload: UploadFile) -> dict[str, object]:
    """Stream, validate and atomically persist one upload under its report id."""
    if not SAFE_REPORT_ID.fullmatch(report_id):
        raise HTTPException(status_code=422, detail="Invalid report identifier for media storage")

    declared_mime = (upload.content_type or "").lower().split(";", maxsplit=1)[0]
    _validate_asset_kind(asset_type, declared_mime)
    root = get_media_storage_root()
    report_directory = (root / report_id).resolve()
    if root != report_directory.parent:
        raise HTTPException(status_code=422, detail="Invalid media storage path")
    report_directory.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=report_directory, delete=False) as temporary_file:
            temp_path = Path(temporary_file.name)
            prefix = b""
            size_bytes = 0
            digest = hashlib.sha256()
            while chunk := upload.file.read(64 * 1024):
                if len(prefix) < 16:
                    prefix += chunk[: 16 - len(prefix)]
                size_bytes += len(chunk)
                if size_bytes > _max_size_for(asset_type):
                    raise HTTPException(status_code=422, detail="Media file exceeds the allowed size")
                digest.update(chunk)
                temporary_file.write(chunk)

        detected = _detect_media_type(prefix)
        if detected is None:
            raise HTTPException(status_code=422, detail="Unsupported or invalid media file")
        detected_mime, extension = detected
        if detected_mime != declared_mime:
            raise HTTPException(status_code=422, detail="Declared media type does not match file content")
        _validate_asset_kind(asset_type, detected_mime)
        if size_bytes == 0:
            raise HTTPException(status_code=422, detail="Media file is empty")

        storage_name = f"{uuid4().hex}{extension}"
        final_path = (report_directory / storage_name).resolve()
        if final_path.parent != report_directory:
            raise HTTPException(status_code=422, detail="Invalid media storage path")
        os.replace(temp_path, final_path)
        temp_path = None
        return {
            "storage_key": str(Path(report_id) / storage_name).replace("\\", "/"),
            "mime_type": detected_mime,
            "size_bytes": size_bytes,
            "sha256": digest.hexdigest(),
            "original_filename": Path(upload.filename or "upload").name[:255],
        }
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def get_storage_path(storage_key: str) -> Path:
    """Resolve a DB-owned key and prevent traversal outside the configured root."""
    root = get_media_storage_root()
    candidate = (root / storage_key).resolve()
    if root not in candidate.parents:
        raise HTTPException(status_code=404, detail="Media file not found")
    return candidate


def remove_stored_file(storage_key: str) -> None:
    get_storage_path(storage_key).unlink(missing_ok=True)
