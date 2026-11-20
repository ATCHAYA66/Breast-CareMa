"""Isolated API router for academic BUSI research models.
Does not alter or interfere with production YOLOv8 or patient diagnosis endpoints.
"""
import logging
from pathlib import Path
from typing import Optional
import re
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from backend.config import UPLOADS_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from backend.schemas.research import BUSIResearchResponse
from backend.services.busi_research_service import run_busi_research_inference
from backend.ai_models.busi_models import get_busi_classifier, get_busi_segmenter

logger = logging.getLogger("breast_care_ma.busi_api")
router = APIRouter(prefix="/api/research", tags=["Academic Research Models"])

RESEARCH_UPLOADS_DIR = UPLOADS_DIR / "research"
RESEARCH_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_study_id(raw_id: Optional[str]) -> str:
    """Sanitizes study_id against path traversal attacks (e.g. ../../) and limits length."""
    if not raw_id:
        return f"busi_{uuid.uuid4().hex[:8]}"
    # Strip any directory path components and allow only safe characters
    cleaned = Path(raw_id).name
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "", cleaned)
    if not cleaned:
        return f"busi_{uuid.uuid4().hex[:8]}"
    return cleaned[:64]


@router.get("/busi/status")
def get_busi_model_status():
    """Returns load status and configuration of isolated BUSI research models."""
    clf = get_busi_classifier()
    seg = get_busi_segmenter()
    return {
        "status": "ready" if (clf.is_loaded and seg.is_loaded) else "partially_ready",
        "models": {
            "classifier": {
                "name": "BUSI EfficientNet-B0 (3-Class)",
                "loaded": clf.is_loaded,
                "weights_exists": clf.weights_path.is_file(),
                "classes": clf.class_names,
                "device": str(clf.device),
                "error": clf.error_message,
            },
            "segmenter": {
                "name": "BUSI Compact U-Net (Binary)",
                "loaded": seg.is_loaded,
                "weights_exists": seg.weights_path.is_file(),
                "threshold": seg.threshold,
                "device": str(seg.device),
                "error": seg.error_message,
            },
        },
        "purpose": "Academic research and comparative model evaluation only.",
    }


@router.post("/busi/analyze", response_model=BUSIResearchResponse)
def analyze_busi_research(
    file: UploadFile = File(..., description="Ultrasound scan image file (.jpg, .jpeg, .png, .bmp)"),
    study_id: Optional[str] = Form(None, description="Optional study ID for traceability"),
):
    """Executes isolated BUSI classifier and U-Net segmenter on an uploaded ultrasound scan.
    Returns independent classifier predictions, segmentation mask, and area measurements.
    """
    print(f"[Research API] Received request for file: {file.filename}, study_id: {study_id}")
    # 1. Validate file extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 2. Assign unique research filename and study ID with path traversal prevention
    safe_study_id = sanitize_study_id(study_id)
    unique_filename = f"{safe_study_id}_{uuid.uuid4().hex[:6]}{ext}"
    dest_path = (RESEARCH_UPLOADS_DIR / unique_filename).resolve()
    if not str(dest_path).startswith(str(RESEARCH_UPLOADS_DIR.resolve())):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid study ID: path traversal detected.",
        )

    # 3. Read and validate file size
    try:
        contents = file.file.read()
        print(f"[Research API] Read {len(contents)} bytes")
    except Exception as exc:
        logger.error("[BUSI File Read Error] %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file.",
        )

    file_size = len(contents)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
        )
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    try:
        with open(dest_path, "wb") as out_file:
            out_file.write(contents)
    except Exception as exc:
        logger.error("[BUSI File Save Error] %s", exc)
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded image file.",
        )

    # 4. Run isolated research inference
    try:
        result = run_busi_research_inference(
            image_path=dest_path,
            study_id=safe_study_id,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as exc:
        logger.error("[BUSI Research Analysis Failure] %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while executing the research inference models.",
        )
