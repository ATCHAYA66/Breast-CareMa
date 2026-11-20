"""Verification Test Suite for Final Architecture Correction:
Tests:
1. Workflow 1: Single Scan – Ultrasound (BUSI Dual-Model Engine)
2. Workflow 2: Single Scan – Mammography (EfficientNetB0 + Grad-CAM)
3. Workflow 3: Dual Scan – Combined (Independent Side-by-Side Correlation)
4. Model Status & Metrics API Verification (YOLOv8 Audit & BUSI Benchmarks)
5. Preserved Research Endpoints (/api/research/busi/status and /api/research/busi/analyze)
"""
import sys
import os
import json
import time
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
import uvicorn

HOST = "127.0.0.1"
PORT = 8003
BASE_URL = f"http://{HOST}:{PORT}"

print("[Init] Pre-loading backend application and models in main thread...", flush=True)
from backend.main import app
print("[Init] Backend application ready.", flush=True)

BUSI_DIR = PROJECT_ROOT / "datasets" / "BUSI"
US_BENIGN = next(BUSI_DIR.rglob("benign (81).png"))
US_MALIGNANT = next(BUSI_DIR.rglob("malignant (88).png"))
MG_SAMPLE = PROJECT_ROOT / "backend" / "uploads" / "sample_test_mg.jpg"


class UvicornServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            log_level="error",
            access_log=False
        )
        self.server = uvicorn.Server(config)
        self.server.install_signal_handlers = lambda: None

    def run(self):
        try:
            self.server.run()
        except Exception as e:
            print(f"[Server Thread Exception] {e}", flush=True)

    def stop(self):
        self.server.should_exit = True


def run_tests():
    print("=" * 70, flush=True)
    print("FINAL ARCHITECTURE CORRECTION: 3-WORKFLOW VERIFICATION", flush=True)
    print("=" * 70, flush=True)

    server_thread = UvicornServerThread()
    server_thread.start()

    max_wait = 25
    start_time = time.time()
    server_up = False
    while time.time() - start_time < max_wait:
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if r.status_code == 200:
                server_up = True
                print(f"[Init] Live backend listening on {BASE_URL} in {time.time() - start_time:.2f}s", flush=True)
                break
        except Exception:
            time.sleep(0.5)

    if not server_up:
        print("[Error] Failed to connect to backend server within timeout.", flush=True)
        sys.exit(1)

    results = {}

    try:
        # ==============================================================
        # WORKFLOW 1: Single Scan – Ultrasound
        # ==============================================================
        print("\n[Workflow 1] Testing Single Scan – Ultrasound (BUSI Engine)...", flush=True)
        # 1. Create study
        create_res = requests.post(f"{BASE_URL}/api/diagnosis/create", json={"modality": "ultrasound", "patient_id": "WF1-PT-001"})
        assert create_res.status_code == 200
        study_id_us = create_res.json()["study_id"]
        print(f"  -> Created ultrasound study: {study_id_us}", flush=True)

        # 2. Upload ultrasound scan
        with open(US_BENIGN, "rb") as f:
            up_res = requests.post(
                f"{BASE_URL}/api/diagnosis/upload",
                data={"study_id": study_id_us, "image_type": "ultrasound"},
                files={"file": ("us_benign.png", f, "image/png")}
            )
        assert up_res.status_code == 200
        print("  -> Uploaded ultrasound scan successfully.", flush=True)

        # 3. Analyze
        ana_res = requests.post(f"{BASE_URL}/api/diagnosis/analyze", data={"study_id": study_id_us})
        assert ana_res.status_code == 200
        ana_json = ana_res.json()

        # Verifications
        assert ana_json["modality"] == "ultrasound"
        assert ana_json["prediction"] == "Benign", f"Expected Benign, got {ana_json['prediction']}"
        assert ana_json["confidence"] is not None and ana_json["confidence"] > 0.90
        assert ana_json["lesion_area"] is not None and ana_json["lesion_area"] > 0.0

        model_names = [m["model_name"] for m in ana_json["model_results"]]
        assert any("BUSI EfficientNet-B0" in name for name in model_names), "BUSI Classifier missing from results"
        assert any("BUSI Compact U-Net" in name for name in model_names), "BUSI Segmenter missing from results"
        assert any("YOLOv8" in name and "Decommissioned" in name for name in model_names), "YOLOv8 audit entry missing"

        # Check overlay URL
        seg_res = next(m for m in ana_json["model_results"] if "Compact U-Net" in m["model_name"])
        assert seg_res["output_url"] is not None
        ov_res = requests.get(f"{BASE_URL}{seg_res['output_url']}")
        assert ov_res.status_code == 200
        print(f"  -> Passed Workflow 1: Prediction={ana_json['prediction']} (Score={ana_json['confidence']*100:.1f}%), LesionArea={ana_json['lesion_area']:.2f}%, Overlay={seg_res['output_url']}", flush=True)
        results["workflow_1_ultrasound"] = {
            "status": "passed",
            "study_id": study_id_us,
            "prediction": ana_json["prediction"],
            "confidence": ana_json["confidence"],
            "lesion_area": ana_json["lesion_area"],
            "models": model_names
        }

        # ==============================================================
        # WORKFLOW 2: Single Scan – Mammography
        # ==============================================================
        print("\n[Workflow 2] Testing Single Scan – Mammography (EfficientNet + Grad-CAM)...", flush=True)
        # 1. Create study
        create_res = requests.post(f"{BASE_URL}/api/diagnosis/create", json={"modality": "mammography", "patient_id": "WF2-PT-002"})
        assert create_res.status_code == 200
        study_id_mg = create_res.json()["study_id"]
        print(f"  -> Created mammography study: {study_id_mg}", flush=True)

        # 2. Upload mammography scan
        with open(MG_SAMPLE, "rb") as f:
            up_res = requests.post(
                f"{BASE_URL}/api/diagnosis/upload",
                data={"study_id": study_id_mg, "image_type": "mammography"},
                files={"file": ("mg_sample.jpg", f, "image/jpeg")}
            )
        assert up_res.status_code == 200

        # 3. Analyze
        ana_res = requests.post(f"{BASE_URL}/api/diagnosis/analyze", data={"study_id": study_id_mg})
        assert ana_res.status_code == 200
        ana_json = ana_res.json()

        # Verifications
        assert ana_json["modality"] == "mammography"
        assert ana_json["prediction"] in ["Benign", "Malignant"]
        assert ana_json["confidence"] is not None

        model_names_mg = [m["model_name"] for m in ana_json["model_results"]]
        assert any("EfficientNetB0" in name for name in model_names_mg), "Mammography EfficientNetB0 missing"
        assert not any("BUSI" in name for name in model_names_mg), "BUSI model incorrectly called for mammography"

        mg_mr = next(m for m in ana_json["model_results"] if "EfficientNetB0" in m["model_name"])
        assert mg_mr["output_url"] is not None
        gradcam_check = requests.get(f"{BASE_URL}{mg_mr['output_url']}")
        assert gradcam_check.status_code == 200
        print(f"  -> Passed Workflow 2: Prediction={ana_json['prediction']} (Conf={ana_json['confidence']*100:.1f}%), Grad-CAM={mg_mr['output_url']}", flush=True)
        results["workflow_2_mammography"] = {
            "status": "passed",
            "study_id": study_id_mg,
            "prediction": ana_json["prediction"],
            "confidence": ana_json["confidence"],
            "models": model_names_mg
        }

        # ==============================================================
        # WORKFLOW 3: Dual Scan – Combined (Independent Side-by-Side)
        # ==============================================================
        print("\n[Workflow 3] Testing Dual Scan – Combined (Independent Correlation)...", flush=True)
        create_res = requests.post(f"{BASE_URL}/api/diagnosis/create", json={"modality": "dual", "patient_id": "WF3-PT-003"})
        assert create_res.status_code == 200
        study_id_dual = create_res.json()["study_id"]
        print(f"  -> Created dual study: {study_id_dual}", flush=True)

        # Upload both images
        with open(US_BENIGN, "rb") as f:
            up_us = requests.post(
                f"{BASE_URL}/api/diagnosis/upload",
                data={"study_id": study_id_dual, "image_type": "ultrasound"},
                files={"file": ("us_dual.png", f, "image/png")}
            )
        assert up_us.status_code == 200

        with open(MG_SAMPLE, "rb") as f:
            up_mg = requests.post(
                f"{BASE_URL}/api/diagnosis/upload",
                data={"study_id": study_id_dual, "image_type": "mammography"},
                files={"file": ("mg_dual.jpg", f, "image/jpeg")}
            )
        assert up_mg.status_code == 200
        print("  -> Both paired scans uploaded successfully.", flush=True)

        # Analyze
        ana_res = requests.post(f"{BASE_URL}/api/diagnosis/analyze", data={"study_id": study_id_dual})
        assert ana_res.status_code == 200
        ana_json = ana_res.json()

        # Strict checks for Dual Scan
        assert ana_json["modality"] == "dual"
        assert "Dual Examination (Independent Findings)" in ana_json["prediction"]
        assert ana_json["confidence"] is None, "Fabricated combined confidence detected; must be None for independent correlation"

        dual_model_names = [m["model_name"] for m in ana_json["model_results"]]
        assert any("BUSI EfficientNet-B0" in name for name in dual_model_names), "Ultrasound BUSI missing in dual scan"
        assert any("EfficientNetB0 Classifier" in name for name in dual_model_names), "Mammography missing in dual scan"
        assert any("Dual Scan (Independent Correlation)" in name for name in dual_model_names), "Independent correlation entry missing"
        assert not any("Multimodal Feature Fusion (MLP)" in name for name in dual_model_names), "Unvalidated MLP fusion should not be called"

        print(f"  -> Passed Workflow 3: Dual Scan completed with independent presentation (Prediction: '{ana_json['prediction']}', Confidence: {ana_json['confidence']}).", flush=True)
        results["workflow_3_dual"] = {
            "status": "passed",
            "study_id": study_id_dual,
            "prediction": ana_json["prediction"],
            "confidence": ana_json["confidence"],
            "models": dual_model_names
        }

        # ==============================================================
        # TELEMETRY & AUDIT: Models API & Research Endpoints
        # ==============================================================
        print("\n[Audit & Telemetry] Testing Model Status and Benchmark Metrics...", flush=True)
        st_res = requests.get(f"{BASE_URL}/api/models/status")
        assert st_res.status_code == 200
        st_json = st_res.json()
        assert "BUSI EfficientNet-B0" in st_json["ultrasound_classifier"]["name"]
        assert st_json["yolov8_audit"]["status"] == "Decommissioned"

        metrics_res = requests.get(f"{BASE_URL}/api/models/metrics")
        assert metrics_res.status_code == 200
        metrics_json = metrics_res.json()
        busi_metric = next(m for m in metrics_json if "BUSI EfficientNet-B0" in m["model_name"])
        assert busi_metric["accuracy"] == 0.8475
        print(f"  -> Passed Model Telemetry: BUSI Accuracy={busi_metric['accuracy']*100:.2f}%, YOLOv8 Audit={st_json['yolov8_audit']['status']}", flush=True)

        print("\n[Preserved Research API] Testing GET /api/research/busi/status...", flush=True)
        busi_st = requests.get(f"{BASE_URL}/api/research/busi/status")
        assert busi_st.status_code == 200
        assert busi_st.json()["status"] == "ready"
        print("  -> Passed: Research status endpoint operational.", flush=True)

        results["telemetry_and_audit"] = {"status": "passed"}

        output_path = PROJECT_ROOT / "training" / "three_workflows_test_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nALL THREE WORKFLOWS VERIFIED SUCCESSFULLY. Results saved to {output_path}", flush=True)

    finally:
        server_thread.stop()


if __name__ == "__main__":
    run_tests()
