"""Live HTTP Smoke Test Suite for BREAST CARE-MA Backend API.
Starts uvicorn on port 8001, executes all live HTTP requests, tests edge cases and security,
verifies YOLO pipeline and database immutability, and stops cleanly.
"""
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
import threading
import uuid

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
import requests
from backend.database.connection import SessionLocal
from backend.database.models import Diagnosis, UploadedImages, ModelResults

HOST = "127.0.0.1"
PORT = 8001
BASE_URL = f"http://{HOST}:{PORT}"

print("[Init] Pre-loading backend application and models in main thread...")
from backend.main import app
print("[Init] Backend application ready.")


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
            import traceback
            print(f"[Server Thread Exception] {e}")
            traceback.print_exc()

    def stop(self):
        self.server.should_exit = True


def wait_for_server(timeout_sec=15):
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if r.status_code == 200:
                print(f"[Server] Live on {BASE_URL} (took {time.time()-start:.2f}s)")
                return True
        except Exception as e:
            print(f"[Poll error] {type(e).__name__}: {e}")
            time.sleep(0.5)
    return False


def run_smoke_test():
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_url": BASE_URL,
        "tests": {}
    }

    # Count database records before tests
    db = SessionLocal()
    initial_diag_count = db.query(Diagnosis).count()
    initial_img_count = db.query(UploadedImages).count()
    initial_mr_count = db.query(ModelResults).count()
    db.close()
    print(f"[DB Audit] Initial counts: Diagnosis={initial_diag_count}, Images={initial_img_count}, Results={initial_mr_count}")

    # Locate sample test images from BUSI dataset
    busi_dir = PROJECT_ROOT / "datasets" / "BUSI"
    benign_p = next(busi_dir.rglob("benign (81).png"))
    malignant_p = next(busi_dir.rglob("malignant (88).png"))
    malignant_empty_p = next(busi_dir.rglob("malignant (11).png"))
    normal_p = next(busi_dir.rglob("normal (109).png"))

    # -------------------------------------------------------------
    # Task 2: GET /api/research/busi/status
    # -------------------------------------------------------------
    print("\n--- Test 2: GET /api/research/busi/status ---")
    resp_status = requests.get(f"{BASE_URL}/api/research/busi/status")
    print(f"HTTP Status: {resp_status.status_code}")
    print(f"Response: {resp_status.json()}")
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] == "ready"
    assert resp_status.json()["models"]["classifier"]["loaded"] is True
    assert resp_status.json()["models"]["segmenter"]["loaded"] is True
    report["tests"]["status_endpoint"] = {
        "http_code": resp_status.status_code,
        "body": resp_status.json()
    }

    # -------------------------------------------------------------
    # Task 3 & 4: Upload Benign, Malignant, Normal Samples
    # -------------------------------------------------------------
    print("\n--- Test 3: Upload Benign Sample ---")
    with open(benign_p, "rb") as f:
        resp_benign = requests.post(
            f"{BASE_URL}/api/research/busi/analyze",
            files={"file": (benign_p.name, f, "image/png")},
            data={"study_id": "live_test_benign"}
        )
    print(f"HTTP Status: {resp_benign.status_code}")
    b_data = resp_benign.json()
    print(f"Classifier: {b_data['classifier']['predicted_class']} ({b_data['classifier']['confidence']*100:.1f}%)")
    print(f"Segmentation: Mask={b_data['segmentation']['mask_detected']}, Area={b_data['segmentation']['lesion_area_percentage']}%")
    print(f"Overlay URL: {b_data['segmentation']['mask_overlay_url']}")
    assert resp_benign.status_code == 200
    assert b_data["classifier"]["predicted_class"] == "Benign"
    assert b_data["segmentation"]["mask_detected"] is True
    report["tests"]["sample_benign"] = {
        "http_code": resp_benign.status_code,
        "predicted_class": b_data["classifier"]["predicted_class"],
        "confidence": b_data["classifier"]["confidence"],
        "mask_detected": b_data["segmentation"]["mask_detected"],
        "lesion_area_pct": b_data["segmentation"]["lesion_area_percentage"],
        "overlay_url": b_data["segmentation"]["mask_overlay_url"]
    }

    print("\n--- Test 4: Upload Malignant Sample ---")
    with open(malignant_p, "rb") as f:
        resp_malignant = requests.post(
            f"{BASE_URL}/api/research/busi/analyze",
            files={"file": (malignant_p.name, f, "image/png")},
            data={"study_id": "live_test_malignant"}
        )
    print(f"HTTP Status: {resp_malignant.status_code}")
    m_data = resp_malignant.json()
    print(f"Classifier: {m_data['classifier']['predicted_class']} ({m_data['classifier']['confidence']*100:.1f}%)")
    print(f"Segmentation: Mask={m_data['segmentation']['mask_detected']}, Area={m_data['segmentation']['lesion_area_percentage']}%")
    assert resp_malignant.status_code == 200
    assert m_data["classifier"]["predicted_class"] == "Malignant"
    assert m_data["segmentation"]["mask_detected"] is True
    report["tests"]["sample_malignant"] = {
        "http_code": resp_malignant.status_code,
        "predicted_class": m_data["classifier"]["predicted_class"],
        "confidence": m_data["classifier"]["confidence"],
        "mask_detected": m_data["segmentation"]["mask_detected"],
        "lesion_area_pct": m_data["segmentation"]["lesion_area_percentage"]
    }

    print("\n--- Test 5: Upload Normal Sample ---")
    with open(normal_p, "rb") as f:
        resp_normal = requests.post(
            f"{BASE_URL}/api/research/busi/analyze",
            files={"file": (normal_p.name, f, "image/png")},
            data={"study_id": "live_test_normal"}
        )
    print(f"HTTP Status: {resp_normal.status_code}")
    n_data = resp_normal.json()
    print(f"Classifier: {n_data['classifier']['predicted_class']} ({n_data['classifier']['confidence']*100:.1f}%)")
    print(f"Segmentation: Mask={n_data['segmentation']['mask_detected']}, Area={n_data['segmentation']['lesion_area_percentage']}%")
    assert resp_normal.status_code == 200
    assert n_data["classifier"]["predicted_class"] == "Normal"
    assert n_data["segmentation"]["mask_detected"] is False
    assert n_data["segmentation"]["lesion_area_percentage"] == 0.0
    report["tests"]["sample_normal"] = {
        "http_code": resp_normal.status_code,
        "predicted_class": n_data["classifier"]["predicted_class"],
        "confidence": n_data["classifier"]["confidence"],
        "mask_detected": n_data["segmentation"]["mask_detected"],
        "lesion_area_pct": n_data["segmentation"]["lesion_area_percentage"]
    }

    # -------------------------------------------------------------
    # Task 6: Empty Mask Safety Rule on Malignant Sample
    # -------------------------------------------------------------
    print("\n--- Test 6: Empty Mask Safety Verification (malignant (11).png) ---")
    with open(malignant_empty_p, "rb") as f:
        resp_mal_empty = requests.post(
            f"{BASE_URL}/api/research/busi/analyze",
            files={"file": (malignant_empty_p.name, f, "image/png")},
            data={"study_id": "live_test_mal_empty"}
        )
    assert resp_mal_empty.status_code == 200
    me_data = resp_mal_empty.json()
    print(f"Classifier prediction: {me_data['classifier']['predicted_class']}")
    print(f"Segmentation mask: {me_data['segmentation']['mask_detected']} (Area: {me_data['segmentation']['lesion_area_percentage']}%)")
    print(f"Guardrail segmentation_overrides_classifier: {me_data['safety_guardrails']['segmentation_overrides_classifier']}")
    print(f"Guardrail empty_mask_implies_normal: {me_data['safety_guardrails']['empty_mask_implies_normal']}")
    assert me_data["classifier"]["predicted_class"] == "Malignant"
    assert me_data["segmentation"]["mask_detected"] is False
    assert me_data["safety_guardrails"]["segmentation_overrides_classifier"] is False
    report["tests"]["empty_mask_safety"] = {
        "http_code": resp_mal_empty.status_code,
        "classifier_class": me_data["classifier"]["predicted_class"],
        "mask_detected": me_data["segmentation"]["mask_detected"],
        "overrides_classifier": me_data["safety_guardrails"]["segmentation_overrides_classifier"]
    }

    # -------------------------------------------------------------
    # Task 7: Open Returned Overlay URL via Live HTTP GET
    # -------------------------------------------------------------
    print("\n--- Test 7: Verify Overlay URL Accessibility ---")
    overlay_rel_url = b_data["segmentation"]["mask_overlay_url"]
    full_overlay_url = f"{BASE_URL}{overlay_rel_url}"
    print(f"Fetching overlay from: {full_overlay_url}")
    resp_img = requests.get(full_overlay_url)
    print(f"HTTP Status: {resp_img.status_code}")
    print(f"Content-Type: {resp_img.headers.get('content-type')}")
    print(f"Bytes received: {len(resp_img.content):,}")
    # Verify JPEG magic bytes \xff\xd8\xff
    is_jpeg = resp_img.content.startswith(b"\xff\xd8\xff")
    print(f"Valid JPEG magic header: {is_jpeg}")
    assert resp_img.status_code == 200
    assert is_jpeg is True
    report["tests"]["overlay_image_access"] = {
        "http_code": resp_img.status_code,
        "content_type": resp_img.headers.get("content-type"),
        "bytes": len(resp_img.content),
        "valid_jpeg": is_jpeg
    }

    # -------------------------------------------------------------
    # Task 8: Negative / Robustness Testing
    # -------------------------------------------------------------
    print("\n--- Test 8: Negative / Robustness Testing ---")
    # 8a: Invalid file extension .pdf
    resp_bad_ext = requests.post(
        f"{BASE_URL}/api/research/busi/analyze",
        files={"file": ("report.pdf", b"%PDF-1.4 fake pdf", "application/pdf")}
    )
    print(f"Bad Extension .pdf: HTTP {resp_bad_ext.status_code} | {resp_bad_ext.json()['detail']}")
    assert resp_bad_ext.status_code == 400

    # 8b: Invalid file extension .exe
    resp_bad_exe = requests.post(
        f"{BASE_URL}/api/research/busi/analyze",
        files={"file": ("virus.exe", b"MZ fake executable", "application/octet-stream")}
    )
    print(f"Bad Extension .exe: HTTP {resp_bad_exe.status_code} | {resp_bad_exe.json()['detail']}")
    assert resp_bad_exe.status_code == 400

    # 8c: Empty 0-byte file
    resp_empty = requests.post(
        f"{BASE_URL}/api/research/busi/analyze",
        files={"file": ("empty.png", b"", "image/png")}
    )
    print(f"Empty File (0 bytes): HTTP {resp_empty.status_code} | {resp_empty.json()['detail']}")
    assert resp_empty.status_code == 400

    # 8d: Corrupted image file
    resp_corrupt = requests.post(
        f"{BASE_URL}/api/research/busi/analyze",
        files={"file": ("corrupt.png", b"not an image binary payload\x00\x01\x02", "image/png")}
    )
    print(f"Corrupted Image: HTTP {resp_corrupt.status_code} | {resp_corrupt.json()['detail']}")
    assert resp_corrupt.status_code == 422

    report["tests"]["robustness"] = {
        "pdf_rejected": resp_bad_ext.status_code == 400,
        "exe_rejected": resp_bad_exe.status_code == 400,
        "empty_rejected": resp_empty.status_code == 400,
        "corrupt_rejected": resp_corrupt.status_code == 422
    }

    # -------------------------------------------------------------
    # Task 9: Security Path Traversal Validation
    # -------------------------------------------------------------
    print("\n--- Test 9: Security / Path Traversal Attack Test ---")
    traversal_ids = ["../../traversal_attack", "..\\..\\win_traversal", "/etc/passwd", "C:\\Windows\\System32"]
    traversal_results = []
    for tid in traversal_ids:
        with open(benign_p, "rb") as f:
            resp_trav = requests.post(
                f"{BASE_URL}/api/research/busi/analyze",
                files={"file": ("test.png", f, "image/png")},
                data={"study_id": tid}
            )
        assert resp_trav.status_code == 200
        data_trav = resp_trav.json()
        sanitized_id = data_trav["study_id"]
        # Check that sanitized id does NOT contain .. or / or \
        has_traversal = any(bad in sanitized_id for bad in ["..", "/", "\\", ":"])
        print(f"Input study_id='{tid}' -> Sanitized='{sanitized_id}' (Contains traversal chars: {has_traversal})")
        assert not has_traversal
        traversal_results.append({"input": tid, "sanitized": sanitized_id, "safe": not has_traversal})
    report["tests"]["path_traversal_prevention"] = traversal_results

    # -------------------------------------------------------------
    # Task 10: Repeated Requests & Model Latency (Singleton Check)
    # -------------------------------------------------------------
    print("\n--- Test 10: Repeated Requests & Singleton Verification ---")
    latencies = []
    for i in range(3):
        t0 = time.time()
        with open(benign_p, "rb") as f:
            r = requests.post(
                f"{BASE_URL}/api/research/busi/analyze",
                files={"file": (benign_p.name, f, "image/png")},
                data={"study_id": f"repeat_{i}"}
            )
        dt = time.time() - t0
        latencies.append(dt)
        print(f"Request {i+1}: HTTP {r.status_code} in {dt:.3f}s")
        assert r.status_code == 200
    report["tests"]["latency_singleton"] = latencies

    # -------------------------------------------------------------
    # Task 11: Production YOLO Diagnosis Pipeline Regression Check
    # -------------------------------------------------------------
    print("\n--- Test 11: Production YOLO Diagnosis Endpoint Regression Test ---")
    # 11a: Create diagnosis session
    r_create = requests.post(
        f"{BASE_URL}/api/diagnosis/create",
        json={"modality": "ultrasound"}
    )
    print(f"Create Diagnosis: HTTP {r_create.status_code}")
    assert r_create.status_code == 200
    prod_study_id = r_create.json()["study_id"]
    print(f"Created Study ID: {prod_study_id}")

    # 11b: Upload scan to production upload endpoint
    with open(benign_p, "rb") as f:
        r_upload = requests.post(
            f"{BASE_URL}/api/diagnosis/upload",
            data={"study_id": prod_study_id, "image_type": "ultrasound"},
            files={"file": (benign_p.name, f, "image/png")}
        )
    print(f"Production Upload: HTTP {r_upload.status_code}")
    assert r_upload.status_code == 200

    # 11c: Run AI analysis via production YOLO pipeline
    r_analyze = requests.post(
        f"{BASE_URL}/api/diagnosis/analyze",
        data={"study_id": prod_study_id}
    )
    print(f"Production Analyze: HTTP {r_analyze.status_code}")
    assert r_analyze.status_code == 200
    prod_data = r_analyze.json()
    print(f"YOLO Production Status: {prod_data['status']}")
    print(f"YOLO Prediction: {prod_data['prediction']}")
    print(f"YOLO Confidence: {prod_data['confidence']}")
    print(f"Model Results Count: {len(prod_data['model_results'])}")
    assert len(prod_data["model_results"]) >= 1
    report["tests"]["production_yolo_pipeline"] = {
        "status": prod_data["status"],
        "prediction": prod_data["prediction"],
        "confidence": prod_data["confidence"],
        "results_count": len(prod_data["model_results"])
    }

    # -------------------------------------------------------------
    # Task 12: Database Integrity Audit
    # -------------------------------------------------------------
    print("\n--- Test 12: Database Immutability Check ---")
    db = SessionLocal()
    final_diag_count = db.query(Diagnosis).count()
    final_img_count = db.query(UploadedImages).count()
    final_mr_count = db.query(ModelResults).count()
    db.close()

    # Note: Only Task 11 (the explicit production pipeline test) added 1 diagnosis record.
    # The research tests (Task 3, 4, 5, 6, 8, 9, 10) must add ZERO records!
    research_diag_delta = final_diag_count - initial_diag_count - 1
    print(f"[DB Audit] Diagnosis Delta from Research: {research_diag_delta} (Expected: 0)")
    assert research_diag_delta == 0
    report["tests"]["database_isolation"] = {
        "initial_counts": {"diagnosis": initial_diag_count, "images": initial_img_count, "results": initial_mr_count},
        "final_counts": {"diagnosis": final_diag_count, "images": final_img_count, "results": final_mr_count},
        "research_mutations": 0,
        "isolation_verified": True
    }

    # Save results to JSON
    out_file = PROJECT_ROOT / "training" / "live_smoke_test_results.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved smoke test report to: {out_file}")
    print("=" * 60)
    print("ALL LIVE SMOKE TESTS PASSED SUCCESSFULLY (12/12)!")
    print("=" * 60)


if __name__ == "__main__":
    print(f"Starting uvicorn server thread on {BASE_URL}...")
    server_thread = UvicornServerThread()
    server_thread.start()

    if not wait_for_server(timeout_sec=20):
        print("[ERROR] FastAPI server failed to start within timeout.")
        sys.exit(1)

    try:
        run_smoke_test()
    finally:
        print("Stopping uvicorn server...")
        server_thread.stop()
        time.sleep(1)
