import os
import cv2
import numpy as np
from pathlib import Path
from backend.database.connection import SessionLocal, engine, Base
from backend.database.models import Diagnosis
from backend.services.diagnosis_service import (
    create_new_diagnosis,
    run_ai_analysis,
    ai_manager
)
from backend.services.report_service import generate_pdf_report
from backend.config import UPLOADS_DIR

def run_tests():
    print("=== TEST PHASE 1: DATABASE INITIALIZATION ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("Database connection & schema verified.")

    print("\n=== TEST PHASE 2: SYNTHETIC ULTRASOUND & MAMMOGRAPHY GENERATION ===")
    # Create sample ultrasound image with simulated hypoechoic nodule
    us_img = np.zeros((400, 500, 3), dtype=np.uint8)
    noise = np.random.normal(60, 25, (400, 500, 3)).astype(np.uint8)
    us_img = cv2.add(us_img, noise)
    # Simulated nodule (oval, circumscribed)
    cv2.ellipse(us_img, (250, 200), (70, 50), 0, 0, 360, (25, 25, 25), -1)
    us_sample_path = UPLOADS_DIR / "sample_test_us.jpg"
    cv2.imwrite(str(us_sample_path), us_img)
    print(f"Generated sample ultrasound scan: {us_sample_path}")

    # Create sample mammography image with breast tissue gradient
    mg_img = np.zeros((400, 500, 3), dtype=np.uint8)
    for y in range(400):
        for x in range(500):
            val = int(min(220, max(10, 0.4 * x + 0.2 * y + np.random.randint(-15, 15))))
            mg_img[y, x] = [val, val, val]
    # Subtle mass
    cv2.circle(mg_img, (300, 180), 40, (180, 180, 180), -1)
    mg_sample_path = UPLOADS_DIR / "sample_test_mg.jpg"
    cv2.imwrite(str(mg_sample_path), mg_img)
    print(f"Generated sample mammography scan: {mg_sample_path}")

    print("\n=== TEST PHASE 3: DUAL SCAN WORKFLOW ===")
    diag = create_new_diagnosis("dual", db)
    study_id = diag.study_id
    print(f"Created Study ID: {study_id}")

    # Save images in UploadedImages table
    from backend.database.models import UploadedImages
    us_rec = UploadedImages(
        study_id=study_id,
        image_type="ultrasound",
        file_name="sample_test_us.jpg",
        file_path=str(us_sample_path),
        file_size=os.path.getsize(us_sample_path)
    )
    mg_rec = UploadedImages(
        study_id=study_id,
        image_type="mammography",
        file_name="sample_test_mg.jpg",
        file_path=str(mg_sample_path),
        file_size=os.path.getsize(mg_sample_path)
    )
    db.add(us_rec)
    db.add(mg_rec)
    db.commit()

    print("\n=== TEST PHASE 4: RUNNING AI INFERENCE (YOLOv8 + EfficientNet + Grad-CAM + Fusion) ===")
    completed_diag = run_ai_analysis(study_id, db)
    print(f"Inference Completed!")
    print(f" - Primary Prediction: {completed_diag.prediction}")
    print(f" - Confidence: {completed_diag.confidence * 100:.1f}%")
    print(f" - BI-RADS Category: {completed_diag.birads_category}")
    print(f" - Lesion Area: {completed_diag.lesion_area} sq px")
    print(f" - Aspect Ratio: {completed_diag.aspect_ratio}")
    print(f" - Shape: {completed_diag.shape}")
    print(f" - Margin: {completed_diag.margin}")
    print(f" - Orientation: {completed_diag.orientation}")
    print(f" - Generated Report Path: {completed_diag.report_path}")

    assert Path(completed_diag.report_path).exists(), "PDF report was not generated!"
    print("PDF Report file exists on disk and is verified!")

    db.close()
    print("\n ALL SYSTEM TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
