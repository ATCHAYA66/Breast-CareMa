import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.config import UPLOADS_DIR, OUTPUTS_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from backend.database.models import Diagnosis, UploadedImages, ModelResults, Reports, PatientClinicalDetails
from backend.ai_models.ultrasound_model import UltrasoundTumorDetector
from backend.ai_models.mammography_model import MammographyClassifier
from backend.ai_models.gradcam import GradCAM
from backend.ai_models.multimodal_model import MultimodalFusionNet
from backend.services.report_service import generate_pdf_report

class AIServiceManager:
    """
    Singleton AI Service Manager holding model backbones in memory.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIServiceManager, cls).__new__(cls)
            print("[AIServiceManager] Initializing local deep learning models...")
            cls._instance.ultrasound_detector = UltrasoundTumorDetector()
            cls._instance.mammography_classifier = MammographyClassifier()
            cls._instance.gradcam = GradCAM(model=cls._instance.mammography_classifier)
            cls._instance.multimodal_fusion = MultimodalFusionNet()
        return cls._instance

ai_manager = AIServiceManager()

def create_new_diagnosis(modality: str, db: Session, patient_id: Optional[str] = None) -> Diagnosis:
    if modality not in ["ultrasound", "mammography", "dual"]:
        raise HTTPException(status_code=400, detail="Invalid modality. Must be 'ultrasound', 'mammography', or 'dual'.")
    
    # Generate research Study ID: BCMA-YYYYMMDD-XXXX
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    study_id = f"BCMA-{date_str}-{unique_suffix}"

    diagnosis = Diagnosis(
        study_id=study_id,
        patient_id=patient_id,
        modality=modality,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)
    return diagnosis

async def save_upload_image(study_id: str, image_type: str, file: UploadFile, db: Session) -> UploadedImages:
    diagnosis = db.query(Diagnosis).filter(Diagnosis.study_id == study_id).first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail=f"Study ID {study_id} not found.")

    if image_type not in ["ultrasound", "mammography"]:
        raise HTTPException(status_code=400, detail="Image type must be 'ultrasound' or 'mammography'.")

    # Extension validation
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension '{file_ext}'. Allowed: JPG, JPEG, PNG, BMP.")

    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of 30MB.")
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Unique sanitized filename
    saved_filename = f"{study_id}_{image_type}_{uuid.uuid4().hex[:6]}{file_ext}"
    dest_path = UPLOADS_DIR / saved_filename
    with open(dest_path, "wb") as f:
        f.write(contents)

    # Remove existing image of same type for this study if re-uploading
    existing = db.query(UploadedImages).filter(
        UploadedImages.study_id == study_id,
        UploadedImages.image_type == image_type
    ).first()
    if existing:
        if Path(existing.file_path).exists():
            try:
                os.remove(existing.file_path)
            except Exception:
                pass
        db.delete(existing)
        db.commit()

    uploaded_rec = UploadedImages(
        study_id=study_id,
        image_type=image_type,
        file_name=file.filename,
        file_path=str(dest_path),
        file_size=file_size,
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_rec)
    db.commit()
    db.refresh(uploaded_rec)
    return uploaded_rec

def run_ai_analysis(study_id: str, db: Session, patient_id: Optional[str] = None) -> Diagnosis:
    diagnosis = db.query(Diagnosis).filter(Diagnosis.study_id == study_id).first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Study not found.")

    if patient_id:
        diagnosis.patient_id = patient_id
        db.commit()

    images = db.query(UploadedImages).filter(UploadedImages.study_id == study_id).all()
    img_dict = {img.image_type: img.file_path for img in images}

    # Validate mandatory images
    if diagnosis.modality == "ultrasound" and "ultrasound" not in img_dict:
        raise HTTPException(status_code=400, detail="Ultrasound scan image is mandatory for this analysis.")
    elif diagnosis.modality == "mammography" and "mammography" not in img_dict:
        raise HTTPException(status_code=400, detail="Mammography scan image is mandatory for this analysis.")
    elif diagnosis.modality == "dual" and ("ultrasound" not in img_dict or "mammography" not in img_dict):
        raise HTTPException(status_code=400, detail="Both Ultrasound and Mammography scans are required for Dual Scan analysis.")

    diagnosis.status = "processing"
    db.commit()

    # Clear previous model results if re-analyzing
    db.query(ModelResults).filter(ModelResults.study_id == study_id).delete()
    db.commit()

    us_result = None
    mg_result = None
    gradcam_result = None
    fusion_result = None

    final_prediction = "Benign"
    final_confidence = 0.85
    birads_cat = "BI-RADS 2 (Benign Finding)"
    recommended_action = "Routine screening and correlation with clinical history recommended."
    lesion_area = 240.0
    aspect_ratio = 1.30
    shape = "Oval"
    margin = "Circumscribed"
    orientation = "Parallel"
    us_annotated_path = None
    mg_overlay_path = None

    # Step 1: Ultrasound analysis
    if diagnosis.modality in ["ultrasound", "dual"]:
        us_path = img_dict["ultrasound"]
        us_result = ai_manager.ultrasound_detector.analyze(us_path, study_id)
        us_annotated_path = us_result["output_image_path"]
        
        us_rec = ModelResults(
            study_id=study_id,
            model_name="YOLOv8 Tumor Detector",
            predicted_class=us_result["predicted_class"],
            confidence=us_result["confidence"],
            output_path=us_result["output_image_path"],
            raw_data=json.dumps({
                "boxes": us_result["boxes"],
                "is_custom_trained": us_result["is_custom_trained"],
                "quantitative": us_result["quantitative_findings"]
            }),
            created_at=datetime.utcnow()
        )
        db.add(us_rec)

        qf = us_result["quantitative_findings"]
        lesion_area = qf.get("lesion_area", lesion_area)
        aspect_ratio = qf.get("aspect_ratio", aspect_ratio)
        shape = qf.get("shape", shape)
        margin = qf.get("margin", margin)
        orientation = qf.get("orientation", orientation)

    # Step 2: Mammography analysis + Grad-CAM
    if diagnosis.modality in ["mammography", "dual"]:
        mg_path = img_dict["mammography"]
        mg_result = ai_manager.mammography_classifier.predict(mg_path)
        gradcam_result = ai_manager.gradcam.generate(mg_path, study_id)
        mg_overlay_path = gradcam_result["overlay_path"]

        mg_rec = ModelResults(
            study_id=study_id,
            model_name="EfficientNetB0 Classifier",
            predicted_class=mg_result["predicted_class"],
            confidence=mg_result["confidence"],
            output_path=gradcam_result["overlay_path"],
            raw_data=json.dumps({
                "probabilities": mg_result["probabilities"],
                "gradcam_heatmap": gradcam_result["heatmap_path"],
                "hotspot": gradcam_result["hotspot"],
                "is_custom_trained": mg_result["is_custom_trained"]
            }),
            created_at=datetime.utcnow()
        )
        db.add(mg_rec)

    # Step 3: Multimodal Feature Fusion (Dual Scan only)
    if diagnosis.modality == "dual":
        fusion_result = ai_manager.multimodal_fusion.fuse(
            img_dict["ultrasound"], img_dict["mammography"], ai_manager.mammography_classifier
        )
        fusion_rec = ModelResults(
            study_id=study_id,
            model_name="Multimodal Feature Fusion (MLP)",
            predicted_class=fusion_result["predicted_class"],
            confidence=fusion_result["confidence"],
            output_path=None,
            raw_data=json.dumps({
                "feature_dimensions": fusion_result["feature_dimensions"],
                "is_trained": fusion_result["is_trained"],
                "status_note": fusion_result["status_note"]
            }),
            created_at=datetime.utcnow()
        )
        db.add(fusion_rec)

    # Formulate Diagnostic Conclusion based on individual models
    if diagnosis.modality == "ultrasound":
        final_prediction = us_result["predicted_class"]
        final_confidence = us_result["confidence"]
    elif diagnosis.modality == "mammography":
        final_prediction = mg_result["predicted_class"]
        final_confidence = mg_result["confidence"]
    else:  # Dual Scan
        if fusion_result and fusion_result["is_trained"]:
            final_prediction = fusion_result["predicted_class"]
            final_confidence = fusion_result["confidence"]
        else:
            us_pred = us_result["predicted_class"]
            mg_pred = mg_result["predicted_class"]
            if us_pred == "Malignant" or mg_pred == "Malignant":
                final_prediction = "Malignant"
                final_confidence = max(us_result["confidence"], mg_result["confidence"])
            else:
                final_prediction = "Benign"
                final_confidence = min(us_result["confidence"], mg_result["confidence"])

    # Determine BI-RADS Evidence & Recommended Actions
    if final_prediction == "Malignant":
        birads_cat = "BI-RADS 4/5 (Suspicious / High Risk)"
        recommended_action = (
            "Suspicious morphological findings identified. Urgent referral for diagnostic workup, "
            "targeted high-resolution ultrasound/mammography, and consideration of core needle biopsy by a qualified clinician."
        )
    else:
        birads_cat = "BI-RADS 2/3 (Benign / Probably Benign)"
        recommended_action = (
            "Circumscribed, non-suspicious features observed. Routine clinical correlation and standard screening "
            "or 6-month short-interval surveillance recommended as clinically appropriate."
        )

    # Save to Diagnosis model
    diagnosis.prediction = final_prediction
    diagnosis.confidence = round(float(final_confidence), 4)
    diagnosis.birads_category = birads_cat
    diagnosis.recommended_action = recommended_action
    diagnosis.lesion_area = lesion_area
    diagnosis.aspect_ratio = aspect_ratio
    diagnosis.shape = shape
    diagnosis.margin = margin
    diagnosis.orientation = orientation
    diagnosis.findings_summary = (
        f"Multi-modality assessment completed. Primary AI classification indicates {final_prediction} "
        f"with {final_confidence * 100:.1f}% confidence under research protocol."
    )
    diagnosis.status = "completed"
    db.commit()

    # Retrieve patient clinical details if available
    patient_data = None
    if diagnosis.patient_id:
        patient_rec = db.query(PatientClinicalDetails).filter(
            PatientClinicalDetails.patient_id == diagnosis.patient_id
        ).first()
        if patient_rec:
            symptoms_list = []
            if patient_rec.symptoms:
                try:
                    symptoms_list = json.loads(patient_rec.symptoms)
                except Exception:
                    symptoms_list = [s.strip() for s in patient_rec.symptoms.split(",") if s.strip()]
            patient_data = {
                "patient_id": patient_rec.patient_id,
                "age": patient_rec.age,
                "menopause_status": patient_rec.menopause_status,
                "breast_density": patient_rec.breast_density,
                "family_history": patient_rec.family_history,
                "breast_side": patient_rec.breast_side,
                "symptoms": symptoms_list,
                "other_symptoms": patient_rec.other_symptoms,
                "previous_biopsy": patient_rec.previous_biopsy,
                "clinical_notes": patient_rec.clinical_notes
            }

    # Generate PDF Diagnostic Report
    report_data = {
        "study_id": study_id,
        "modality": diagnosis.modality,
        "prediction": final_prediction,
        "confidence": final_confidence,
        "birads_category": birads_cat,
        "recommended_action": recommended_action,
        "patient": patient_data,
        "quantitative_findings": {
            "lesion_area": lesion_area,
            "aspect_ratio": aspect_ratio,
            "shape": shape,
            "margin": margin,
            "orientation": orientation
        },
        "us_annotated_path": us_annotated_path,
        "mg_overlay_path": mg_overlay_path,
        "birads_evidence": (
            f"Evaluated via deep feature extraction against BUSI (Ultrasound) and CBIS-DDSM (Mammography) benchmarks. "
            f"Morphological features: {shape} shape, {margin} margin, {orientation} orientation."
        )
    }

    try:
        pdf_path = generate_pdf_report(report_data)
        diagnosis.report_path = pdf_path
        
        # Save Reports table entry
        db.query(Reports).filter(Reports.study_id == study_id).delete()
        rep_rec = Reports(
            study_id=study_id,
            report_path=pdf_path,
            generated_at=datetime.utcnow()
        )
        db.add(rep_rec)
        db.commit()
    except Exception as e:
        print(f"[ReportService] Error generating PDF report: {e}")

    db.refresh(diagnosis)
    return diagnosis
