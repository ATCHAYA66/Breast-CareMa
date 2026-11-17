import torch
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.connection import get_db
from backend.database.models import Diagnosis
from backend.services.diagnosis_service import ai_manager

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns real statistics computed from the database.
    """
    total = db.query(Diagnosis).count()
    us_count = db.query(Diagnosis).filter(Diagnosis.modality == "ultrasound").count()
    mg_count = db.query(Diagnosis).filter(Diagnosis.modality == "mammography").count()
    dual_count = db.query(Diagnosis).filter(Diagnosis.modality == "dual").count()

    benign_count = db.query(Diagnosis).filter(Diagnosis.prediction == "Benign").count()
    malignant_count = db.query(Diagnosis).filter(Diagnosis.prediction == "Malignant").count()
    pending_count = db.query(Diagnosis).filter(Diagnosis.status.in_(["pending", "processing"])).count()

    modality_distribution = [
        {"name": "Ultrasound", "value": us_count, "color": "#6825A8"},
        {"name": "Mammography", "value": mg_count, "color": "#E83E91"},
        {"name": "Dual Scan", "value": dual_count, "color": "#351052"}
    ]

    class_distribution = [
        {"name": "Benign", "value": benign_count, "color": "#16A36A"},
        {"name": "Malignant", "value": malignant_count, "color": "#E5484D"},
        {"name": "Pending", "value": pending_count, "color": "#F59E0B"}
    ]

    # CUDA or CPU device status
    device = "CUDA (GPU Acceleration)" if torch.cuda.is_available() else "CPU Mode"

    ai_engine_status = {
        "device": device,
        "yolov8_ultrasound": {
            "status": "Online",
            "weights_loaded": ai_manager.ultrasound_detector.is_custom_trained,
            "architecture": "YOLOv8 Tumor Detector (BUSI)",
            "state": "Active" if ai_manager.ultrasound_detector.model is not None else "Unavailable"
        },
        "efficientnet_mammography": {
            "status": "Online",
            "weights_loaded": ai_manager.mammography_classifier.is_custom_trained,
            "architecture": "EfficientNetB0 (CBIS-DDSM)",
            "state": "Active"
        },
        "multimodal_fusion": {
            "status": "Online",
            "is_trained": ai_manager.multimodal_fusion.is_trained,
            "architecture": "MLP Feature Fusion (512-US + 1280-MG = 1792)",
            "state": "Active & Calibrated" if ai_manager.multimodal_fusion.is_trained else "Architecture Ready (Awaiting Paired Data)"
        },
        "gradcam_explainability": {
            "status": "Online",
            "target_layer": "backbone.features[-1]",
            "state": "Active"
        }
    }

    return {
        "total_scans": total,
        "ultrasound_scans": us_count,
        "mammography_scans": mg_count,
        "dual_scans": dual_count,
        "modality_distribution": modality_distribution,
        "class_distribution": class_distribution,
        "ai_engine_status": ai_engine_status
    }
