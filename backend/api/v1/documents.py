"""Document management endpoints — upload, download, check status."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.api.dependencies import get_db_session
from backend.core.container import get_container
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# ── File validation constants ────────────────────────────────────

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/jpg",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file(content_type: str, file_size: int) -> None:
    """Validate file MIME type and size. Raises HTTPException on violation."""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": (
                        f"File type '{content_type}' is not allowed. "
                        f"Accepted types: {', '.join(sorted(ALLOWED_MIME_TYPES))}."
                    ),
                    "details": {
                        "allowed_types": sorted(ALLOWED_MIME_TYPES),
                        "received_type": content_type,
                    },
                }
            },
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": (
                        f"File size {file_size} bytes exceeds maximum "
                        f"of {MAX_FILE_SIZE_BYTES} bytes (10 MB)."
                    ),
                    "details": {
                        "max_size_bytes": MAX_FILE_SIZE_BYTES,
                        "received_size_bytes": file_size,
                    },
                }
            },
        )


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Get document metadata by ID."""
    from sqlalchemy import select

    from backend.domain.claims.models import ClaimDocument

    result = await session.execute(
        select(ClaimDocument).where(ClaimDocument.document_id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail={"error": {"message": "Document not found"}})

    return {
        "document_id": doc.document_id,
        "claim_id": doc.claim_id,
        "file_name": doc.file_name,
        "document_type": doc.document_type,
        "detected_type": doc.detected_type,
        "verification_status": doc.verification_status,
        "quality_score": float(doc.quality_score) if doc.quality_score else None,
        "file_size_bytes": doc.file_size_bytes,
        "content_type": doc.content_type,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("/claim/{claim_id}")
async def get_claim_documents(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """List all documents attached to a claim."""
    from sqlalchemy import select

    from backend.domain.claims.models import ClaimDocument

    result = await session.execute(select(ClaimDocument).where(ClaimDocument.claim_id == claim_id))
    docs = result.scalars().all()

    return {
        "claim_id": claim_id,
        "documents": [
            {
                "document_id": d.document_id,
                "file_name": d.file_name,
                "document_type": d.document_type,
                "verification_status": d.verification_status,
                "quality_score": float(d.quality_score) if d.quality_score else None,
                "error_message": d.error_message,
            }
            for d in docs
        ],
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
):
    """Upload a document file to local storage.

    Returns file metadata including file_id and file_path for use in claim submission.
    """
    # Validate file type
    content_type = file.content_type or "application/octet-stream"
    validate_file(content_type, 0)  # 0 = skip size check for upload

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size {file_size} bytes exceeds maximum of {MAX_FILE_SIZE_BYTES} bytes (10 MB).",
                }
            },
        )

    # Upload to storage
    storage = get_container().storage
    stored = await storage.upload(
        file_name=file.filename or "document",
        content=content,
        content_type=content_type,
    )

    logger.info(
        "document_uploaded",
        file_id=stored.file_id,
        file_name=stored.file_name,
        size=stored.size_bytes,
        document_type=document_type,
    )

    return {
        "file_id": stored.file_id,
        "file_name": stored.file_name,
        "file_path": stored.file_path,
        "content_type": stored.content_type,
        "size_bytes": stored.size_bytes,
        "document_type": document_type,
    }


@router.get("/{file_id}/download")
async def download_document(file_id: str):
    """Download a stored document by file_id."""
    storage = get_container().storage
    file_path = f"/uploads/{file_id}"

    if not await storage.exists(file_path):
        raise HTTPException(status_code=404, detail={"error": {"message": "File not found"}})

    content = await storage.download(file_path)
    return Response(content=content, media_type="application/octet-stream")


@router.get("/db/{document_id}/view")
async def view_document_by_db_id(
    document_id: int,
    session: AsyncSession = Depends(get_db_session),
    _current_user=Depends(get_current_user),
):
    """View/download a document's actual file content by database document_id.

    This endpoint serves the actual uploaded file bytes (image, PDF, etc.)
    so the frontend can display document previews.
    """
    from sqlalchemy import select

    from backend.domain.claims.models import ClaimDocument

    result = await session.execute(
        select(ClaimDocument).where(ClaimDocument.document_id == document_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail={"error": {"message": "Document not found"}})

    storage = get_container().storage

    if not await storage.exists(doc.file_path):
        raise HTTPException(status_code=404, detail={"error": {"message": "File not found in storage"}})

    content = await storage.download(doc.file_path)

    # Use the original content_type for proper browser rendering
    media_type = doc.content_type or "application/octet-stream"
    # Sanitize filename for Content-Disposition header (escape double quotes and backslashes)
    safe_filename = doc.file_name.replace("\\", "\\\\").replace('"', '\\"')
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{safe_filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )
