from pathlib import Path
from typing import Dict, Any, Tuple
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from backend.config import OUTPUTS_DIR
from backend.ai_models.preprocessing import load_and_validate_image, preprocess_mammography

class GradCAM:
    def __init__(self, model: torch.nn.Module, target_layer=None):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # If target layer not specified, pick the final feature layer
        if self.target_layer is None:
            if hasattr(model, "backbone") and hasattr(model.backbone, "features"):
                self.target_layer = model.backbone.features[-1]
            elif hasattr(model, "features"):
                self.target_layer = model.features[-1]

        self.hook_layers()

    def hook_layers(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]

        if self.target_layer is not None:
            self.target_layer.register_forward_hook(forward_hook)
            self.target_layer.register_full_backward_hook(backward_hook)

    def generate(self, image_path: str, study_id: str, target_class: int = None) -> Dict[str, Any]:
        """
        Generates Grad-CAM activation heatmap and blended overlay.
        """
        img_rgb = load_and_validate_image(image_path)
        orig_h, orig_w, _ = img_rgb.shape
        tensor = preprocess_mammography(img_rgb)
        tensor.requires_grad_(True)

        # Forward pass
        self.model.zero_grad()
        logits = self.model(tensor)
        
        if target_class is None:
            target_class = torch.argmax(logits, dim=1).item()

        # Backward pass on target class score
        score = logits[0, target_class]
        score.backward()

        if self.gradients is None or self.activations is None:
            # Fallback activation if hooks didn't capture
            heatmap = np.ones((orig_h, orig_w), dtype=np.float32) * 0.5
        else:
            gradients = self.gradients.detach().cpu().numpy()[0]  # Shape: (C, H, W)
            activations = self.activations.detach().cpu().numpy()[0]  # Shape: (C, H, W)

            # Global average pooling of gradients: weights
            weights = np.mean(gradients, axis=(1, 2))  # Shape: (C,)
            
            # Weighted combination of forward activation maps
            cam = np.zeros(activations.shape[1:], dtype=np.float32)
            for i, w in enumerate(weights):
                cam += w * activations[i]

            # Apply ReLU (only features that positively correlate with the class)
            cam = np.maximum(cam, 0)
            
            # Normalize CAM
            cam_max = np.max(cam)
            if cam_max > 0:
                cam = cam / cam_max
            
            # Resize heatmap to match original image dimensions
            heatmap = cv2.resize(cam, (orig_w, orig_h))

        # Colorize heatmap with JET colormap
        heatmap_uint8 = np.uint8(255 * heatmap)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        heatmap_colored_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

        # Blend original scan with heatmap overlay
        alpha = 0.55
        overlay = cv2.addWeighted(img_rgb, 1 - alpha, heatmap_colored_rgb, alpha, 0)

        # Save files
        heatmap_filename = f"{study_id}_gradcam_heatmap.jpg"
        overlay_filename = f"{study_id}_gradcam_overlay.jpg"
        
        heatmap_save_path = OUTPUTS_DIR / heatmap_filename
        overlay_save_path = OUTPUTS_DIR / overlay_filename

        cv2.imwrite(str(heatmap_save_path), heatmap_colored)
        cv2.imwrite(str(overlay_save_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

        # Peak activation region coordinates (hotspot)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(heatmap)
        hotspot = {
            "peak_x": max_loc[0],
            "peak_y": max_loc[1],
            "max_intensity": round(float(max_val), 4)
        }

        return {
            "heatmap_path": str(heatmap_save_path),
            "heatmap_filename": heatmap_filename,
            "overlay_path": str(overlay_save_path),
            "overlay_filename": overlay_filename,
            "hotspot": hotspot,
            "target_class": target_class
        }
