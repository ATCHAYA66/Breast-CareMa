"""Full Live HTTP/ASGI Smoke Test Suite for BREAST CARE-MA Backend API.
Uses httpx.ASGITransport directly on the FastAPI app instance, verifying:
1. GET /api/research/busi/status (HTTP 200, valid JSON)
2. POST /api/research/busi/analyze (Benign, Malignant, Normal multipart uploads)
3. Independence of classifier and segmentation
4. Empty mask safety rule (malignant (11).png)
5. Overlay URL accessibility via HTTP GET (returns HTTP 200 and valid JPEG header)
6. Negative & robustness tests (.pdf, .exe, 0-byte, corrupt image)
7. Security / Path Traversal validation on study_id
8. Repeated requests & model latency (singleton verification)
9. Production YOLO pipeline regression test
10. Database immutability audit (0 mutations from research)
"""
import asyncio
import io
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from backend.main import app
from backend.database.connection import SessionLocal
from backend.database.models import Diagnosis, UploadedImages, ModelResults

BASE_URL = "http://127.0.0.1:8000"


async def run_full_smoke_test():
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transport": "httpx.AsyncClient(ASGITransport) (Full FastAPI HTTP Stack)",
        "tests": {}
    }

    # 1. Database initial audit
    db = SessionLocal()
    init_diag = db.query(Diagnosis).count()
    init_img = db.query(UploadedImages).count()
    init_mr = db.query(ModelResults).count()
    db.close()
    print(f"[DB Audit] Initial counts: Diagnosis={init_diag}, Images={init_img}, Results={init_mr}")

    # Locate sample test images from BUSI dataset
    busi_dir = PROJECT_ROOT / "datasets" / "BUSI"
    benign_p = next(busi_dir.rglob("benign (81).png"))
    malignant_p = next(busi_dir.rglob("malignant (88).png"))
    malignant_empty_p = next(busi_dir.rglob("malignant (11).png"))
    normal_p = next(busi_dir.rglob("normal (109).png"))

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL, timeout=60.0) as client:

        # -------------------------------------------------------------
        # Task 2: GET /api/research/busi/status
        # -------------------------------------------------------------
        print("\n--- Task 2: GET /api/research/busi/status ---")
        resp_status = await client.get("/api/research/busi/status")
        print(f"HTTP Status: {resp_status.status_code}")
        print(f"Response Body: {json.dumps(resp_status.json(), indent=2)}")
        assert resp_status.status_code == 200
        status_body = resp_status.json()
        assert status_body["status"] == "ready"
        assert status_body["models"]["classifier"]["loaded"] is True
        assert status_body["models"]["segmenter"]["loaded"] is True
        assert status_body["models"]["classifier"]["classes"] == ["Benign", "Malignant", "Normal"]
        report["tests"]["status_endpoint"] = {
            "http_code": resp_status.status_code,
            "response": status_body
        }

        # -------------------------------------------------------------
        # Task 3 & 4: Upload Benign, Malignant, Normal Samples
        # -------------------------------------------------------------
        print("\n--- Task 3: Upload Benign Sample ---")
        with open(benign_p, "rb") as f:
            resp_benign = await client.post(
                "/api/research/busi/analyze",
                files={"file": (benign_p.name, f.read(), "image/png")},
                data={"study_id": "smoke_test_benign"}
            )
        print(f"HTTP Status: {resp_benign.status_code}")
        b_data = resp_benign.json()
        print(f"Classifier: {b_data['classifier']['predicted_class']} ({b_data['classifier']['confidence']*100:.1f}%)")
        print(f"Class Probs: {b_data['classifier']['class_probabilities']}")
        print(f"Segmentation: Mask={b_data['segmentation']['mask_detected']}, Area={b_data['segmentation']['lesion_area_percentage']}%")
        print(f"Overlay URL: {b_data['segmentation']['mask_overlay_url']}")
        assert resp_benign.status_code == 200
        assert b_data["status"] == "success"
        assert b_data["classifier"]["predicted_class"] == "Benign"
        assert b_data["segmentation"]["mask_detected"] is True
        report["tests"]["sample_benign"] = {
            "http_code": resp_benign.status_code,
            "classifier": b_data["classifier"],
            "segmentation": b_data["segmentation"]
        }

        print("\n--- Task 4: Upload Malignant Sample ---")
        with open(malignant_p, "rb") as f:
            resp_malignant = await client.post(
                "/api/research/busi/analyze",
                files={"file": (malignant_p.name, f.read(), "image/png")},
                data={"study_id": "smoke_test_malignant"}
            )
        print(f"HTTP Status: {resp_malignant.status_code}")
        m_data = resp_malignant.json()
        print(f"Classifier: {m_data['classifier']['predicted_class']} ({m_data['classifier']['confidence']*100:.1f}%)")
        print(f"Class Probs: {m_data['classifier']['class_probabilities']}")
        print(f"Segmentation: Mask={m_data['segmentation']['mask_detected']}, Area={m_data['segmentation']['lesion_area_percentage']}%")
        assert resp_malignant.status_code == 200
        assert m_data["classifier"]["predicted_class"] == "Malignant"
        assert m_data["segmentation"]["mask_detected"] is True
        report["tests"]["sample_malignant"] = {
            "http_code": resp_malignant.status_code,
            "classifier": m_data["classifier"],
            "segmentation": m_data["segmentation"]
        }

        print("\n--- Task 5: Upload Normal Sample ---")
        with open(normal_p, "rb") as f:
            resp_normal = await client.post(
                "/api/research/busi/analyze",
                files={"file": (normal_p.name, f.read(), "image/png")},
                data={"study_id": "smoke_test_normal"}
            )
        print(f"HTTP Status: {resp_normal.status_code}")
        n_data = resp_normal.json()
        print(f"Classifier: {n_data['classifier']['predicted_class']} ({n_data['classifier']['confidence']*100:.1f}%)")
        print(f"Class Probs: {n_data['classifier']['class_probabilities']}")
        print(f"Segmentation: Mask={n_data['segmentation']['mask_detected']}, Area={n_data['segmentation']['lesion_area_percentage']}%")
        print(f"Interpretation: {n_data['segmentation']['interpretation']}")
        assert resp_normal.status_code == 200
        assert n_data["classifier"]["predicted_class"] == "Normal"
        assert n_data["segmentation"]["mask_detected"] is False
        assert n_data["segmentation"]["lesion_area_percentage"] == 0.0
        report["tests"]["sample_normal"] = {
            "http_code": resp_normal.status_code,
            "classifier": n_data["classifier"],
            "segmentation": n_data["segmentation"]
        }

        # -------------------------------------------------------------
        # Task 6: Empty Mask Safety Rule on Malignant Sample
        # -------------------------------------------------------------
        print("\n--- Task 6: Empty Mask Safety Rule (malignant (11).png) ---")
        with open(malignant_empty_p, "rb") as f:
            resp_mal_empty = await client.post(
                "/api/research/busi/analyze",
                files={"file": (malignant_empty_p.name, f.read(), "image/png")},
                data={"study_id": "smoke_test_mal_empty"}
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
        assert me_data["safety_guardrails"]["empty_mask_implies_normal"] is False
        report["tests"]["empty_mask_safety"] = {
            "http_code": resp_mal_empty.status_code,
            "classifier_class": me_data["classifier"]["predicted_class"],
            "mask_detected": me_data["segmentation"]["mask_detected"],
            "overrides_classifier": me_data["safety_guardrails"]["segmentation_overrides_classifier"]
        }

        # -------------------------------------------------------------
        # Task 7: Fetch Returned Overlay URL via HTTP GET
        # -------------------------------------------------------------
        print("\n--- Task 7: Verify Overlay URL Accessibility ---")
        overlay_url = b_data["segmentation"]["mask_overlay_url"]
        print(f"GET {overlay_url}")
        resp_img = await client.get(overlay_url)
        print(f"HTTP Status: {resp_img.status_code}")
        print(f"Content-Type: {resp_img.headers.get('content-type')}")
        print(f"Bytes received: {len(resp_img.content):,}")
        is_jpeg = resp_img.content.startswith(b"\xff\xd8\xff")
        print(f"Valid JPEG magic header: {is_jpeg}")
        assert resp_img.status_code == 200
        assert is_jpeg is True
        report["tests"]["overlay_image_access"] = {
            "http_code": resp_img.status_code,
            "url": overlay_url,
            "bytes": len(resp_img.content),
            "valid_jpeg": is_jpeg
        }

        # -------------------------------------------------------------
        # Task 8: Negative & Robustness Testing
        # -------------------------------------------------------------
        print("\n--- Task 8: Negative & Robustness Testing ---")
        # 8a: Invalid file extension .pdf
        resp_bad_pdf = await client.post(
            "/api/research/busi/analyze",
            files={"file": ("test.pdf", b"%PDF-1.4 fake pdf", "application/pdf")}
        )
        print(f"Bad extension .pdf -> HTTP {resp_bad_pdf.status_code}: {resp_bad_pdf.json()['detail']}")
        assert resp_bad_pdf.status_code == 400

        # 8b: Invalid file extension .exe
        resp_bad_exe = await client.post(
            "/api/research/busi/analyze",
            files={"file": ("evil.exe", b"MZ fake executable", "application/octet-stream")}
        )
        print(f"Bad extension .exe -> HTTP {resp_bad_exe.status_code}: {resp_bad_exe.json()['detail']}")
        assert resp_bad_exe.status_code == 400

        # 8c: Empty 0-byte file
        resp_empty = await client.post(
            "/api/research/busi/analyze",
            files={"file": ("empty.png", b"", "image/png")}
        )
        print(f"Empty 0-byte file -> HTTP {resp_empty.status_code}: {resp_empty.json()['detail']}")
        assert resp_empty.status_code == 400

        # 8d: Corrupted image file
        resp_corrupt = await client.post(
            "/api/research/busi/analyze",
            files={"file": ("corrupt.png", b"random bytes not image \x00\x01\x02", "image/png")}
        )
        print(f"Corrupted image -> HTTP {resp_corrupt.status_code}: {resp_corrupt.json()['detail']}")
        assert resp_corrupt.status_code == 422

        report["tests"]["robustness"] = {
            "pdf_status": resp_bad_pdf.status_code,
            "exe_status": resp_bad_exe.status_code,
            "empty_status": resp_empty.status_code,
            "corrupt_status": resp_corrupt.status_code
        }

        # -------------------------------------------------------------
        # Task 9: Security / Path Traversal Validation
        # -------------------------------------------------------------
        print("\n--- Task 9: Security / Path Traversal Validation ---")
        traversal_payloads = [
            "../../escape_dir",
            "..\\..\\win_escape",
            "/etc/shadow",
            "C:\\Windows\\System32\\cmd.exe",
            "safe_study_123"
        ]
        trav_results = []
        for tid in traversal_payloads:
            with open(benign_p, "rb") as f:
                r_trav = await client.post(
                    "/api/research/busi/analyze",
                    files={"file": ("test.png", f.read(), "image/png")},
                    data={"study_id": tid}
                )
            assert r_trav.status_code == 200
            sanitized = r_trav.json()["study_id"]
            has_traversal = any(bad in sanitized for bad in ["..", "/", "\\", ":"])
            print(f"Payload: '{tid}' -> Sanitized Study ID: '{sanitized}' (Safe: {not has_traversal})")
            assert not has_traversal
            trav_results.append({"payload": tid, "sanitized": sanitized, "safe": not has_traversal})
        report["tests"]["path_traversal_validation"] = trav_results

        # -------------------------------------------------------------
        # Task 10: Repeated Requests & Model Latency (Singleton Check)
        # -------------------------------------------------------------
        print("\n--- Task 10: Repeated Requests & Singleton Latency ---")
        latencies = []
        for i in range(3):
            t0 = time.time()
            with open(benign_p, "rb") as f:
                r_rep = await client.post(
                    "/api/research/busi/analyze",
                    files={"file": (benign_p.name, f.read(), "image/png")},
                    data={"study_id": f"repeat_{i+1}"}
                )
            dt = time.time() - t0
            latencies.append(round(dt, 3))
            print(f"Call {i+1}: HTTP {r_rep.status_code} in {dt:.3f}s")
            assert r_rep.status_code == 200
        report["tests"]["repeated_request_latencies_sec"] = latencies

        # -------------------------------------------------------------
        # Task 11: Production YOLO Diagnosis Pipeline Regression Check
        # -------------------------------------------------------------
        print("\n--- Task 11: Production YOLO Diagnosis Pipeline Regression ---")
        r_create = await client.post("/api/diagnosis/create", json={"modality": "ultrasound"})
        print(f"POST /api/diagnosis/create -> HTTP {r_create.status_code}")
        assert r_create.status_code == 200
        prod_study_id = r_create.json()["study_id"]
        print(f"Created Study ID: {prod_study_id}")

        with open(benign_p, "rb") as f:
            r_up = await client.post(
                "/api/diagnosis/upload",
                data={"study_id": prod_study_id, "image_type": "ultrasound"},
                files={"file": (benign_p.name, f.read(), "image/png")}
            )
        print(f"POST /api/diagnosis/upload -> HTTP {r_up.status_code}")
        assert r_up.status_code == 200

        r_an = await client.post(
            "/api/diagnosis/analyze",
            data={"study_id": prod_study_id}
        )
        print(f"POST /api/diagnosis/analyze -> HTTP {r_an.status_code}")
        assert r_an.status_code == 200
        prod_res = r_an.json()
        print(f"YOLO Diagnosis Status: {prod_res['status']}")
        print(f"YOLO Prediction: {prod_res['prediction']}")
        print(f"YOLO Confidence: {prod_res['confidence']}")
        print(f"Model Results: {len(prod_res['model_results'])} records")
        assert len(prod_res["model_results"]) >= 1
        report["tests"]["yolo_regression"] = {
            "http_create": r_create.status_code,
            "http_upload": r_up.status_code,
            "http_analyze": r_an.status_code,
            "yolo_status": prod_res["status"],
            "yolo_prediction": prod_res["prediction"],
            "model_results_count": len(prod_res["model_results"])
        }

    # -------------------------------------------------------------
    # Task 12: Database Immutability Check
    # -------------------------------------------------------------
    print("\n--- Task 12: Database Immutability Check ---")
    db = SessionLocal()
    final_diag = db.query(Diagnosis).count()
    final_img = db.query(UploadedImages).count()
    final_mr = db.query(ModelResults).count()
    db.close()

    # Only Task 11 (the explicit YOLO test) added 1 diagnosis record and 1 image and 1 result.
    # The research tests (Tasks 3, 4, 5, 6, 8, 9, 10) added ZERO database records!
    research_diag_delta = final_diag - init_diag - 1
    research_img_delta = final_img - init_img - 1
    research_mr_delta = final_mr - init_mr - 1
    print(f"Database Delta from Research Calls: Diagnosis={research_diag_delta}, Images={research_img_delta}, Results={research_mr_delta}")
    assert research_diag_delta == 0
    assert research_img_delta == 0
    assert research_mr_delta == 0
    report["tests"]["database_isolation"] = {
        "initial_counts": {"diagnosis": init_diag, "images": init_img, "results": init_mr},
        "final_counts": {"diagnosis": final_diag, "images": final_img, "results": final_mr},
        "research_mutations": 0,
        "isolation_verified": True
    }

    # Save complete JSON report
    out_p = PROJECT_ROOT / "training" / "live_smoke_test_results.json"
    out_p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved smoke test report to: {out_p}")
    print("=" * 65)
    print("ALL 12 LIVE HTTP/ASGI SMOKE TESTS PASSED (100% SUCCESS)!")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(run_full_smoke_test())
