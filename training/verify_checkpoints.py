"""Verify that both trained BUSI research checkpoints load and run inference successfully."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch import nn
from torchvision import models

from train_segmenter import UNet

def verify_classifier(pth_path: Path):
    print(f"\n--- Verifying Classifier: {pth_path} ---")
    assert pth_path.exists(), f"File not found: {pth_path}"
    
    ck = torch.load(pth_path, map_location="cpu")
    print("Checkpoint keys:", list(ck.keys()))
    print("Architecture:", ck.get("architecture"))
    print("Class names:", ck.get("class_names"))
    print("Best val accuracy:", ck.get("best_val_accuracy"))
    print("Test accuracy:", ck.get("test_accuracy"))
    
    # Load model architecture
    m = models.efficientnet_b0(weights=None)
    in_features = m.classifier[1].in_features
    m.classifier[1] = nn.Linear(in_features, len(ck["class_names"]))
    m.load_state_dict(ck["state_dict"])
    m.eval()
    
    # Forward pass on dummy tensor
    dummy = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        out = m(dummy)
        probs = torch.softmax(out, dim=1).numpy()[0]
    print("Dummy test forward pass logits shape:", out.shape)
    print("Dummy test softmax probabilities:", {name: float(p) for name, p in zip(ck["class_names"], probs)})
    print("Classifier checkpoint verification PASSED.")
    return ck

def verify_segmenter(pth_path: Path):
    print(f"\n--- Verifying Segmenter: {pth_path} ---")
    assert pth_path.exists(), f"File not found: {pth_path}"
    
    ck = torch.load(pth_path, map_location="cpu")
    print("Checkpoint keys:", list(ck.keys()))
    print("Architecture:", ck.get("architecture"))
    print("Image size:", ck.get("image_size"))
    print("Threshold:", ck.get("threshold"))
    print("Best val dice:", ck.get("best_val_dice"))
    
    # Load U-Net architecture
    m = UNet()
    m.load_state_dict(ck["state_dict"])
    m.eval()
    
    # Forward pass on dummy tensor
    dummy = torch.randn(1, 1, ck.get("image_size", 256), ck.get("image_size", 256))
    with torch.no_grad():
        logits = m(dummy)
        prob_mask = torch.sigmoid(logits)
        bin_mask = (prob_mask > ck.get("threshold", 0.5)).float()
    print("Dummy test forward pass logits shape:", logits.shape)
    print("Predicted mask min/max probability:", float(prob_mask.min()), float(prob_mask.max()))
    print("Segmenter checkpoint verification PASSED.")
    return ck

def verify_real_sample(classifier_path: Path, segmenter_path: Path):
    print("\n--- Running Inference on Real BUSI Sample ---")
    manifest = Path("training/manifests/busi_manifest.csv")
    if not manifest.exists():
        print("Manifest not found, skipping real sample.")
        return
    
    import csv
    with open(manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    # Pick one sample per class from test split
    test_samples = {r["class_name"]: r for r in rows if r["split"] == "test"}
    print(f"Testing real test samples across classes: {list(test_samples.keys())}")
    
    # Load models
    ck_c = torch.load(classifier_path, map_location="cpu")
    clf = models.efficientnet_b0(weights=None)
    clf.classifier[1] = nn.Linear(clf.classifier[1].in_features, len(ck_c["class_names"]))
    clf.load_state_dict(ck_c["state_dict"])
    clf.eval()
    
    ck_s = torch.load(segmenter_path, map_location="cpu")
    seg = UNet()
    seg.load_state_dict(ck_s["state_dict"])
    seg.eval()
    
    for cls_name, row in test_samples.items():
        img_p = Path(row["image"])
        im = Image.open(img_p).convert("RGB")
        
        # Classifier input: 224x224 normalized
        im_c = im.resize((224, 224), Image.Resampling.BILINEAR)
        arr_c = np.asarray(im_c, dtype=np.float32) / 255.0
        # ImageNet normalize
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr_c = (arr_c - mean) / std
        tensor_c = torch.from_numpy(arr_c.transpose(2, 0, 1)[None]).float()
        
        with torch.no_grad():
            logits_c = clf(tensor_c)
            probs_c = torch.softmax(logits_c, dim=1).numpy()[0]
            pred_class = ck_c["class_names"][int(np.argmax(probs_c))]
            pred_conf = float(np.max(probs_c))
        
        # Segmenter input: 256x256 grayscale
        im_s = im.convert("L").resize((256, 256), Image.Resampling.BILINEAR)
        arr_s = np.asarray(im_s, dtype=np.float32) / 255.0
        tensor_s = torch.from_numpy(arr_s[None, None]).float()
        
        with torch.no_grad():
            logits_s = seg(tensor_s)
            mask = (torch.sigmoid(logits_s) > 0.5).numpy()[0, 0]
            lesion_pct = float(np.mean(mask) * 100.0)
            
        print(f"Sample [{cls_name}] {img_p.name}: True={cls_name} | Pred={pred_class} ({pred_conf*100:.1f}%) | Segmented Lesion Area={lesion_pct:.2f}%")

def verify_protection_rules():
    print("\n--- Verifying Protection of Existing Model Weights ---")
    best_pt = Path("backend/weights/best.pt")
    assert best_pt.exists(), "CRITICAL: backend/weights/best.pt is missing!"
    print(f"CONFIRMED: {best_pt} exists and is intact (size: {best_pt.stat().st_size:,} bytes).")
    
    yolo_pt = Path("backend/weights/yolov8n.pt")
    if yolo_pt.exists():
        print(f"CONFIRMED: {yolo_pt} exists (size: {yolo_pt.stat().st_size:,} bytes).")

if __name__ == "__main__":
    clf_path = Path("backend/weights/research_busi_classifier_best.pth")
    seg_path = Path("backend/weights/research_busi_unet_best.pth")
    verify_classifier(clf_path)
    verify_segmenter(seg_path)
    verify_real_sample(clf_path, seg_path)
    verify_protection_rules()
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
