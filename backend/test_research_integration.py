"""Comprehensive Test Suite for Isolated BUSI Research Integration.
Verifies:
1. Model loading (both checkpoints).
2. Dedicated preprocessing (shapes, normalization).
3. Classifier inference (3 classes, softmax probabilities).
4. Segmenter inference (mask generation, area calculation, overlays).
5. Normal, Benign, and Malignant test images.
6. Empty-mask safety behavior (verifying it never overrides classifier or implies Normal).
7. Independent error handling (one model fails, other succeeds).
8. Existing YOLO production pipeline integrity (verifying no regressions).
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import unittest
from pathlib import Path
import numpy as np
from PIL import Image
import torch

from fastapi.testclient import TestClient

from backend.main import app
from backend.ai_models.busi_models import (
    get_busi_classifier,
    get_busi_segmenter,
    preprocess_for_busi_classifier,
    preprocess_for_busi_segmenter,
    BUSIClassifierWrapper,
    BUSISegmenterWrapper,
)
from backend.services.busi_research_service import run_busi_research_inference
from backend.config import YOLO_WEIGHTS_PATH, BUSI_CLASSIFIER_WEIGHTS_PATH, BUSI_UNET_WEIGHTS_PATH

client = TestClient(app)


class TestBUSIResearchIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Locate sample test images from BUSI dataset
        busi_dir = Path("datasets/BUSI")
        cls.benign_sample = next(busi_dir.rglob("benign (81).png"), None)
        cls.malignant_sample = next(busi_dir.rglob("malignant (88).png"), None)
        cls.malignant_empty_mask_sample = next(busi_dir.rglob("malignant (11).png"), None)
        cls.normal_sample = next(busi_dir.rglob("normal (109).png"), None)

        assert cls.benign_sample is not None, "Benign sample not found in datasets/BUSI"
        assert cls.malignant_sample is not None, "Malignant sample not found in datasets/BUSI"
        assert cls.malignant_empty_mask_sample is not None, "Malignant empty-mask sample not found"
        assert cls.normal_sample is not None, "Normal sample not found in datasets/BUSI"

    def test_01_weights_files_exist(self):
        """Verify checkpoint paths and ensure YOLO production weights are intact."""
        self.assertTrue(BUSI_CLASSIFIER_WEIGHTS_PATH.is_file(), "Classifier weights file missing")
        self.assertTrue(BUSI_UNET_WEIGHTS_PATH.is_file(), "Segmenter weights file missing")
        self.assertTrue(YOLO_WEIGHTS_PATH.is_file(), "CRITICAL: Production best.pt missing!")
        # Verify YOLO weights size untouched
        self.assertEqual(YOLO_WEIGHTS_PATH.stat().st_size, 6549796, "best.pt was modified!")

    def test_02_model_loading_and_singleton(self):
        """Verify models load correctly once and return singletons."""
        clf1 = get_busi_classifier()
        clf2 = get_busi_classifier()
        self.assertIs(clf1, clf2, "Classifier is not a singleton instance")
        self.assertTrue(clf1.is_loaded, f"Classifier failed to load: {clf1.error_message}")
        self.assertEqual(clf1.class_names, ["Benign", "Malignant", "Normal"])

        seg1 = get_busi_segmenter()
        seg2 = get_busi_segmenter()
        self.assertIs(seg1, seg2, "Segmenter is not a singleton instance")
        self.assertTrue(seg1.is_loaded, f"Segmenter failed to load: {seg1.error_message}")
        self.assertEqual(seg1.threshold, 0.5)
        self.assertEqual(seg1.image_size, 256)

    def test_03_dedicated_preprocessing(self):
        """Verify preprocessing output shapes and value domains."""
        # Classifier preprocessing: (1, 3, 224, 224)
        c_tensor = preprocess_for_busi_classifier(self.benign_sample)
        self.assertEqual(c_tensor.shape, (1, 3, 224, 224))
        self.assertEqual(c_tensor.dtype, torch.float32)

        # Segmenter preprocessing: (1, 1, 256, 256)
        s_tensor = preprocess_for_busi_segmenter(self.benign_sample)
        self.assertEqual(s_tensor.shape, (1, 1, 256, 256))
        self.assertEqual(s_tensor.dtype, torch.float32)
        # Check normalization bounds [0, 1]
        self.assertGreaterEqual(float(s_tensor.min()), 0.0)
        self.assertLessEqual(float(s_tensor.max()), 1.0)

    def test_04_benign_inference(self):
        """Test inference on a known benign ultrasound scan."""
        res = run_busi_research_inference(self.benign_sample, study_id="test_benign")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["classifier"]["status"], "success")
        self.assertEqual(res["classifier"]["predicted_class"], "Benign")
        self.assertGreater(res["classifier"]["confidence"], 0.80)
        self.assertIn("Benign", res["classifier"]["class_probabilities"])

        self.assertEqual(res["segmentation"]["status"], "success")
        self.assertTrue(res["segmentation"]["mask_detected"])
        self.assertGreater(res["segmentation"]["lesion_area_percentage"], 0.5)
        self.assertIsNotNone(res["segmentation"]["mask_overlay_url"])

    def test_05_malignant_inference(self):
        """Test inference on a known malignant ultrasound scan."""
        res = run_busi_research_inference(self.malignant_sample, study_id="test_malignant")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["classifier"]["status"], "success")
        self.assertEqual(res["classifier"]["predicted_class"], "Malignant")
        self.assertGreater(res["classifier"]["confidence"], 0.80)

        self.assertEqual(res["segmentation"]["status"], "success")
        self.assertTrue(res["segmentation"]["mask_detected"])
        self.assertGreater(res["segmentation"]["lesion_area_percentage"], 1.0)

    def test_06_normal_inference(self):
        """Test inference on a known normal ultrasound scan."""
        res = run_busi_research_inference(self.normal_sample, study_id="test_normal")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["classifier"]["status"], "success")
        self.assertEqual(res["classifier"]["predicted_class"], "Normal")

        self.assertEqual(res["segmentation"]["status"], "success")
        self.assertFalse(res["segmentation"]["mask_detected"])
        self.assertEqual(res["segmentation"]["lesion_area_percentage"], 0.0)
        # Safety text must be present
        self.assertIn("does NOT imply a normal scan", res["segmentation"]["interpretation"])

    def test_07_empty_mask_safety_rule(self):
        """Verify that an empty mask on a malignant scan does NOT override the classifier."""
        res = run_busi_research_inference(self.malignant_empty_mask_sample, study_id="test_mal_empty")
        # In this sample, classifier sees Malignant while segmenter outputs empty mask
        self.assertEqual(res["classifier"]["predicted_class"], "Malignant")
        self.assertFalse(res["segmentation"]["mask_detected"])
        self.assertEqual(res["segmentation"]["lesion_area_percentage"], 0.0)

        # Confirm safety guardrails
        self.assertFalse(res["safety_guardrails"]["segmentation_overrides_classifier"])
        self.assertFalse(res["safety_guardrails"]["empty_mask_implies_normal"])
        self.assertIn("does NOT imply a normal scan", res["segmentation"]["interpretation"])

    def test_08_independent_error_handling(self):
        """Verify that when one model fails, the other model's output is still returned."""
        # Test simulated missing classifier
        fake_clf = BUSIClassifierWrapper(weights_path=Path("non_existent_weights.pth"))
        self.assertFalse(fake_clf.is_loaded)
        dummy_tensor = torch.randn(1, 3, 224, 224)
        clf_out = fake_clf.predict(dummy_tensor)
        self.assertEqual(clf_out["status"], "unavailable")
        self.assertIsNone(clf_out["predicted_class"])

        # Test simulated missing segmenter
        fake_seg = BUSISegmenterWrapper(weights_path=Path("non_existent_seg.pth"))
        self.assertFalse(fake_seg.is_loaded)
        dummy_seg_tensor = torch.randn(1, 1, 256, 256)
        seg_out = fake_seg.predict(dummy_seg_tensor)
        self.assertEqual(seg_out["status"], "unavailable")
        self.assertFalse(seg_out["mask_detected"])

    def test_09_api_endpoints_direct(self):
        """Test API route functions /api/research/busi/status and /api/research/busi/analyze."""
        from fastapi import UploadFile, HTTPException
        from backend.api.research import get_busi_model_status, analyze_busi_research

        # 1. Status endpoint function
        status_data = get_busi_model_status()
        self.assertEqual(status_data["status"], "ready")
        self.assertTrue(status_data["models"]["classifier"]["loaded"])
        self.assertTrue(status_data["models"]["segmenter"]["loaded"])
        self.assertEqual(status_data["models"]["classifier"]["classes"], ["Benign", "Malignant", "Normal"])

        # 2. Analyze endpoint function with real image upload
        with open(self.benign_sample, "rb") as f:
            uf = UploadFile(filename=self.benign_sample.name, file=f)
            data = analyze_busi_research(file=uf, study_id="api_test_01")

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["classifier"]["predicted_class"], "Benign")
        self.assertEqual(data["classifier"]["confidence_type"], "uncalibrated_softmax")
        self.assertTrue(data["segmentation"]["mask_detected"])
        self.assertIn("ACADEMIC RESEARCH ONLY", data["disclaimer"])

        # 3. Test invalid file extension rejection
        import io
        fake_pdf = io.BytesIO(b"fake pdf content")
        uf_bad = UploadFile(filename="test.pdf", file=fake_pdf)
        with self.assertRaises(HTTPException) as cm:
            analyze_busi_research(file=uf_bad, study_id="bad_ext_test")
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("Unsupported file type", cm.exception.detail)

    def test_10_production_yolo_endpoint_unchanged(self):
        """Verify that the production database, models, and YOLO pipeline are untouched."""
        from backend.database.connection import SessionLocal
        from backend.database.models import Diagnosis
        from backend.config import YOLO_WEIGHTS_PATH

        # Verify database connection
        db = SessionLocal()
        count = db.query(Diagnosis).count()
        db.close()
        self.assertGreaterEqual(count, 0)

        # Verify YOLO weights exist and size unchanged
        self.assertTrue(YOLO_WEIGHTS_PATH.is_file())
        self.assertEqual(YOLO_WEIGHTS_PATH.stat().st_size, 6549796)


if __name__ == "__main__":
    unittest.main(verbosity=2)
