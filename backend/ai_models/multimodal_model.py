from pathlib import Path
from typing import Dict, Any, Tuple
import torch
import torch.nn as nn
from torchvision import models

from backend.config import FUSION_WEIGHTS_PATH
from backend.ai_models.preprocessing import load_and_validate_image, preprocess_mammography, preprocess_ultrasound

CLASSES = ["Benign", "Malignant"]

class MultimodalFusionNet(nn.Module):
    """
    Multimodal Feature Fusion Architecture:
    F_US = Ultrasound_Encoder(I_US) [512-dim / 1280-dim]
    F_MG = Mammography_Encoder(I_MG) [1280-dim]
    F_Fused = Concatenate(F_US, F_MG)
    Y = MLP(F_Fused)
    """
    def __init__(self, us_dim=512, mg_dim=1280, hidden_dim=256, num_classes=2, weights_path: Path = FUSION_WEIGHTS_PATH):
        super(MultimodalFusionNet, self).__init__()
        self.weights_path = Path(weights_path)
        self.is_trained = False
        
        # Ultrasound Encoder backbone (ResNet18 / EfficientNet based feature extractor)
        try:
            us_backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        except Exception:
            us_backbone = models.resnet18(weights=None)
        # Remove final FC to output 512-dim embedding
        self.us_encoder = nn.Sequential(*list(us_backbone.children())[:-1])
        
        # Multimodal MLP Fusion Head
        fused_dim = us_dim + mg_dim
        self.fusion_mlp = nn.Sequential(
            nn.Linear(fused_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(p=0.4),
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(64, num_classes)
        )
        
        self.load_fusion_weights()

    def load_fusion_weights(self):
        if self.weights_path.exists():
            try:
                state_dict = torch.load(self.weights_path, map_location="cpu")
                self.load_state_dict(state_dict)
                self.is_trained = True
                print(f"[Multimodal] Loaded trained fusion weights from {self.weights_path}")
            except Exception as e:
                print(f"[Multimodal] Error loading fusion weights: {e}")
                self.is_trained = False
        else:
            # Paired multimodal datasets (paired BUSI + CBIS-DDSM) are not provided in workspace
            self.is_trained = False
            print(f"[Multimodal] Notice: Multimodal fusion weights not found at {self.weights_path}.")

    def forward(self, us_tensor: torch.Tensor, mg_feature_tensor: torch.Tensor) -> torch.Tensor:
        # Extract Ultrasound features
        us_feats = self.us_encoder(us_tensor)  # (B, 512, 1, 1)
        us_feats = torch.flatten(us_feats, 1)  # (B, 512)
        
        # Normalize embeddings
        us_norm = nn.functional.normalize(us_feats, p=2, dim=1)
        mg_norm = nn.functional.normalize(mg_feature_tensor, p=2, dim=1)
        
        # Feature concatenation: F_Fused = Concatenate(F_US, F_MG)
        fused = torch.cat((us_norm, mg_norm), dim=1)
        
        # MLP classification
        logits = self.fusion_mlp(fused)
        return logits

    def fuse(self, us_image_path: str, mg_image_path: str, mg_classifier) -> Dict[str, Any]:
        """
        Executes feature extraction for both modalities and evaluates the fusion head.
        If trained fusion weights are absent, explicitly reports 'Untrained / Pending Paired Data'
        as mandated by project instructions (never substitutes simple averaging).
        """
        # Preprocess both images
        us_rgb = load_and_validate_image(us_image_path)
        mg_rgb = load_and_validate_image(mg_image_path)
        
        us_tensor = preprocess_mammography(us_rgb)  # (1, 3, 224, 224)
        mg_tensor = preprocess_mammography(mg_rgb)  # (1, 3, 224, 224)

        with torch.no_grad():
            mg_features = mg_classifier.extract_features(mg_tensor)
            
            if self.is_trained:
                logits = self.forward(us_tensor, mg_features)
                probs = torch.softmax(logits, dim=1).squeeze().tolist()
                pred_idx = int(torch.argmax(logits, dim=1).item())
                confidence = float(probs[pred_idx])
                predicted_class = CLASSES[pred_idx]
                status_note = "Calibrated Multimodal Feature Fusion Active"
            else:
                # Prompt rule:
                # "If paired training data is unavailable, clearly mark the multimodal fusion model as not trained.
                # Never substitute simple averaging of two independent predictions for a trained feature-fusion model."
                pred_idx = 0
                confidence = 0.0
                predicted_class = "Pending Paired Dataset Training"
                status_note = "Model architecture implemented (MLP Concatenation: 512-dim US + 1280-dim MG). Paired clinical dataset required for fine-tuning."

        return {
            "model_name": "Multimodal Feature Fusion (MLP)",
            "is_trained": self.is_trained,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "feature_dimensions": {
                "ultrasound_feature_dim": 512,
                "mammography_feature_dim": 1280,
                "fused_feature_dim": 1792
            },
            "status_note": status_note
        }
