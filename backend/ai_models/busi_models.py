"""Isolated PyTorch inference models for academic BUSI research.
Contains:
1. EfficientNet-B0 3-class classifier (Benign, Malignant, Normal)
2. Compact U-Net binary lesion segmenter
Both models are strictly segregated from the production YOLOv8 pipeline.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch
from torch import nn
from torchvision import models, transforms

from backend.config import (
    BUSI_CLASSIFIER_WEIGHTS_PATH,
    BUSI_UNET_WEIGHTS_PATH,
)

logger = logging.getLogger("breast_care_ma.busi_research")

# Standard ImageNet statistics (used strictly during classifier training)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


# =====================================================================
# Dedicated BUSI Preprocessing Functions
# (Completely independent of existing YOLO preprocess_ultrasound)
# =====================================================================

def preprocess_for_busi_classifier(image_input: Union[str, Path, np.ndarray, Image.Image]) -> torch.Tensor:
    """Preprocess image for BUSI 3-class EfficientNet-B0.
    Exact match with training:
    - RGB conversion
    - Resize to 224x224 (Bilinear)
    - ImageNet normalization: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    Returns shape: (1, 3, 224, 224) float32 tensor
    """
    if isinstance(image_input, (str, Path)):
        pil_img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            pil_img = Image.fromarray(image_input).convert("RGB")
        elif image_input.shape[2] == 3:
            pil_img = Image.fromarray(image_input).convert("RGB")
        else:
            raise ValueError(f"Unsupported image array shape: {image_input.shape}")
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("RGB")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    transform = transforms.Compose([
        transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    return transform(pil_img).unsqueeze(0)


def preprocess_for_busi_segmenter(image_input: Union[str, Path, np.ndarray, Image.Image]) -> torch.Tensor:
    """Preprocess image for BUSI compact U-Net binary segmenter.
    Exact match with training:
    - Grayscale conversion ('L')
    - Resize to 256x256 (Bilinear)
    - Min-max scaling [0.0, 1.0] float32
    Returns shape: (1, 1, 256, 256) float32 tensor
    """
    if isinstance(image_input, (str, Path)):
        pil_img = Image.open(image_input).convert("L")
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 3:
            pil_img = Image.fromarray(image_input).convert("L")
        else:
            pil_img = Image.fromarray(image_input)
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("L")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    resized = pil_img.resize((256, 256), resample=Image.Resampling.BILINEAR)
    arr = np.asarray(resized, dtype=np.float32) / 255.0
    return torch.from_numpy(arr[None, None]).float()


# =====================================================================
# Model Architecture Definitions
# =====================================================================

class Block(nn.Module):
    """Double conv block matching train_segmenter.py"""
    def __init__(self, ci: int, co: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(ci, co, 3, padding=1),
            nn.BatchNorm2d(co),
            nn.ReLU(inplace=True),
            nn.Conv2d(co, co, 3, padding=1),
            nn.BatchNorm2d(co),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class CompactUNet(nn.Module):
    """Compact binary U-Net matching train_segmenter.py"""
    def __init__(self):
        super().__init__()
        self.e1 = Block(1, 32)
        self.e2 = Block(32, 64)
        self.e3 = Block(64, 128)
        self.pool = nn.MaxPool2d(2)
        self.mid = Block(128, 256)
        self.u3 = nn.ConvTranspose2d(256, 128, 2, 2)
        self.d3 = Block(256, 128)
        self.u2 = nn.ConvTranspose2d(128, 64, 2, 2)
        self.d2 = Block(128, 64)
        self.u1 = nn.ConvTranspose2d(64, 32, 2, 2)
        self.d1 = Block(64, 32)
        self.out = nn.Conv2d(32, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        a = self.e1(x)
        b = self.e2(self.pool(a))
        c = self.e3(self.pool(b))
        z = self.mid(self.pool(c))
        z = self.d3(torch.cat([self.u3(z), c], 1))
        z = self.d2(torch.cat([self.u2(z), b], 1))
        z = self.d1(torch.cat([self.u1(z), a], 1))
        return self.out(z)


# =====================================================================
# Model Wrapper Classes
# =====================================================================

class BUSIClassifierWrapper:
    """Loads and wraps the research BUSI 3-class classifier checkpoint."""

    def __init__(self, weights_path: Path = BUSI_CLASSIFIER_WEIGHTS_PATH):
        self.weights_path = Path(weights_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.class_names = ["Benign", "Malignant", "Normal"]
        self.is_loaded = False
        self.error_message: Optional[str] = None
        self.load()

    def load(self) -> None:
        if not self.weights_path.is_file():
            self.error_message = f"Classifier weights not found at: {self.weights_path}"
            logger.warning("[BUSI Classifier] %s", self.error_message)
            self.is_loaded = False
            return

        try:
            ckpt = torch.load(self.weights_path, map_location=self.device)
            self.class_names = ckpt.get("class_names", ["Benign", "Malignant", "Normal"])
            num_classes = len(self.class_names)

            net = models.efficientnet_b0(weights=None)
            in_features = net.classifier[1].in_features
            net.classifier[1] = nn.Linear(in_features, num_classes)
            net.load_state_dict(ckpt["state_dict"])
            net.to(self.device)
            net.eval()

            self.model = net
            self.is_loaded = True
            self.error_message = None
            logger.info(
                "[BUSI Classifier] Successfully loaded %s on %s with classes: %s",
                self.weights_path.name, self.device, self.class_names
            )
        except Exception as exc:
            self.error_message = f"Failed to load classifier checkpoint: {str(exc)}"
            logger.error("[BUSI Classifier] %s", self.error_message)
            self.model = None
            self.is_loaded = False

    def predict(self, tensor: torch.Tensor) -> Dict[str, Any]:
        """Runs inference on a preprocessed (1, 3, 224, 224) tensor."""
        if not self.is_loaded or self.model is None:
            return {
                "status": "unavailable",
                "error": self.error_message or "Model not loaded",
                "predicted_class": None,
                "confidence": None,
                "class_probabilities": None,
            }

        try:
            with torch.no_grad():
                logits = self.model(tensor.to(self.device))
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
                pred_idx = int(np.argmax(probs))
                pred_class = self.class_names[pred_idx]
                confidence = float(probs[pred_idx])
                prob_dict = {
                    name: round(float(p), 4) for name, p in zip(self.class_names, probs)
                }

            return {
                "status": "success",
                "error": None,
                "predicted_class": pred_class,
                "confidence": confidence,
                "class_probabilities": prob_dict,
                "confidence_type": "uncalibrated_softmax",
            }
        except Exception as exc:
            logger.error("[BUSI Classifier Inference Error] %s", exc)
            return {
                "status": "error",
                "error": f"Inference failure: {str(exc)}",
                "predicted_class": None,
                "confidence": None,
                "class_probabilities": None,
            }


class BUSISegmenterWrapper:
    """Loads and wraps the research BUSI compact U-Net segmentation checkpoint."""

    def __init__(self, weights_path: Path = BUSI_UNET_WEIGHTS_PATH):
        self.weights_path = Path(weights_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.threshold: float = 0.5
        self.image_size: int = 256
        self.is_loaded = False
        self.error_message: Optional[str] = None
        self.load()

    def load(self) -> None:
        if not self.weights_path.is_file():
            self.error_message = f"Segmenter weights not found at: {self.weights_path}"
            logger.warning("[BUSI Segmenter] %s", self.error_message)
            self.is_loaded = False
            return

        try:
            ckpt = torch.load(self.weights_path, map_location=self.device)
            self.threshold = float(ckpt.get("threshold", 0.5))
            self.image_size = int(ckpt.get("image_size", 256))

            net = CompactUNet()
            net.load_state_dict(ckpt["state_dict"])
            net.to(self.device)
            net.eval()

            self.model = net
            self.is_loaded = True
            self.error_message = None
            logger.info(
                "[BUSI Segmenter] Successfully loaded %s on %s (size=%dx%d, threshold=%.2f)",
                self.weights_path.name, self.device, self.image_size, self.image_size, self.threshold
            )
        except Exception as exc:
            self.error_message = f"Failed to load segmenter checkpoint: {str(exc)}"
            logger.error("[BUSI Segmenter] %s", self.error_message)
            self.model = None
            self.is_loaded = False

    def predict(self, tensor: torch.Tensor) -> Dict[str, Any]:
        """Runs inference on a preprocessed (1, 1, 256, 256) tensor.
        Returns probability map and binary mask.
        """
        if not self.is_loaded or self.model is None:
            return {
                "status": "unavailable",
                "error": self.error_message or "Model not loaded",
                "mask_detected": False,
                "lesion_area_percentage": None,
                "binary_mask": None,
                "probability_map": None,
            }

        try:
            with torch.no_grad():
                logits = self.model(tensor.to(self.device))
                probs = torch.sigmoid(logits).cpu().numpy()[0, 0]
                bin_mask = (probs > self.threshold).astype(np.uint8)

            lesion_pixels = int(np.sum(bin_mask))
            total_pixels = int(bin_mask.size)
            area_pct = round(float((lesion_pixels / total_pixels) * 100.0), 2)
            mask_detected = bool(lesion_pixels > 0)

            return {
                "status": "success",
                "error": None,
                "mask_detected": mask_detected,
                "lesion_area_percentage": area_pct if mask_detected else 0.0,
                "binary_mask": bin_mask,
                "probability_map": probs,
                "threshold": self.threshold,
            }
        except Exception as exc:
            logger.error("[BUSI Segmenter Inference Error] %s", exc)
            return {
                "status": "error",
                "error": f"Inference failure: {str(exc)}",
                "mask_detected": False,
                "lesion_area_percentage": None,
                "binary_mask": None,
                "probability_map": None,
            }


# =====================================================================
# Singleton Accessors (Loaded Once In Memory)
# =====================================================================

_classifier_instance: Optional[BUSIClassifierWrapper] = None
_segmenter_instance: Optional[BUSISegmenterWrapper] = None

def get_busi_classifier() -> BUSIClassifierWrapper:
    """Returns singleton instance of BUSI classifier wrapper."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = BUSIClassifierWrapper()
    return _classifier_instance

def get_busi_segmenter() -> BUSISegmenterWrapper:
    """Returns singleton instance of BUSI segmenter wrapper."""
    global _segmenter_instance
    if _segmenter_instance is None:
        _segmenter_instance = BUSISegmenterWrapper()
    return _segmenter_instance
