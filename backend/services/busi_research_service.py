"""Research-only service for BUSI 3-class classification and U-Net segmentation.
Maintains total isolation from production YOLO and database workflows.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import re
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

from backend.config import OUTPUTS_DIR
from backend.ai_models.busi_models import (
    get_busi_classifier,
    get_busi_segmenter,
    preprocess_for_busi_classifier,
    preprocess_for_busi_segmenter,
)

logger = logging.getLogger("breast_care_ma.busi_research")

RESEARCH_DISCLAIMER = (
    "ACADEMIC RESEARCH ONLY: Experimental research models (EfficientNet-B0 and compact U-Net trained on the BUSI dataset). "
    "Outputs are uncalibrated and NOT validated for diagnostic decisions, patient triage, or malignancy exclusion. "
    "Clinical diagnosis must be made by a qualified radiologist."
)


def generate_research_overlay(
    image_path: Path,
    binary_mask_256: Optional[np.ndarray],
    pred_class: Optional[str],
    confidence: Optional[float],
    area_pct: Optional[float],
    study_id: str,
) -> Optional[str]:
    """Generates an annotated 2-panel overlay image for visual inspection.
    Panel 1: Original ultrasound
    Panel 2: Segmentation overlay with red lesion highlight and contour
    Saves to OUTPUTS_DIR and returns the relative URL.
    """
    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^a-zA-Z0-9_\-]", "", Path(study_id).name) or f"research_{uuid.uuid4().hex[:6]}"
        filename = f"{safe_id[:64]}_busi_research_overlay.jpg"
        save_path = (OUTPUTS_DIR / filename).resolve()
        if not str(save_path).startswith(str(OUTPUTS_DIR.resolve())):
            save_path = OUTPUTS_DIR / f"research_{uuid.uuid4().hex[:8]}_busi_research_overlay.jpg"
            filename = save_path.name

        with Image.open(image_path) as orig_pil:
            rgb_orig = orig_pil.convert("RGB")

        # Standardize display size to 384x384 for clear visualization
        display_size = (384, 384)
        p1 = rgb_orig.resize(display_size, Image.Resampling.BILINEAR)
        p1_np = np.array(p1)

        # Panel 2: Overlay
        p2_np = p1_np.copy()
        if binary_mask_256 is not None and np.sum(binary_mask_256) > 0:
            # Resize binary mask to display_size
            mask_disp = cv2.resize(
                binary_mask_256.astype(np.uint8),
                display_size,
                interpolation=cv2.INTER_NEAREST,
            )
            # Tint lesion red
            red_tint = np.zeros_like(p2_np)
            red_tint[:, :] = [255, 60, 60]
            mask_bool = mask_disp == 1
            p2_np[mask_bool] = (p2_np[mask_bool] * 0.55 + red_tint[mask_bool] * 0.45).astype(np.uint8)

            # Draw contour boundary in yellow
            contours, _ = cv2.findContours(mask_disp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(p2_np, contours, -1, (255, 230, 0), 2)

        # Compose side-by-side canvas with top header
        canvas_w = display_size[0] * 2 + 10
        canvas_h = display_size[1] + 60
        canvas = Image.new("RGB", (canvas_w, canvas_h), color=(18, 18, 22))
        draw = ImageDraw.Draw(canvas)

        # Draw header text
        class_str = f"Classifier: {pred_class} ({confidence*100:.1f}%)" if pred_class and confidence else "Classifier: Unavailable"
        area_str = f"U-Net Lesion Area: {area_pct:.2f}%" if area_pct is not None else "U-Net: No Mask"
        header_text = f"[RESEARCH] {class_str} | {area_str}"
        draw.text((12, 10), header_text, fill=(240, 240, 240))
        draw.text((12, 32), "FOR ACADEMIC INVESTIGATION ONLY - NOT FOR CLINICAL USE", fill=(255, 120, 120))

        # Paste panels
        canvas.paste(Image.fromarray(p1_np), (0, 60))
        canvas.paste(Image.fromarray(p2_np), (display_size[0] + 10, 60))

        # Labels on panels
        draw.text((10, 65), "Original Ultrasound", fill=(255, 255, 255))
        draw.text((display_size[0] + 20, 65), "U-Net Segmentation Overlay", fill=(255, 230, 0))

        canvas.save(save_path, quality=90)
        return f"/outputs/{filename}"
    except Exception as exc:
        logger.error("[BUSI Research Overlay Error] %s", exc)
        return None


def run_busi_research_inference(
    image_path: Union[str, Path],
    study_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Executes isolated BUSI classifier and U-Net segmenter on the given image.
    Enforces strict safety rules:
    - Independent execution: classifier runs even if U-Net fails and vice versa.
    - Zero override: segmentation cannot override classifier.
    - Empty mask does NOT imply normal.
    - Outputs are explicitly tagged as uncalibrated model scores.
    """
    img_path = Path(image_path)
    if not img_path.is_file():
        raise FileNotFoundError(f"Input image not found: {img_path.name}")

    if not study_id:
        study_id = f"research_{uuid.uuid4().hex[:8]}"

    # Validate image readability and obtain dimensions
    try:
        with Image.open(img_path) as im:
            orig_w, orig_h = im.size
            channels = len(im.getbands())
    except Exception as exc:
        raise ValueError(f"Invalid or corrupted image format: {str(exc)}")

    # 1. Independent Classifier Execution
    classifier = get_busi_classifier()
    try:
        clf_tensor = preprocess_for_busi_classifier(img_path)
        clf_result = classifier.predict(clf_tensor)
    except Exception as exc:
        logger.error("[BUSI Classifier Step Failure] %s", exc)
        clf_result = {
            "status": "error",
            "error": f"Preprocessing or inference error: {str(exc)}",
            "predicted_class": None,
            "confidence": None,
            "class_probabilities": None,
            "confidence_type": "uncalibrated_softmax",
        }

    # 2. Independent Segmenter Execution
    segmenter = get_busi_segmenter()
    try:
        seg_tensor = preprocess_for_busi_segmenter(img_path)
        seg_result = segmenter.predict(seg_tensor)
    except Exception as exc:
        logger.error("[BUSI Segmenter Step Failure] %s", exc)
        seg_result = {
            "status": "error",
            "error": f"Preprocessing or inference error: {str(exc)}",
            "mask_detected": False,
            "lesion_area_percentage": None,
            "binary_mask": None,
            "probability_map": None,
        }

    # 3. Interpret Segmentation & Build Safety Guidance
    mask_detected = seg_result.get("mask_detected", False)
    area_pct = seg_result.get("lesion_area_percentage")
    bin_mask = seg_result.get("binary_mask")

    if seg_result.get("status") == "success":
        if mask_detected:
            seg_interpretation = (
                f"Lesion contour delineated by U-Net covering {area_pct:.2f}% of image area. "
                f"Represents anatomical boundary localization only; does not provide a histological diagnosis."
            )
        else:
            seg_interpretation = (
                "No focal lesion contour delineated at the 0.50 probability threshold. "
                "IMPORTANT SAFETY NOTICE: An empty segmentation mask does NOT imply a normal scan or absence of pathology."
            )
    else:
        seg_interpretation = f"Segmentation unavailable: {seg_result.get('error')}"

    # 4. Generate Visualization Overlay
    overlay_url = generate_research_overlay(
        image_path=img_path,
        binary_mask_256=bin_mask,
        pred_class=clf_result.get("predicted_class"),
        confidence=clf_result.get("confidence"),
        area_pct=area_pct,
        study_id=study_id,
    )

    # 5. Determine Overall Research Status
    clf_ok = (clf_result.get("status") == "success")
    seg_ok = (seg_result.get("status") == "success")
    if clf_ok and seg_ok:
        overall_status = "success"
    elif clf_ok or seg_ok:
        overall_status = "partial_success"
    else:
        overall_status = "error"

    return {
        "status": overall_status,
        "study_id": study_id,
        "filename": img_path.name,
        "image_dimensions": {"width": orig_w, "height": orig_h, "channels": channels},
        "classifier": {
            "status": clf_result.get("status"),
            "predicted_class": clf_result.get("predicted_class"),
            "confidence": round(clf_result["confidence"], 4) if clf_result.get("confidence") is not None else None,
            "class_probabilities": clf_result.get("class_probabilities"),
            "confidence_type": "uncalibrated_softmax",
            "error": clf_result.get("error"),
        },
        "segmentation": {
            "status": seg_result.get("status"),
            "mask_detected": mask_detected,
            "lesion_area_percentage": area_pct,
            "threshold": seg_result.get("threshold", 0.5),
            "mask_overlay_url": overlay_url,
            "interpretation": seg_interpretation,
            "error": seg_result.get("error"),
        },
        "safety_guardrails": {
            "segmentation_overrides_classifier": False,
            "empty_mask_implies_normal": False,
            "clinical_triage_authorized": False,
        },
        "disclaimer": RESEARCH_DISCLAIMER,
    }
