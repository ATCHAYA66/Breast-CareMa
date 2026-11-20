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
from backend.services.busi_research_service import run_busi_research_inference
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

    # Verify required image uploads
    if diagnosis.modality in ["ultrasound", "dual"] and "ultrasound" not in img_dict:
        raise HTTPException(status_code=400, detail="Ultrasound scan image is required for this study modality.")
    if diagnosis.modality in ["mammography", "dual"] and "mammography" not in img_dict:
        raise HTTPException(status_code=400, detail="Mammography scan image is required for this study modality.")

    diagnosis.status = "processing"
    db.commit()

    # Clear previous results if re-analyzing
    db.query(ModelResults).filter(ModelResults.study_id == study_id).delete()
    db.commit()

    final_prediction = "Inconclusive"
    final_confidence = None
    birads_cat = "Not assigned by AI system"
    recommended_action = (
        "This is an academic AI output only. No clinical diagnosis or BI-RADS category is assigned. "
        "Please have the original images reviewed by a qualified breast radiologist."
    )
    lesion_area = None
    aspect_ratio = None
    shape = "Not assessed"
    margin = "Not assessed"
    orientation = "Not assessed"
    us_annotated_path = None
    mg_overlay_path = None
    us_result = None
    mg_result = None
    gradcam_result = None
    fusion_result = None

    # Step 1: Ultrasound analysis via verified BUSI models
    if diagnosis.modality in ["ultrasound", "dual"]:
        us_path = img_dict["ultrasound"]
        try:
            busi_result = run_busi_research_inference(image_path=us_path, study_id=study_id)
        except Exception as exc:
            if diagnosis.modality == "ultrasound":
                diagnosis.status = "failed"
                diagnosis.findings_summary = f"BUSI ultrasound inference failed: {exc}"
                db.commit()
                raise HTTPException(status_code=503, detail=f"Ultrasound inference failed: {exc}") from exc
            else:
                busi_result = {
                    "status": "error",
                    "classifier": {"status": "error", "predicted_class": "Error", "confidence": None},
                    "segmentation": {"status": "error", "mask_detected": False, "lesion_area_percentage": None, "mask_overlay_url": None},
                    "error": str(exc)
                }

        clf_out = busi_result.get("classifier", {})
        seg_out = busi_result.get("segmentation", {})
        us_annotated_path = seg_out.get("mask_overlay_url")
        us_confidence = clf_out.get("confidence")
        us_prediction = clf_out.get("predicted_class", "Inconclusive")
        lesion_area = seg_out.get("lesion_area_percentage")
        us_result = busi_result

        # Store Model 1: BUSI EfficientNet-B0 Classifier (3-Class)
        db.add(ModelResults(
            study_id=study_id,
            model_name="BUSI EfficientNet-B0 (3-Class)",
            predicted_class=us_prediction,
            confidence=float(us_confidence) if us_confidence is not None else 0.0,
            output_path=us_annotated_path,
            raw_data=json.dumps({
                "model_type": "busi_classifier",
                "classes": ["Benign", "Malignant", "Normal"],
                "class_probabilities": clf_out.get("class_probabilities"),
                "confidence_type": clf_out.get("confidence_type", "uncalibrated_softmax"),
                "confidence_available": us_confidence is not None,
                "is_custom_trained": True,
            }),
            created_at=datetime.utcnow(),
        ))

        # Store Model 2: BUSI Compact U-Net Segmenter (Binary)
        db.add(ModelResults(
            study_id=study_id,
            model_name="BUSI Compact U-Net (Binary)",
            predicted_class="Lesion Detected" if seg_out.get("mask_detected") else "No Lesion Mask",
            confidence=float(lesion_area) if lesion_area is not None else 0.0,
            output_path=us_annotated_path,
            raw_data=json.dumps({
                "model_type": "busi_segmenter",
                "mask_detected": seg_out.get("mask_detected", False),
                "lesion_area_percentage": lesion_area,
                "threshold": seg_out.get("threshold", 0.5),
                "interpretation": seg_out.get("interpretation", ""),
                "is_custom_trained": True,
            }),
            created_at=datetime.utcnow(),
        ))

        # Store Audit Entry: YOLOv8 Decommissioned Record
        db.add(ModelResults(
            study_id=study_id,
            model_name="YOLOv8 Tumor Detector (Audited / Decommissioned)",
            predicted_class="Decommissioned – Generic COCO Weights",
            confidence=0.0,
            output_path=None,
            raw_data=json.dumps({
                "audit_status": "decommissioned",
                "audit_finding": "Weights file 'best.pt' contains 80 standard COCO classes (e.g. person, car). Not trained on breast lesions. Decommissioned to prevent false clinical reliance.",
                "replacement": "BUSI EfficientNet-B0 & Compact U-Net",
                "is_custom_trained": False,
                "confidence_available": False,
            }),
            created_at=datetime.utcnow(),
        ))

    # Step 2: Mammography analysis + Grad-CAM (existing pipeline retained)
    if diagnosis.modality in ["mammography", "dual"]:
        mg_path = img_dict["mammography"]
        try:
            mg_result = ai_manager.mammography_classifier.predict(mg_path)
            gradcam_result = ai_manager.gradcam.generate(mg_path, study_id)
            mg_overlay_path = gradcam_result["overlay_path"]
            
            db.add(ModelResults(
                study_id=study_id,
                model_name="EfficientNetB0 Classifier",
                predicted_class=mg_result["predicted_class"],
                confidence=mg_result["confidence"],
                output_path=gradcam_result["overlay_path"],
                raw_data=json.dumps({
                    "probabilities": mg_result["probabilities"],
                    "gradcam_heatmap": gradcam_result["heatmap_path"],
                    "hotspot": gradcam_result["hotspot"],
                    "is_custom_trained": mg_result["is_custom_trained"],
                }),
                created_at=datetime.utcnow(),
            ))
        except Exception as exc:
            if diagnosis.modality == "mammography":
                diagnosis.status = "failed"
                diagnosis.findings_summary = f"Mammography inference failed: {exc}"
                db.commit()
                raise HTTPException(status_code=503, detail=f"Mammography inference failed: {exc}") from exc
            else:
                mg_result = {"status": "error", "predicted_class": "Error", "confidence": 0.0, "error": str(exc)}
                db.add(ModelResults(
                    study_id=study_id,
                    model_name="EfficientNetB0 Classifier",
                    predicted_class="Error / Failed",
                    confidence=0.0,
                    output_path=None,
                    raw_data=json.dumps({"error": str(exc), "status": "error"}),
                    created_at=datetime.utcnow(),
                ))

    # Step 3: Dual-modality correlation (Strict: Independent presentation, NO black-box fusion)
    if diagnosis.modality == "dual":
        us_summary = f"Ultrasound (BUSI): {us_prediction} (Score: {us_confidence*100:.1f}%)" if us_confidence else f"Ultrasound (BUSI): {us_prediction}"
        mg_summary = f"Mammography: {mg_result.get('predicted_class')} (Conf: {mg_result.get('confidence', 0)*100:.1f}%)" if mg_result and mg_result.get('confidence') else "Mammography: Failed/Unavailable"
        
        db.add(ModelResults(
            study_id=study_id,
            model_name="Dual Scan (Independent Correlation)",
            predicted_class=f"US: {us_prediction} | MG: {mg_result.get('predicted_class', 'N/A')}",
            confidence=0.0,
            output_path=None,
            raw_data=json.dumps({
                "mode": "independent_correlation",
                "ultrasound_summary": us_summary,
                "mammography_summary": mg_summary,
                "fused_diagnosis": False,
                "academic_notice": "Independent side-by-side evaluation. No artificial black-box fusion score is fabricated.",
            }),
            created_at=datetime.utcnow(),
        ))

    # Formulate final diagnostic output
    if diagnosis.modality == "ultrasound":
        final_prediction = us_prediction
        final_confidence = us_confidence
        findings_text = (
            f"BUSI Ultrasound Analysis: Predicted '{final_prediction}' with "
            + (f"{final_confidence * 100:.1f}% uncalibrated model score. " if final_confidence is not None else "")
            + (f"Lesion coverage: {lesion_area:.2f}%." if lesion_area else "No focal lesion mask detected.")
        )
    elif diagnosis.modality == "mammography":
        final_prediction = mg_result.get("predicted_class", "Inconclusive")
        final_confidence = mg_result.get("confidence")
        findings_text = (
            f"Mammography Analysis (CBIS-DDSM): Predicted '{final_prediction}' with "
            + (f"{final_confidence * 100:.1f}% confidence." if final_confidence is not None else "")
            + " Grad-CAM activation heatmap generated."
        )
    else:  # dual
        final_prediction = "Dual Examination (Independent Findings)"
        final_confidence = None  # Strictly no fabricated single combined score
        findings_text = (
            f"Dual Scan Independent Correlation: "
            f"Ultrasound (BUSI): {us_prediction} (Uncalibrated Score: {us_confidence*100:.1f}% if us_confidence else 'N/A'); "
            f"Mammography: {mg_result.get('predicted_class', 'Error')} (Confidence: {mg_result.get('confidence', 0)*100:.1f}%). "
            f"Independent side-by-side correlation without black-box fusion."
        )

    birads_cat = "Not assigned by AI system"
    recommended_action = (
        "AI output is for academic research only. It does not establish or exclude cancer and does not assign BI-RADS. "
        "A qualified breast radiologist must interpret the original images and determine any required follow-up."
    )

    diagnosis.prediction = final_prediction
    diagnosis.confidence = round(float(final_confidence), 4) if final_confidence is not None else None
    diagnosis.birads_category = birads_cat
    diagnosis.recommended_action = recommended_action
    diagnosis.lesion_area = lesion_area
    diagnosis.aspect_ratio = None
    diagnosis.margin = "Assessed via U-Net contour" if lesion_area else "Not assessed"
    diagnosis.orientation = "Not assessed"
    diagnosis.findings_summary = findings_text
    diagnosis.status = "completed"
    print(f"[Diagnosis Service] Study {study_id} completed. Modality: {diagnosis.modality} | Prediction: {final_prediction} | Confidence: {final_confidence}")
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
            "lesion_area_px": lesion_area,
            "aspect_ratio": aspect_ratio,
            "shape": shape,
            "margin": margin,
            "orientation": orientation
        },
        "us_annotated_path": us_annotated_path,
        "mg_overlay_path": mg_overlay_path,
        "birads_evidence": (
            "No BI-RADS category is generated by this research model. "
            "Bounding-box geometry, when available, is not a clinical morphology assessment."
        ),
        "detection_status": us_result.get("detection_status") if us_result else "not_applicable",
        "confidence_available": final_confidence is not None
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
