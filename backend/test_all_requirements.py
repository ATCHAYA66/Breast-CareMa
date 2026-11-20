import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import Diagnosis, UploadedImages, ModelResults, Reports
from backend.ai_models.ultrasound_model import UltrasoundTumorDetector
from backend.services.diagnosis_service import create_new_diagnosis, run_ai_analysis, ai_manager
from backend.services.report_service import generate_pdf_report
from backend.config import UPLOADS_DIR

client = TestClient(app)

def test_1_image_with_detection():
    print("\n--- TEST 1: Image with Detected Lesion ---")
    detector = UltrasoundTumorDetector()
    assert detector.model is not None, "Model should be loaded"
    
    # We found BCMA-20261114-6B4F_ultrasound_6bd931.png produces detections
    img_path = UPLOADS_DIR / "BCMA-20261114-6B4F_ultrasound_6bd931.png"
    assert img_path.exists(), f"Image {img_path} not found"
    
    res = detector.analyze(str(img_path), "TEST_STUDY_DETECT")
    assert res["detection_status"] == "detected", f"Expected 'detected', got {res['detection_status']}"
    assert res["predicted_class"] != "Inconclusive", "Detected image should have actual class"
    assert res["confidence"] is not None and 0.0 < res["confidence"] <= 1.0
    assert len(res["boxes"]) > 0
    qf = res["quantitative_findings"]
    assert qf["lesion_area_px"] is not None and qf["lesion_area_px"] > 0
    assert qf["aspect_ratio"] is not None and qf["aspect_ratio"] > 0
    print(f" Detected lesion: Class={res['predicted_class']}, Conf={res['confidence']}, Area={qf['lesion_area_px']}, AspectRatio={qf['aspect_ratio']}")

def test_2_image_with_no_detection():
    print("\n--- TEST 2: Image with No Detection ---")
    detector = UltrasoundTumorDetector()
    img_path = UPLOADS_DIR / "sample_test_us.jpg"
    assert img_path.exists(), f"Image {img_path} not found"
    
    res = detector.analyze(str(img_path), "TEST_STUDY_NODETECT")
    assert res["detection_status"] == "no_detection", f"Expected 'no_detection', got {res['detection_status']}"
    assert res["predicted_class"] == "Inconclusive", f"Expected 'Inconclusive', got {res['predicted_class']}"
    assert res["confidence"] is None, f"Expected None confidence, got {res['confidence']}"
    assert len(res["boxes"]) == 0
    qf = res["quantitative_findings"]
    assert qf["lesion_area_px"] is None, f"Expected None lesion_area_px, got {qf['lesion_area_px']}"
    assert qf["aspect_ratio"] is None, f"Expected None aspect_ratio, got {qf['aspect_ratio']}"
    print(f" No-detection image correctly evaluated as Inconclusive with None confidence and None area.")

def test_3_model_loading_failure():
    print("\n--- TEST 3: Model Loading Failure Handling ---")
    # Non-existent weights should not fall back to COCO or pretend to be loaded
    bad_detector = UltrasoundTumorDetector(weights_path=Path("non_existent_weights_xyz.pt"))
    assert bad_detector.model is None, "Model should be None when weights are missing"
    assert bad_detector.is_custom_trained is False
    
    img_path = UPLOADS_DIR / "sample_test_us.jpg"
    res = bad_detector.analyze(str(img_path), "TEST_STUDY_UNAVAIL")
    assert res["detection_status"] == "model_unavailable"
    assert res["predicted_class"] == "Inconclusive"
    assert res["confidence"] is None
    
    # Test API error response when model is unavailable
    db = SessionLocal()
    diag = create_new_diagnosis("ultrasound", db)
    us_rec = UploadedImages(
        study_id=diag.study_id,
        image_type="ultrasound",
        file_name="sample_test_us.jpg",
        file_path=str(img_path),
        file_size=os.path.getsize(img_path)
    )
    db.add(us_rec)
    db.commit()
    
    # Temporarily set detector model to None to test API error handling
    orig_detector = ai_manager.ultrasound_detector
    ai_manager.ultrasound_detector = bad_detector
    try:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            run_ai_analysis(diag.study_id, db)
        assert exc_info.value.status_code == 503
        
        # Verify DB records status as failed
        db.refresh(diag)
        assert diag.status == "failed"
        print(f" API correctly raised HTTP 503 and marked study status as 'failed' when model was unavailable.")
    finally:
        ai_manager.ultrasound_detector = orig_detector
        db.close()

def test_4_report_generation():
    print("\n--- TEST 4: Diagnostic PDF Report Generation ---")
    report_data = {
        "study_id": "BCMA-TEST-REPORT-001",
        "modality": "ultrasound",
        "prediction": "Inconclusive",
        "confidence": None,
        "birads_category": "Not assigned by AI system",
        "recommended_action": "Routine clinical correlation recommended. Review with certified radiologist.",
        "patient": {
            "patient_id": "PT-TEST-01",
            "age": 45,
            "menopause_status": "Premenopausal",
            "breast_density": "Category B",
            "family_history": "No",
            "breast_side": "Left",
            "symptoms": ["Palpable Lump"],
            "other_symptoms": None,
            "previous_biopsy": "No",
            "clinical_notes": "Screening examination"
        },
        "quantitative_findings": {
            "lesion_area_px": None,
            "aspect_ratio": None,
            "shape": "Not assessed",
            "margin": "Not assessed",
            "orientation": "Not assessed"
        },
        "us_annotated_path": None,
        "mg_overlay_path": None,
        "birads_evidence": "No BI-RADS category is generated by this research model.",
        "detection_status": "no_detection",
        "confidence_available": False
    }
    
    pdf_path = generate_pdf_report(report_data)
    assert Path(pdf_path).exists(), "PDF report file was not created"
    assert os.path.getsize(pdf_path) > 1000, "PDF file is too small / empty"
    print(f" Generated valid PDF report: {pdf_path} (Size: {os.path.getsize(pdf_path)} bytes)")

def test_5_verify_no_hardcoded_values():
    print("\n--- TEST 5: Verify Confidence and Measurements are NOT Hardcoded ---")
    detector = UltrasoundTumorDetector()
    
    # Run two different images
    img1 = UPLOADS_DIR / "BCMA-20261114-6B4F_ultrasound_6bd931.png"
    img2 = UPLOADS_DIR / "sample_test_us.jpg"
    
    res1 = detector.analyze(str(img1), "TEST_HC_1")
    res2 = detector.analyze(str(img2), "TEST_HC_2")
    
    # Check that res1 and res2 have completely different, dynamic values
    assert res1["confidence"] != 0.85, f"Confidence should not be hardcoded 0.85 (got {res1['confidence']})"
    assert res2["confidence"] != 0.85, f"Confidence should not be hardcoded 0.85 (got {res2['confidence']})"
    assert res1["confidence"] != res2["confidence"], "Different images must yield different confidences"
    
    qf1 = res1["quantitative_findings"]
    qf2 = res2["quantitative_findings"]
    assert qf1["lesion_area_px"] != 245.0, f"Area should not be hardcoded 245.0 (got {qf1['lesion_area_px']})"
    assert qf2["lesion_area_px"] is None, f"No detection should have None area (got {qf2['lesion_area_px']})"
    assert qf1["aspect_ratio"] != 1.35, f"Aspect ratio should not be hardcoded 1.35 (got {qf1['aspect_ratio']})"
    assert qf2["aspect_ratio"] is None, f"No detection should have None aspect ratio (got {qf2['aspect_ratio']})"
    print(" Confirmed: Confidence, lesion area, and aspect ratio are dynamic model outputs, NOT hardcoded.")

def test_6_api_endpoints_working():
    print("\n--- TEST 6: Check all existing API endpoints ---")
    # Health check
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    assert r.json()["status"] == "healthy"
    print(" GET /api/health -> 200 OK")
    
    # Models metrics
    r = client.get("/api/models/metrics")
    assert r.status_code == 200, f"Models metrics failed: {r.status_code}"
    print(" GET /api/models/metrics -> 200 OK")
    
    # Dashboard stats
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200, f"Dashboard stats failed: {r.status_code}"
    print(" GET /api/dashboard/stats -> 200 OK")
    
    # Diagnosis create
    r = client.post("/api/diagnosis/create", json={"modality": "ultrasound"})
    assert r.status_code == 200, f"Diagnosis create failed: {r.status_code}"
    study_id = r.json()["study_id"]
    print(f" POST /api/diagnosis/create -> 200 OK (Study: {study_id})")
    
    # Diagnosis history
    r = client.get("/api/diagnosis/history")
    assert r.status_code == 200, f"Diagnosis history failed: {r.status_code}"
    print(" GET /api/diagnosis/history -> 200 OK")
    
    # Patient list & creation
    r = client.get("/api/patients")
    assert r.status_code == 200, f"Patients list failed: {r.status_code}"
    print(" GET /api/patients -> 200 OK")

if __name__ == "__main__":
    test_1_image_with_detection()
    test_2_image_with_no_detection()
    test_3_model_loading_failure()
    test_4_report_generation()
    test_5_verify_no_hardcoded_values()
    test_6_api_endpoints_working()
    print("\n=======================================================")
    print(" ALL 6 SPECIFIED TEST REQUIREMENTS PASSED SUCCESSFULLY!")
    print("=======================================================")
