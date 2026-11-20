"""Deep visual and numerical inspection of all test set segmentation overlays, especially malignant cases."""
import csv
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from train_segmenter import UNet

def inspect_malignant_cases():
    manifest_p = Path("training/manifests/busi_manifest.csv")
    with open(manifest_p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    test_rows = [r for r in rows if r["split"] == "test"]
    
    ckpt_p = Path("backend/weights/research_busi_unet_best.pth")
    ck = torch.load(ckpt_p, map_location="cpu")
    model = UNet()
    model.load_state_dict(ck["state_dict"])
    model.eval()
    
    mal_rows = [r for r in test_rows if r["class_name"] == "malignant"]
    print(f"Total Malignant Test Cases: {len(mal_rows)}")
    
    results = []
    for r in mal_rows:
        img_p = Path(r["image"])
        im = Image.open(img_p).convert("L").resize((256, 256), Image.Resampling.BILINEAR)
        x = np.asarray(im, dtype=np.float32) / 255.0
        x_t = torch.from_numpy(x[None, None]).float()
        
        gt = np.zeros((256, 256), dtype=np.uint8)
        if r.get("masks"):
            for mp in r["masks"].split(";"):
                if mp and Path(mp).exists():
                    m = np.asarray(Image.open(mp).convert("L").resize((256, 256), Image.Resampling.NEAREST))
                    gt = np.maximum(gt, (m > 0).astype(np.uint8))
                    
        with torch.no_grad():
            logits = model(x_t)
            probs = torch.sigmoid(logits).numpy()[0, 0]
            pred = (probs > 0.5).astype(np.uint8)
            
        inter = np.sum(pred & gt)
        union = np.sum(pred | gt)
        dice = (2.0 * inter + 1.0) / (np.sum(pred) + np.sum(gt) + 1.0)
        iou = (inter + 1.0) / (union + 1.0)
        
        results.append({
            "name": img_p.name,
            "gt_pct": float(np.mean(gt) * 100),
            "pred_pct": float(np.mean(pred) * 100),
            "max_prob": float(np.max(probs)),
            "dice": float(dice),
            "iou": float(iou)
        })
        
    print("\nMalignant Cases Summary:")
    print(f"{'Image':<22} | {'GT Area %':>10} | {'Pred Area %':>12} | {'Max Prob':>10} | {'Dice':>8}")
    print("-" * 70)
    empty_preds = []
    under_segmented = []
    for res in sorted(results, key=lambda x: x["dice"]):
        print(f"{res['name']:<22} | {res['gt_pct']:>9.2f}% | {res['pred_pct']:>11.2f}% | {res['max_prob']:>9.4f} | {res['dice']:>8.4f}")
        if res["pred_pct"] == 0:
            empty_preds.append(res)
        elif res["pred_pct"] < res["gt_pct"] * 0.4:
            under_segmented.append(res)
            
    print(f"\nZero-mask predictions among Malignant cases: {len(empty_preds)} / {len(mal_rows)} ({len(empty_preds)/len(mal_rows)*100:.1f}%)")
    print(f"Under-segmented cases (<40% of GT): {len(under_segmented)} / {len(mal_rows)}")
    
if __name__ == "__main__":
    inspect_malignant_cases()
