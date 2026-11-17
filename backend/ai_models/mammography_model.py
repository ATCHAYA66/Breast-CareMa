import os
from pathlib import Path
from typing import Dict, Any, Tuple
import torch
import torch.nn as nn
from torchvision import models

from backend.config import EFFICIENTNET_WEIGHTS_PATH
from backend.ai_models.preprocessing import load_and_validate_image, preprocess_mammography

CLASSES = ["Benign", "Malignant"]

class MammographyClassifier(nn.Module):
    def __init__(self, num_classes=2, pretrained_weights_path: Path = EFFICIENTNET_WEIGHTS_PATH):
        super(MammographyClassifier, self).__init__()
        self.weights_path = Path(pretrained_weights_path)
        self.num_classes = num_classes
        self.is_custom_trained = False
        
        # Load torchvision EfficientNetB0 backbone
        try:
            weights = models.EfficientNet_B0_Weights.DEFAULT
            self.backbone = models.efficientnet_b0(weights=weights)
        except Exception:
            self.backbone = models.efficientnet_b0(weights=None)
            
        in_features = self.backbone.classifier[1].in_features
        # Replace classifier head for 2-class diagnostic output
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features=in_features, out_features=num_classes)
        )
        
        self.load_custom_weights()
        self.eval()

    def load_custom_weights(self):
        if self.weights_path.exists():
            try:
                state_dict = torch.load(self.weights_path, map_location="cpu")
                self.load_state_dict(state_dict)
                self.is_custom_trained = True
                print(f"[EfficientNetB0] Successfully loaded custom weights from {self.weights_path}")
            except Exception as e:
                print(f"[EfficientNetB0] Failed to load custom weights: {e}")
                self.is_custom_trained = False
        else:
            print(f"[EfficientNetB0] Custom weights not found at {self.weights_path}. Operating with initialized transfer-learning backbone.")
            self.is_custom_trained = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extracts 1280-dimensional feature embedding before classification head
        for multimodal feature fusion.
        """
        features = self.backbone.features(x)
        pooled = self.backbone.avgpool(features)
        flattened = torch.flatten(pooled, 1)
        return flattened

    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Inference on single mammography scan.
        """
        img_rgb = load_and_validate_image(image_path)
        tensor = preprocess_mammography(img_rgb)
        
        with torch.no_grad():
            logits = self.forward(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().tolist()
            
            # If scalar or 2 classes
            if isinstance(probs, float):
                probs = [1.0 - probs, probs]
            
            pred_idx = int(torch.argmax(logits, dim=1).item())
            confidence = float(probs[pred_idx])
            pred_class = CLASSES[pred_idx]

        return {
            "model_name": "EfficientNetB0",
            "is_custom_trained": self.is_custom_trained,
            "predicted_class": pred_class,
            "confidence": round(confidence, 4),
            "probabilities": {
                "Benign": round(probs[0], 4),
                "Malignant": round(probs[1], 4)
            }
        }
