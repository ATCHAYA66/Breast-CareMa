import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import cv2

from backend.config import YOLO_WEIGHTS_PATH, OUTPUTS_DIR
from backend.ai_models.preprocessing import load_and_validate_image

logger = logging.getLogger("breast_care_ma.ultrasound")


class UltrasoundTumorDetector:
    """YOLOv8 ultrasound detector. No-detection is never treated as benign."""

    def __init__(self, weights_path: Path = YOLO_WEIGHTS_PATH, conf_threshold: float = 0.25):
        self.weights_path = Path(weights_path)
        self.conf_threshold = float(conf_threshold)
        self.model = None
        self.is_custom_trained = False
        self.class_names = {}
        self.load_model()

    def load_model(self) -> None:
        if not self.weights_path.is_file():
            print(f"[YOLOv8] Medical weights not found at path: {self.weights_path}")
            self.model = None
            self.is_custom_trained = False
            return

        try:
            from ultralytics import YOLO
            self.model = YOLO(str(self.weights_path))
            names = self.model.names
            if isinstance(names, list):
                names = {i: name for i, name in enumerate(names)}
            self.class_names = names

            # Distinguish custom fine-tuned weights from default COCO weights
            is_coco = (len(names) == 80 and names.get(0) == "person")
            self.is_custom_trained = not is_coco

            if is_coco:
                print(
                    f"[YOLOv8 WARNING] Weights file '{self.weights_path.name}' contains standard 80 COCO classes. "
                    f"Model is NOT fine-tuned on breast ultrasound lesions (e.g., Benign / Malignant)."
                )
            else:
                print(f"[YOLOv8] Loaded custom trained weights ({self.weights_path.name}) with classes: {self.class_names}")

        except Exception as exc:
            print(f"[YOLOv8 ERROR] Failed to load model weights: {exc}")
            self.model = None
            self.is_custom_trained = False
            self.class_names = {}

    def analyze(self, image_path: str, study_id: str) -> Dict[str, Any]:
        img_rgb = load_and_validate_image(image_path)
        img_h, img_w, img_c = img_rgb.shape
        annotated_filename = f"{study_id}_us_annotated.jpg"
        annotated_path = OUTPUTS_DIR / annotated_filename

        print(f"[YOLOv8 Inference] Study: {study_id} | File: {Path(image_path).name} | Dims: {img_w}x{img_h}x{img_c} | Conf Threshold: {self.conf_threshold}")

        base = {
            "model_name": "YOLOv8",
            "weights_path": str(self.weights_path),
            "is_custom_trained": self.is_custom_trained,
            "predicted_class": "Inconclusive",
            "confidence": None,
            "detection_status": "model_unavailable",
            "boxes": [],
            "image_dimensions": {"width": img_w, "height": img_h, "channels": img_c},
            "output_image_path": str(annotated_path),
            "output_image_filename": annotated_filename,
            "quantitative_findings": {
                "lesion_area_px": None,
                "lesion_area": None,
                "aspect_ratio": None,
                "shape": "Not assessed",
                "margin": "Not assessed",
                "orientation": "Not assessed",
            },
        }

        # Save original image for traceability if model is unavailable
        original_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        if self.model is None:
            cv2.imwrite(str(annotated_path), original_bgr)
            print(f"[YOLOv8 Inference] Aborted: YOLO model instance is None.")
            return base

        try:
            results = self.model.predict(
                source=img_rgb,
                conf=self.conf_threshold,
                verbose=False,
            )
            if not results:
                raise RuntimeError("YOLO returned an empty results list")
            result = results[0]
            names = self.model.names
            if isinstance(names, list):
                names = {i: name for i, name in enumerate(names)}

            boxes_list = []
            for box in result.boxes if result.boxes is not None else []:
                coords = box.xyxy[0].detach().cpu().tolist()
                confidence = float(box.conf[0].detach().cpu().item())
                class_id = int(box.cls[0].detach().cpu().item())
                raw_class_name = str(names.get(class_id, f"class_{class_id}"))
                
                # Format medical class names cleanly
                if raw_class_name.lower() == "benign":
                    class_name = "Benign"
                elif raw_class_name.lower() == "malignant":
                    class_name = "Malignant"
                elif raw_class_name.lower() == "normal":
                    class_name = "Normal"
                else:
                    class_name = raw_class_name

                x1, y1, x2, y2 = [float(v) for v in coords]
                width = max(0.0, x2 - x1)
                height = max(0.0, y2 - y1)
                box_info = {
                    "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                    "class_id": class_id,
                    "class": class_name,
                    "confidence": round(confidence, 4),
                    "area_px": round(width * height, 1),
                    "aspect_ratio": round(width / height, 3) if height > 0 else None,
                }
                boxes_list.append(box_info)
                print(f"[YOLOv8 Detection] Box found: {box_info['box']}, Class='{class_name}' (ID={class_id}), Conf={confidence:.4f}, Area={box_info['area_px']} px²")

            annotated_bgr = result.plot() if boxes_list else original_bgr
            if not cv2.imwrite(str(annotated_path), annotated_bgr):
                raise RuntimeError(f"Could not write annotated image: {annotated_path}")

            if not boxes_list:
                # Probe candidates below threshold to log near-miss detections
                highest_sub_conf = None
                sub_class = None
                try:
                    probe = self.model.predict(source=img_rgb, conf=0.01, verbose=False)
                    if probe and probe[0].boxes and len(probe[0].boxes) > 0:
                        top_box = probe[0].boxes[0]
                        highest_sub_conf = float(top_box.conf[0].item())
                        sub_class = names.get(int(top_box.cls[0].item()), "unknown")
                except Exception:
                    pass

                if highest_sub_conf is not None:
                    print(f"[YOLOv8 Inference] Study {study_id}: 0 boxes met conf_threshold={self.conf_threshold}. Highest candidate below threshold: {highest_sub_conf:.4f} (class: '{sub_class}')")
                else:
                    print(f"[YOLOv8 Inference] Study {study_id}: 0 candidate boxes detected across entire image.")

                base.update({
                    "detection_status": "no_detection",
                    "predicted_class": "Inconclusive",
                    "confidence": None,
                    "boxes": [],
                    "quantitative_findings": {
                        "lesion_area_px": None,
                        "lesion_area": None,
                        "aspect_ratio": None,
                        "shape": "Not assessed",
                        "margin": "Not assessed",
                        "orientation": "Not assessed",
                    }
                })
                return base

            # Select the highest-confidence detected box for the summary
            best = max(boxes_list, key=lambda item: item["confidence"])
            print(f"[YOLOv8 Inference] Study {study_id}: {len(boxes_list)} detection(s) found. Top finding: '{best['class']}' with conf {best['confidence']:.4f}")

            base.update({
                "predicted_class": best["class"],
                "confidence": best["confidence"],
                "detection_status": "detected",
                "boxes": boxes_list,
                "quantitative_findings": {
                    "lesion_area_px": best["area_px"],
                    "lesion_area": best["area_px"],
                    "aspect_ratio": best["aspect_ratio"],
                    "shape": "Not assessed from bounding box",
                    "margin": "Not assessed from bounding box",
                    "orientation": "Not assessed from bounding box",
                },
            })
            return base

        except Exception as exc:
            cv2.imwrite(str(annotated_path), original_bgr)
            print(f"[YOLOv8 ERROR] Inference exception on study {study_id}: {exc}")
            raise RuntimeError(f"Ultrasound YOLO inference failed: {exc}") from exc
