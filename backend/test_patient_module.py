import os
import json
from pathlib import Path
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import PatientClinicalDetails, Diagnosis, UploadedImages
from backend.services.diagnosis_service import create_new_diagnosis, run_ai_analysis
from backend.config import UPLOADS_DIR

def test_patient_module():
    print("=== TESTING PATIENT & CLINICAL DETAILS MODULE ===")
    from backend.database.connection import run_migrations
    Base.metadata.create_all(bind=engine)
    run_migrations()
    db = SessionLocal()

    patient_id = "PT-2026-TEST01"
    
    # 1. Create Patient Record
    existing = db.query(PatientClinicalDetails).filter(PatientClinicalDetails.patient_id == patient_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    patient = PatientClinicalDetails(
        patient_id=patient_id,
        age=52,
        menopause_status="Postmenopausal",
        breast_density="Category C – Heterogeneously Dense",
        family_history="Yes",
        breast_side="Left",
        symptoms=json.dumps(["Breast Lump", "Breast Pain"]),
        other_symptoms=None,
        previous_biopsy="No",
        clinical_notes="Palpable firm nodule upper outer quadrant, non-tender."
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    print(f"Created Patient Clinical Details: {patient.patient_id}, Age {patient.age}, Side {patient.breast_side}")

    # 2. Test Dual Scan Workflow Linked to Patient
    diag = create_new_diagnosis("dual", db, patient_id=patient_id)
    study_id = diag.study_id
    print(f"Created Study ID: {study_id} linked to Patient: {diag.patient_id}")

    # Link test images
    us_path = UPLOADS_DIR / "sample_test_us.jpg"
    mg_path = UPLOADS_DIR / "sample_test_mg.jpg"

    us_rec = UploadedImages(
        study_id=study_id,
        image_type="ultrasound",
        file_name="sample_test_us.jpg",
        file_path=str(us_path),
        file_size=os.path.getsize(us_path)
    )
    mg_rec = UploadedImages(
        study_id=study_id,
        image_type="mammography",
        file_name="sample_test_mg.jpg",
        file_path=str(mg_path),
        file_size=os.path.getsize(mg_path)
    )
    db.add(us_rec)
    db.add(mg_rec)
    db.commit()

    # Run Analysis and generate PDF report with patient info
    res = run_ai_analysis(study_id, db, patient_id=patient_id)
    print("AI Analysis & Report Generation Completed!")
    print(f" - Study ID: {res.study_id}")
    print(f" - Linked Patient ID: {res.patient_id}")
    print(f" - Primary Prediction: {res.prediction}")
    print(f" - Report Path: {res.report_path}")

    assert Path(res.report_path).exists(), "PDF report missing!"
    print(f"Verified PDF report on disk: {os.path.getsize(res.report_path)} bytes")

    db.close()
    print("\n PATIENT CLINICAL DETAILS MODULE PASSED ALL TESTS!")

if __name__ == "__main__":
    test_patient_module()
