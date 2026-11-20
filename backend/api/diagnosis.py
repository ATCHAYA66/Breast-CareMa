import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.connection import get_db
from backend.database.models import Diagnosis, UploadedImages, ModelResults, PatientClinicalDetails
from backend.schemas.diagnosis import DiagnosisCreate, DiagnosisResponse, DiagnosisHistoryItem, UploadedImageResponse, ModelResultResponse
from backend.services.diagnosis_service import create_new_diagnosis, save_upload_image, run_ai_analysis

router = APIRouter(prefix="/api/diagnosis", tags=["Diagnosis"])

def format_diagnosis_response(diag: Diagnosis, db: Session = None) -> dict:
    images_list = []
    for img in diag.images:
        images_list.append({
            "id": img.id,
            "study_id": img.study_id,
            "image_type": img.image_type,
            "file_name": img.file_name,
            "file_url": f"/uploads/{Path(img.file_path).name}",
            "file_size": img.file_size,
            "uploaded_at": img.uploaded_at
        })

    model_res_list = []
    for mr in diag.model_results:
        raw_obj = {}
        if mr.raw_data:
            try:
                raw_obj = json.loads(mr.raw_data)
            except Exception:
                raw_obj = {}

        model_res_list.append({
            "id": mr.id,
            "model_name": mr.model_name,
            "predicted_class": mr.predicted_class,
            "confidence": (
                mr.confidence
                if raw_obj.get("confidence_available", True)
                else None
            ),
            "output_url": f"/outputs/{Path(mr.output_path).name}" if mr.output_path else None,
            "raw_data": raw_obj,
            "created_at": mr.created_at
        })

    # Patient details
    patient_data = None
    if diag.patient:
        p = diag.patient
        symptoms_list = []
        if p.symptoms:
            try:
                symptoms_list = json.loads(p.symptoms)
            except Exception:
                symptoms_list = [s.strip() for s in p.symptoms.split(",") if s.strip()]
        patient_data = {
            "id": p.id,
            "patient_id": p.patient_id,
            "age": p.age,
            "menopause_status": p.menopause_status,
            "breast_density": p.breast_density,
            "family_history": p.family_history,
            "breast_side": p.breast_side,
            "symptoms": symptoms_list,
            "other_symptoms": p.other_symptoms,
            "previous_biopsy": p.previous_biopsy,
            "clinical_notes": p.clinical_notes,
            "created_at": p.created_at,
            "updated_at": p.updated_at
        }
    elif diag.patient_id and db:
        p = db.query(PatientClinicalDetails).filter(PatientClinicalDetails.patient_id == diag.patient_id).first()
        if p:
            symptoms_list = []
            if p.symptoms:
                try:
                    symptoms_list = json.loads(p.symptoms)
                except Exception:
                    symptoms_list = [s.strip() for s in p.symptoms.split(",") if s.strip()]
            patient_data = {
                "id": p.id,
                "patient_id": p.patient_id,
                "age": p.age,
                "menopause_status": p.menopause_status,
                "breast_density": p.breast_density,
                "family_history": p.family_history,
                "breast_side": p.breast_side,
                "symptoms": symptoms_list,
                "other_symptoms": p.other_symptoms,
                "previous_biopsy": p.previous_biopsy,
                "clinical_notes": p.clinical_notes,
                "created_at": p.created_at,
                "updated_at": p.updated_at
            }

    report_url = f"/api/reports/{diag.study_id}/pdf" if diag.report_path else None

    return {
        "id": diag.id,
        "study_id": diag.study_id,
        "patient_id": diag.patient_id,
        "modality": diag.modality,
        "created_at": diag.created_at,
        "status": diag.status,
        "prediction": diag.prediction,
        "confidence": diag.confidence,
        "report_path": diag.report_path,
        "report_url": report_url,
        "birads_category": diag.birads_category,
        "recommended_action": diag.recommended_action,
        "lesion_area": diag.lesion_area,
        "aspect_ratio": diag.aspect_ratio,
        "margin": diag.margin,
        "orientation": diag.orientation,
        "findings_summary": diag.findings_summary,
        "patient": patient_data,
        "images": images_list,
        "model_results": model_res_list
    }

@router.post("/create", response_model=DiagnosisResponse)
def create_diagnosis(payload: DiagnosisCreate, db: Session = Depends(get_db)):
    """
    Creates a new study session with chosen modality and optional patient_id.
    """
    diag = create_new_diagnosis(payload.modality, db, patient_id=payload.patient_id)
    return format_diagnosis_response(diag, db)

@router.post("/upload")
async def upload_image(
    study_id: str = Form(...),
    image_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads scan image for a given study (Ultrasound or Mammography).
    """
    uploaded_rec = await save_upload_image(study_id, image_type, file, db)
    return {
        "status": "success",
        "study_id": study_id,
        "image_type": uploaded_rec.image_type,
        "file_name": uploaded_rec.file_name,
        "file_url": f"/uploads/{Path(uploaded_rec.file_path).name}",
        "file_size": uploaded_rec.file_size
    }

@router.post("/analyze", response_model=DiagnosisResponse)
def analyze_diagnosis(
    study_id: str = Form(...),
    patient_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Triggers local AI model inference pipeline.
    """
    diag = run_ai_analysis(study_id, db, patient_id=patient_id)
    return format_diagnosis_response(diag, db)

@router.get("/history", response_model=List[DiagnosisHistoryItem])
def get_diagnosis_history(db: Session = Depends(get_db)):
    """
    Returns historical studies ordered by creation date.
    """
    history = db.query(Diagnosis).order_by(desc(Diagnosis.created_at)).all()
    results = []
    for d in history:
        results.append({
            "study_id": d.study_id,
            "patient_id": d.patient_id,
            "date": d.created_at,
            "modality": d.modality,
            "prediction": d.prediction,
            "confidence": d.confidence,
            "status": d.status,
            "birads_category": d.birads_category
        })
    return results

@router.get("/{study_id}", response_model=DiagnosisResponse)
def get_diagnosis_by_study_id(study_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full study details including images, model results, and explainability heatmaps.
    """
    diag = db.query(Diagnosis).filter(Diagnosis.study_id == study_id).first()
    if not diag:
        raise HTTPException(status_code=404, detail="Study not found.")
    return format_diagnosis_response(diag, db)
