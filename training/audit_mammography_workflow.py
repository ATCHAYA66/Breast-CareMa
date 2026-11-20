"""Detailed technical audit of the Mammography workflow in Breast CARE-MA.
Checks:
1. Model architecture and checkpoint path.
2. Checkpoint existence, training origin, custom trained flag.
3. Dataset used and class mapping.
4. Mammography preprocessing and input tensor dimensions.
5. End-to-end API upload and inference execution (matching frontend flow).
6. Classification output and confidence score verification.
7. Grad-CAM generation, heatmap file existence, and HTTP delivery.
8. Negative / invalid input handling (.pdf, 0-byte, corrupt image).
9. Verification that BUSI ultrasound models are NOT called by the mammography workflow.
"""
import sys
import os
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
import torch
from backend.config import EFFICIENTNET_WEIGHTS_PATH, OUTPUTS_DIR
from backend.ai_models.mammography_model import MammographyClassifier, CLASSES
from backend.ai_models.preprocessing import preprocess_mammography, load_and_validate_image

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_MG = PROJECT_ROOT / "backend" / "uploads" / "sample_test_mg.jpg"

def run_audit():
    audit = {}

    print("=" * 70)
    print("MAMMOGRAPHY WORKFLOW AUDIT")
    print("=" * 70)

    # -----------------------------------------------------------------
    # Check 1: Model Architecture & Checkpoint Path
    # -----------------------------------------------------------------
    print("\n[Check 1] Model Architecture & Checkpoint Path:")
    model = MammographyClassifier()
    backbone_name = type(model.backbone).__name__
    clf_head = str(model.backbone.classifier)
    weights_path = model.weights_path
    print(f"  -> Backbone Type: {backbone_name}")
    print(f"  -> Classifier Head: {clf_head}")
    print(f"  -> Checkpoint Path configured: {weights_path}")
    audit["check_1_architecture"] = {
        "backbone": backbone_name,
        "classifier_head": clf_head,
        "weights_path": str(weights_path)
    }

    # -----------------------------------------------------------------
    # Check 2: Checkpoint file existence and training verification
    # -----------------------------------------------------------------
    print("\n[Check 2] Checkpoint File Verification:")
    file_exists = weights_path.is_file()
    is_custom_trained = model.is_custom_trained
    print(f"  -> Weights file exists on disk: {file_exists}")
    print(f"  -> Model is_custom_trained flag: {is_custom_trained}")
    if not file_exists:
        print("  -> CRITICAL AUDIT FINDING: 'efficientnet_b0_mammography.pth' is NOT present in backend/weights/.")
        print("  -> The model is operating on standard torchvision ImageNet weights with a randomly initialized 2-class head.")
    audit["check_2_checkpoint_file"] = {
        "file_exists": file_exists,
        "is_custom_trained": is_custom_trained
    }

    # -----------------------------------------------------------------
    # Check 3: Dataset Used & Class Mapping
    # -----------------------------------------------------------------
    print("\n[Check 3] Dataset Used & Class Mapping:")
    print(f"  -> Designated Dataset: CBIS-DDSM (Curated Breast Imaging Subset of DDSM)")
    print(f"  -> Classes Defined in code: {CLASSES}")
    print(f"  -> Number of classes: {len(CLASSES)}")
    audit["check_3_dataset_classes"] = {
        "dataset": "CBIS-DDSM",
        "classes": CLASSES
    }

    # -----------------------------------------------------------------
    # Check 4: Preprocessing & Input Dimensions
    # -----------------------------------------------------------------
    print("\n[Check 4] Preprocessing & Tensor Dimensions:")
    assert SAMPLE_MG.is_file(), f"Sample image not found: {SAMPLE_MG}"
    img_rgb = load_and_validate_image(str(SAMPLE_MG))
    orig_h, orig_w, orig_c = img_rgb.shape
    tensor = preprocess_mammography(img_rgb)
    print(f"  -> Original sample shape: {orig_h}x{orig_w}x{orig_c}")
    print(f"  -> Preprocessed tensor shape: {list(tensor.shape)} (Expected: [1, 3, 224, 224])")
    print(f"  -> Tensor dtype: {tensor.dtype}")
    print(f"  -> Normalization: ImageNet mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]")
    assert list(tensor.shape) == [1, 3, 224, 224], f"Unexpected shape: {tensor.shape}"
    audit["check_4_preprocessing"] = {
        "input_dimensions": list(tensor.shape),
        "target_size": [224, 224],
        "channels": 3,
        "normalization": "ImageNet"
    }

    # -----------------------------------------------------------------
    # Check 5: End-to-End API Upload & Study Creation
    # -----------------------------------------------------------------
    print("\n[Check 5] Frontend-Equivalent Study Creation & Upload:")
    # 1. Create study
    create_res = requests.post(f"{BASE_URL}/api/diagnosis/create", json={"modality": "mammography", "patient_id": "AUDIT-MG-001"})
    assert create_res.status_code == 200, f"Failed to create study: {create_res.text}"
    study_id = create_res.json()["study_id"]
    print(f"  -> Created study: {study_id} (modality=mammography)")

    # 2. Upload mammogram
    with open(SAMPLE_MG, "rb") as f:
        up_res = requests.post(
            f"{BASE_URL}/api/diagnosis/upload",
            data={"study_id": study_id, "image_type": "mammography"},
            files={"file": ("sample_test_mg.jpg", f, "image/jpeg")}
        )
    assert up_res.status_code == 200, f"Upload failed: {up_res.text}"
    print(f"  -> Uploaded mammography image successfully (HTTP {up_res.status_code}).")
    audit["check_5_upload"] = {
        "study_id": study_id,
        "upload_http_code": up_res.status_code
    }

    # -----------------------------------------------------------------
    # Check 6 & 7: Inference, Classification Output & Confidence
    # -----------------------------------------------------------------
    print("\n[Check 6 & 7] Inference Execution & Classification Output:")
    ana_res = requests.post(f"{BASE_URL}/api/diagnosis/analyze", data={"study_id": study_id})
    assert ana_res.status_code == 200, f"Inference failed: {ana_res.text}"
    ana_json = ana_res.json()
    print(f"  -> Study Status: {ana_json['status']}")
    print(f"  -> Predicted Class: {ana_json['prediction']}")
    print(f"  -> Confidence Score: {ana_json['confidence']}")
    print(f"  -> Findings Summary: {ana_json['findings_summary']}")

    mg_model_result = next((m for m in ana_json["model_results"] if "EfficientNetB0" in m["model_name"]), None)
    assert mg_model_result is not None, "EfficientNetB0 result missing from database"
    raw_obj = mg_model_result.get("raw_data", {})
    if isinstance(raw_obj, str):
        raw_obj = json.loads(raw_obj)

    print(f"  -> Probabilities: {raw_obj.get('probabilities')}")
    print(f"  -> Raw is_custom_trained recorded: {raw_obj.get('is_custom_trained')}")

    audit["check_6_7_inference"] = {
        "status": ana_json["status"],
        "predicted_class": ana_json["prediction"],
        "confidence": ana_json["confidence"],
        "probabilities": raw_obj.get("probabilities"),
        "is_custom_trained": raw_obj.get("is_custom_trained")
    }

    # -----------------------------------------------------------------
    # Check 8: Grad-CAM Generation & Image Rendering
    # -----------------------------------------------------------------
    print("\n[Check 8] Grad-CAM Generation & Asset Delivery:")
    output_url = mg_model_result.get("output_url")
    assert output_url is not None, "Grad-CAM output_url is null"
    print(f"  -> Grad-CAM Output URL: {output_url}")

    # Test HTTP image accessibility
    img_http_res = requests.get(f"{BASE_URL}{output_url}")
    assert img_http_res.status_code == 200, f"Failed to retrieve overlay: {img_http_res.status_code}"
    assert img_http_res.headers.get("content-type") in ["image/jpeg", "image/png"]
    assert len(img_http_res.content) > 1000
    assert img_http_res.content[:3] == b"\xff\xd8\xff", "Overlay is not a valid JPEG"
    print(f"  -> Overlay image delivered via HTTP: {len(img_http_res.content):,} bytes, valid JPEG magic bytes.")
    audit["check_8_gradcam"] = {
        "output_url": output_url,
        "http_code": img_http_res.status_code,
        "content_type": img_http_res.headers.get("content-type"),
        "bytes": len(img_http_res.content)
    }

    # -----------------------------------------------------------------
    # Check 9: Invalid Image Handling
    # -----------------------------------------------------------------
    print("\n[Check 9] Invalid Image Handling:")
    # A. Invalid extension (.pdf)
    inv_ext_res = requests.post(
        f"{BASE_URL}/api/diagnosis/upload",
        data={"study_id": study_id, "image_type": "mammography"},
        files={"file": ("invalid.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    print(f"  -> .pdf upload response: HTTP {inv_ext_res.status_code} ({inv_ext_res.json().get('detail')})")
    assert inv_ext_res.status_code == 400

    # B. Empty file (0 bytes)
    empty_res = requests.post(
        f"{BASE_URL}/api/diagnosis/upload",
        data={"study_id": study_id, "image_type": "mammography"},
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    print(f"  -> 0-byte upload response: HTTP {empty_res.status_code} ({empty_res.json().get('detail')})")
    assert empty_res.status_code == 400

    # C. Corrupted image file
    create_corrupt = requests.post(f"{BASE_URL}/api/diagnosis/create", json={"modality": "mammography", "patient_id": "CORRUPT-001"})
    corrupt_study_id = create_corrupt.json()["study_id"]
    requests.post(
        f"{BASE_URL}/api/diagnosis/upload",
        data={"study_id": corrupt_study_id, "image_type": "mammography"},
        files={"file": ("corrupt.jpg", b"NOT AN IMAGE JUNK BYTES 1234567890", "image/jpeg")}
    )
    corrupt_ana = requests.post(f"{BASE_URL}/api/diagnosis/analyze", data={"study_id": corrupt_study_id})
    print(f"  -> Corrupted image analysis response: HTTP {corrupt_ana.status_code} ({corrupt_ana.json().get('detail')})")
    assert corrupt_ana.status_code == 503 or corrupt_ana.status_code == 422 or corrupt_ana.status_code == 500

    audit["check_9_negative_testing"] = {
        "disallowed_extension_code": inv_ext_res.status_code,
        "empty_file_code": empty_res.status_code,
        "corrupted_image_code": corrupt_ana.status_code
    }

    # -----------------------------------------------------------------
    # Check 10: Confirm BUSI Models are NOT Called
    # -----------------------------------------------------------------
    print("\n[Check 10] Confirm BUSI Models are NOT Called by Mammography Workflow:")
    model_names_in_study = [m["model_name"] for m in ana_json["model_results"]]
    print(f"  -> Models executed for mammography study {study_id}: {model_names_in_study}")
    has_busi = any("BUSI" in name for name in model_names_in_study)
    has_yolo = any("YOLO" in name for name in model_names_in_study)
    print(f"  -> Any BUSI models called: {has_busi}")
    print(f"  -> Any YOLO models called: {has_yolo}")
    assert not has_busi, "CRITICAL ERROR: BUSI model was found in mammography study!"
    assert not has_yolo, "CRITICAL ERROR: YOLO model was found in mammography study!"
    print("  -> Passed: Mammography workflow strictly isolated from ultrasound BUSI models.")
    audit["check_10_isolation"] = {
        "models_recorded": model_names_in_study,
        "busi_called": has_busi,
        "yolo_called": has_yolo
    }

    out_json = PROJECT_ROOT / "training" / "mammography_audit_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    print(f"\nAudit completed. Telemetry written to {out_json}")

if __name__ == "__main__":
    run_audit()
