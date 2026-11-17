import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import PatientClinicalDetails
from backend.schemas.patient import PatientCreate, PatientUpdate, PatientResponse

router = APIRouter(prefix="/api/patients", tags=["Patients"])

def format_patient_response(p: PatientClinicalDetails) -> dict:
    symptoms_list = []
    if p.symptoms:
        try:
            symptoms_list = json.loads(p.symptoms)
            if not isinstance(symptoms_list, list):
                symptoms_list = [str(symptoms_list)]
        except Exception:
            symptoms_list = [s.strip() for s in p.symptoms.split(",") if s.strip()]

    return {
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

@router.post("", response_model=PatientResponse)
def create_or_update_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    """
    Creates a new patient clinical record or updates existing if patient_id already exists.
    """
    patient_id = payload.patient_id.strip()
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID cannot be empty.")

    symptoms_json = json.dumps(payload.symptoms) if payload.symptoms else "[]"

    existing = db.query(PatientClinicalDetails).filter(PatientClinicalDetails.patient_id == patient_id).first()
    if existing:
        # Update existing record
        existing.age = payload.age
        existing.menopause_status = payload.menopause_status
        existing.breast_density = payload.breast_density
        existing.family_history = payload.family_history
        existing.breast_side = payload.breast_side
        existing.symptoms = symptoms_json
        existing.other_symptoms = payload.other_symptoms
        existing.previous_biopsy = payload.previous_biopsy
        existing.clinical_notes = payload.clinical_notes
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return format_patient_response(existing)

    new_patient = PatientClinicalDetails(
        patient_id=patient_id,
        age=payload.age,
        menopause_status=payload.menopause_status,
        breast_density=payload.breast_density,
        family_history=payload.family_history,
        breast_side=payload.breast_side,
        symptoms=symptoms_json,
        other_symptoms=payload.other_symptoms,
        previous_biopsy=payload.previous_biopsy,
        clinical_notes=payload.clinical_notes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return format_patient_response(new_patient)

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieves patient clinical details by patient_id.
    """
    patient = db.query(PatientClinicalDetails).filter(PatientClinicalDetails.patient_id == patient_id.strip()).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID '{patient_id}' not found.")
    return format_patient_response(patient)

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, payload: PatientUpdate, db: Session = Depends(get_db)):
    """
    Updates clinical details for an existing patient.
    """
    patient = db.query(PatientClinicalDetails).filter(PatientClinicalDetails.patient_id == patient_id.strip()).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient ID '{patient_id}' not found.")

    if payload.age is not None:
        patient.age = payload.age
    if payload.menopause_status is not None:
        patient.menopause_status = payload.menopause_status
    if payload.breast_density is not None:
        patient.breast_density = payload.breast_density
    if payload.family_history is not None:
        patient.family_history = payload.family_history
    if payload.breast_side is not None:
        patient.breast_side = payload.breast_side
    if payload.symptoms is not None:
        patient.symptoms = json.dumps(payload.symptoms)
    if payload.other_symptoms is not None:
        patient.other_symptoms = payload.other_symptoms
    if payload.previous_biopsy is not None:
        patient.previous_biopsy = payload.previous_biopsy
    if payload.clinical_notes is not None:
        patient.clinical_notes = payload.clinical_notes

    patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(patient)
    return format_patient_response(patient)
