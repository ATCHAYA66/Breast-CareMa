"""Automated end-to-end integration and smoke test for Step 7: Frontend Integration - BUSI Research Module.
Tests:
1. Built SPA asset serving (HTML, JS bundle with BUSI research code).
2. Direct API calls matching frontend service payload format over real HTTP.
3. Benign, Malignant, Normal responses.
4. Empty-mask malignant case independence.
5. Overlay URL accessibility.
6. Negative input handling (.pdf, .exe, 0-byte, corrupt).
7. Production YOLO workflow regression check.
8. Database isolation check.
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
from backend.database.connection import SessionLocal
from backend.database.models import Diagnosis, UploadedImages, ModelResults

HOST = "127.0.0.1"
PORT = 8002
BASE_URL = f"http://{HOST}:{PORT}"

print("[Init] Pre-loading backend application and models in main thread...", flush=True)
from backend.main import app
print("[Init] Backend application ready.", flush=True)

BUSI_DIR = PROJECT_ROOT / "datasets" / "BUSI"
BENIGN_SAMPLE = next(BUSI_DIR.rglob("benign (81).png"))
MALIGNANT_SAMPLE = next(BUSI_DIR.rglob("malignant (88).png"))
NORMAL_SAMPLE = next(BUSI_DIR.rglob("normal (109).png"))
EMPTY_MASK_MALIGNANT = next(BUSI_DIR.rglob("malignant (11).png"))


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


def count_db_rows():
    db = SessionLocal()
    try:
        diag = db.query(Diagnosis).count()
        imgs = db.query(UploadedImages).count()
        res = db.query(ModelResults).count()
        return {"diagnosis": diag, "images": imgs, "results": res}
    finally:
        db.close()


def run_tests():
    print("=" * 70, flush=True)
    print("STEP 7: FRONTEND INTEGRATION VERIFICATION TEST SUITE", flush=True)
    print("=" * 70, flush=True)

    server_thread = UvicornServerThread()
    server_thread.start()

    # Wait for server to become responsive
    max_wait = 20
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
    initial_db = count_db_rows()
    print(f"Initial DB counts: {initial_db}", flush=True)

    try:
        # Test 1: Frontend SPA HTML Serving
        print("\n[Test 1] Verifying SPA HTML Root Delivery...", flush=True)
        res = requests.get(f"{BASE_URL}/", timeout=5)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert "index-" in res.text, "Built JS chunk reference not found in HTML"
        assert 'id="root"' in res.text, "Root element not found in HTML"
        print("  -> Passed: Root index.html served with bundled production scripts.", flush=True)
        results["spa_html"] = {"status": "passed", "code": res.status_code}

        # Test 2: Bundled JavaScript includes BUSI Research strings
        print("\n[Test 2] Verifying Built JS Bundle Content...", flush=True)
        dist_assets = PROJECT_ROOT / "frontend" / "dist" / "assets"
        js_files = list(dist_assets.glob("index-*.js"))
        assert len(js_files) > 0, "No built JS asset found"
        js_content = js_files[0].read_text(encoding="utf-8")
        assert "BUSI Research Analysis" in js_content, "Page title string not in bundle"
        assert "/api/research/busi" in js_content or "/research/busi" in js_content, "API route not in bundle"
        assert "FOR ACADEMIC RESEARCH AND COMPARATIVE EVALUATION ONLY" in js_content, "Disclaimer not in bundle"
        print(f"  -> Passed: Found BUSI Research components and disclaimers in {js_files[0].name} ({len(js_content):,} chars).", flush=True)
        results["bundle_content"] = {"status": "passed", "file": js_files[0].name}

        # Test 3: SPA Route Rewriting
        print("\n[Test 3] Verifying SPA Client-Side Route Fallback...", flush=True)
        for route in ["/research/busi", "/diagnosis/new", "/models"]:
            r = requests.get(f"{BASE_URL}{route}", timeout=5)
            assert r.status_code == 200, f"Route {route} returned {r.status_code}"
            assert 'id="root"' in r.text
        print("  -> Passed: Client-side routes properly serve SPA fallback.", flush=True)
        results["spa_routing"] = {"status": "passed"}

        # Test 4: Model Status Endpoint
        print("\n[Test 4] Verifying GET /api/research/busi/status...", flush=True)
        status_res = requests.get(f"{BASE_URL}/api/research/busi/status", timeout=5)
        assert status_res.status_code == 200
        status_json = status_res.json()
        assert status_json["status"] == "ready"
        assert status_json["models"]["classifier"]["loaded"] is True
        assert status_json["models"]["segmenter"]["loaded"] is True
        print(f"  -> Passed: Status is 'ready', Classifier: {status_json['models']['classifier']['name']}, Segmenter: {status_json['models']['segmenter']['name']}", flush=True)
        results["model_status"] = {"status": "passed", "body": status_json}

        # Test 5: Benign Sample Analysis
        print("\n[Test 5] Verifying Benign Sample POST /api/research/busi/analyze...", flush=True)
        with open(BENIGN_SAMPLE, "rb") as f:
            files = {"file": ("benign (81).png", f, "image/png")}
            b_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files=files, data={"study_id": "FE_TEST_BENIGN"}, timeout=10)
        assert b_res.status_code == 200, f"Expected 200, got {b_res.status_code}: {b_res.text}"
        b_json = b_res.json()
        assert b_json["classifier"]["predicted_class"] == "Benign"
        assert b_json["classifier"]["confidence"] > 0.90
        assert b_json["segmentation"]["mask_detected"] is True
        assert b_json["segmentation"]["lesion_area_percentage"] > 0.0
        assert b_json["segmentation"]["mask_overlay_url"] is not None
        print(f"  -> Passed: Class={b_json['classifier']['predicted_class']} (Score: {b_json['classifier']['confidence']:.4f}), MaskDetected={b_json['segmentation']['mask_detected']}, Area={b_json['segmentation']['lesion_area_percentage']:.2f}%", flush=True)
        results["sample_benign"] = b_json

        # Test 6: Malignant Sample Analysis
        print("\n[Test 6] Verifying Malignant Sample POST /api/research/busi/analyze...", flush=True)
        with open(MALIGNANT_SAMPLE, "rb") as f:
            files = {"file": ("malignant (88).png", f, "image/png")}
            m_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files=files, data={"study_id": "FE_TEST_MALIGNANT"}, timeout=10)
        assert m_res.status_code == 200
        m_json = m_res.json()
        assert m_json["classifier"]["predicted_class"] == "Malignant"
        assert m_json["classifier"]["confidence"] > 0.90
        assert m_json["segmentation"]["mask_detected"] is True
        print(f"  -> Passed: Class={m_json['classifier']['predicted_class']} (Score: {m_json['classifier']['confidence']:.4f}), MaskDetected={m_json['segmentation']['mask_detected']}, Area={m_json['segmentation']['lesion_area_percentage']:.2f}%", flush=True)
        results["sample_malignant"] = m_json

        # Test 7: Normal Sample Analysis
        print("\n[Test 7] Verifying Normal Sample POST /api/research/busi/analyze...", flush=True)
        with open(NORMAL_SAMPLE, "rb") as f:
            files = {"file": ("normal (109).png", f, "image/png")}
            n_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files=files, data={"study_id": "FE_TEST_NORMAL"}, timeout=10)
        assert n_res.status_code == 200
        n_json = n_res.json()
        assert n_json["classifier"]["predicted_class"] == "Normal"
        assert n_json["classifier"]["confidence"] > 0.90
        assert n_json["segmentation"]["mask_detected"] is False
        assert n_json["segmentation"]["lesion_area_percentage"] == 0.0
        print(f"  -> Passed: Class={n_json['classifier']['predicted_class']} (Score: {n_json['classifier']['confidence']:.4f}), MaskDetected={n_json['segmentation']['mask_detected']}, Area=0.0%", flush=True)
        results["sample_normal"] = n_json

        # Test 8: Empty-Mask Malignant Edge Case
        print("\n[Test 8] Verifying Empty-Mask Malignant Edge Case (Safety Guardrail)...", flush=True)
        with open(EMPTY_MASK_MALIGNANT, "rb") as f:
            files = {"file": ("malignant (11).png", f, "image/png")}
            em_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files=files, data={"study_id": "FE_TEST_EMPTY_MASK"}, timeout=10)
        assert em_res.status_code == 200
        em_json = em_res.json()
        assert em_json["classifier"]["predicted_class"] == "Malignant"
        assert em_json["segmentation"]["mask_detected"] is False
        assert em_json["safety_guardrails"]["segmentation_overrides_classifier"] is False
        print(f"  -> Passed: Classifier kept '{em_json['classifier']['predicted_class']}' while MaskDetected={em_json['segmentation']['mask_detected']}. Guardrail respected.", flush=True)
        results["empty_mask_malignant"] = em_json

        # Test 9: Overlay Image Retrieval
        print("\n[Test 9] Verifying Overlay Image Retrieval via HTTP...", flush=True)
        overlay_url = b_json["segmentation"]["mask_overlay_url"]
        ov_res = requests.get(f"{BASE_URL}{overlay_url}", timeout=5)
        assert ov_res.status_code == 200, f"Overlay URL {overlay_url} returned {ov_res.status_code}"
        assert ov_res.headers["content-type"] in ["image/jpeg", "image/png"]
        assert len(ov_res.content) > 1000
        assert ov_res.content[:3] == b"\xff\xd8\xff", "Overlay is not a valid JPEG"
        print(f"  -> Passed: Overlay retrieved successfully ({len(ov_res.content):,} bytes, valid JPEG magic bytes).", flush=True)
        results["overlay_retrieval"] = {"status": "passed", "bytes": len(ov_res.content)}

        # Test 10: Negative Input Robustness
        print("\n[Test 10] Verifying Negative Inputs Handling...", flush=True)
        # .pdf
        pdf_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")})
        assert pdf_res.status_code == 400
        # .exe
        exe_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files={"file": ("test.exe", b"MZ...", "application/octet-stream")})
        assert exe_res.status_code == 400
        # 0 bytes
        empty_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files={"file": ("empty.png", b"", "image/png")})
        assert empty_res.status_code == 400
        # Corrupt image
        corrupt_res = requests.post(f"{BASE_URL}/api/research/busi/analyze", files={"file": ("corrupt.png", b"Not an image at all!", "image/png")})
        assert corrupt_res.status_code == 422
        print("  -> Passed: .pdf (400), .exe (400), empty (400), corrupt (422) rejected cleanly.", flush=True)
        results["negative_inputs"] = {"status": "passed"}

        # Test 11: Production YOLO Regression
        print("\n[Test 11] Verifying Production YOLO Pipeline Unchanged...", flush=True)
        session_res = requests.post(f"{BASE_URL}/api/diagnosis/create", json={"patient_id": "FE-PT-001", "modality": "ultrasound"})
        assert session_res.status_code == 200
        study_id = session_res.json()["study_id"]
        with open(BENIGN_SAMPLE, "rb") as f:
            up_res = requests.post(
                f"{BASE_URL}/api/diagnosis/upload",
                data={"study_id": study_id, "image_type": "ultrasound"},
                files={"file": ("scan.png", f, "image/png")}
            )
        assert up_res.status_code == 200
        ana_res = requests.post(f"{BASE_URL}/api/diagnosis/analyze", data={"study_id": study_id})
        assert ana_res.status_code == 200
        ana_json = ana_res.json()
        assert ana_json["status"] == "completed"
        assert ana_json["prediction"] == "Inconclusive"
        print(f"  -> Passed: Production YOLO diagnosis returned '{ana_json['prediction']}' without regression.", flush=True)
        results["production_yolo"] = {"status": "passed", "prediction": ana_json["prediction"]}

        # Test 12: DB Isolation Check
        final_db = count_db_rows()
        print(f"\n[Test 12] Final DB Counts: {final_db}", flush=True)
        expected_delta = {"diagnosis": 1, "images": 1, "results": 1}
        actual_delta = {k: final_db[k] - initial_db[k] for k in initial_db}
        assert actual_delta == expected_delta, f"Unexpected DB mutation: {actual_delta}"
        print("  -> Passed: Zero database mutations caused by BUSI research calls.", flush=True)
        results["db_isolation"] = {"status": "passed", "delta": actual_delta}

        # Save output
        output_path = PROJECT_ROOT / "training" / "frontend_integration_test_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nAll 12 tests PASSED. Telemetry written to {output_path}", flush=True)

    finally:
        server_thread.stop()


if __name__ == "__main__":
    run_tests()
