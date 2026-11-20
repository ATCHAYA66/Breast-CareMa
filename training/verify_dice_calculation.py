"""Examine the exact per-sample segmentation results for all 118 test cases."""
import csv
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from train_segmenter import UNet

def analyze_all_test_cases():
    manifest_p = Path("training/manifests/busi_manifest.csv")
    with open(manifest_p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    test_rows = [r for r in rows if r["split"] == "test"]
    
    ckpt_p = Path("backend/weights/research_busi_unet_best.pth")
    ck = torch.load(ckpt_p, map_location="cpu")
    model = UNet()
    model.load_state_dict(ck["state_dict"])
    model.eval()
    
    size = 256
    results = []
    
    for i, r in enumerate(test_rows):
        img_p = Path(r["image"])
        im = Image.open(img_p).convert("L").resize((size, size), Image.Resampling.BILINEAR)
        x = np.asarray(im, dtype=np.float32) / 255.0
        x_t = torch.from_numpy(x[None, None]).float()
        
        gt = np.zeros((size, size), dtype=np.uint8)
        if r.get("masks"):
            for mp in r["masks"].split(";"):
                if mp and Path(mp).exists():
                    m = np.asarray(Image.open(mp).convert("L").resize((size, size), Image.Resampling.NEAREST))
                    gt = np.maximum(gt, (m > 0).astype(np.uint8))
                    
        with torch.no_grad():
            logits = model(x_t)
            probs = torch.sigmoid(logits).numpy()[0, 0]
            pred = (probs > 0.5).astype(np.uint8)
            
        gt_sum = int(np.sum(gt))
        pred_sum = int(np.sum(pred))
        inter = int(np.sum(pred & gt))
        union = int(np.sum(pred | gt))
        
        # 1. Training/testing code formula (Laplace +1 smoothed)
        dice_smoothed = (2.0 * inter + 1.0) / (pred_sum + gt_sum + 1.0)
        iou_smoothed = (inter + 1.0) / (union + 1.0)
        
        # 2. Standard clinical / statistical formula:
        # If both are empty: dice = 1.0 (perfect negative) or undefined
        # If one is empty and other non-empty: dice = 0.0
        # If both non-empty: 2*inter / (pred + gt)
        if gt_sum == 0 and pred_sum == 0:
            dice_standard_empty1 = 1.0
            iou_standard_empty1 = 1.0
            dice_standard_empty_nan = np.nan
        elif gt_sum == 0 or pred_sum == 0:
            dice_standard_empty1 = 0.0
            iou_standard_empty1 = 0.0
            dice_standard_empty_nan = 0.0
        else:
            dice_standard_empty1 = (2.0 * inter) / (pred_sum + gt_sum)
            iou_standard_empty1 = inter / union
            dice_standard_empty_nan = dice_standard_empty1
            
        results.append({
            "idx": i,
            "image": img_p.name,
            "class": r["class_name"],
            "gt_sum": gt_sum,
            "pred_sum": pred_sum,
            "inter": inter,
            "union": union,
            "max_prob": float(np.max(probs)),
            "dice_smoothed": float(dice_smoothed),
            "iou_smoothed": float(iou_smoothed),
            "dice_standard_empty1": float(dice_standard_empty1),
            "iou_standard_empty1": float(iou_standard_empty1),
            "dice_standard_empty_nan": dice_standard_empty_nan
        })
        
    print(f"Total Test Cases Analyzed: {len(results)}")
    
    # Analyze NORMAL subgroup specifically
    normal_res = [res for res in results if res["class"] == "normal"]
    print(f"\n--- NORMAL SUBGROUP ({len(normal_res)} cases) ---")
    fp_normal = [res for res in normal_res if res["pred_sum"] > 0]
    tn_normal = [res for res in normal_res if res["pred_sum"] == 0]
    print(f"True Negatives (GT=0, Pred=0): {len(tn_normal)} / {len(normal_res)}")
    print(f"False Positives (GT=0, Pred>0): {len(fp_normal)} / {len(normal_res)}")
    
    for res in fp_normal:
        print(f"  FP Normal Case: {res['image']} | GT pixels: {res['gt_sum']} | Pred pixels: {res['pred_sum']} ({res['pred_sum']/(256*256)*100:.2f}%) | Max Prob: {res['max_prob']:.4f} | Smoothed Dice: {res['dice_smoothed']:.6f} | Standard Dice: {res['dice_standard_empty1']:.4f}")
        
    for res in tn_normal[:3]:
        print(f"  TN Normal Case (sample): {res['image']} | GT pixels: {res['gt_sum']} | Pred pixels: {res['pred_sum']} | Smoothed Dice: {res['dice_smoothed']:.4f} | Standard Dice: {res['dice_standard_empty1']:.4f}")
        
    # Check Normal Mean Dice under smoothed formula
    normal_smoothed_dices = [res["dice_smoothed"] for res in normal_res]
    print(f"\nNormal Mean Smoothed Dice: {np.mean(normal_smoothed_dices):.4f}")
    
    # Subgroup breakdowns
    benign_res = [res for res in results if res["class"] == "benign"]
    malignant_res = [res for res in results if res["class"] == "malignant"]
    
    print("\n" + "="*95)
    print("SUBGROUP COMPARISON ACROSS FORMULAS (DICE & IoU)")
    print("="*95)
    print(f"{'Subgroup':<18} | {'N':>4} | {'Smoothed Dice':>14} | {'Std Dice':>10} | {'Smoothed IoU':>14} | {'Std IoU':>10} | {'Std Lesion Dice':>16}")
    print("-" * 95)
    
    for name, grp in [("Benign", benign_res), ("Malignant", malignant_res), ("Normal", normal_res)]:
        sm_d = np.mean([r["dice_smoothed"] for r in grp])
        st_d1 = np.mean([r["dice_standard_empty1"] for r in grp])
        sm_iou = np.mean([r["iou_smoothed"] for r in grp])
        st_iou1 = np.mean([r["iou_standard_empty1"] for r in grp])
        print(f"{name:<18} | {len(grp):>4} | {sm_d:>14.4f} | {st_d1:>10.4f} | {sm_iou:>14.4f} | {st_iou1:>10.4f} | {'N/A' if name=='Normal' else f'{st_d1:>16.4f}'}")
        
    # Overall Macro Average (all 118 cases)
    overall_sm_d = np.mean([r["dice_smoothed"] for r in results])
    overall_st_d1 = np.mean([r["dice_standard_empty1"] for r in results])
    overall_sm_iou = np.mean([r["iou_smoothed"] for r in results])
    overall_st_iou1 = np.mean([r["iou_standard_empty1"] for r in results])
    print("-" * 95)
    print(f"{'Overall (118 cases)':<18} | {len(results):>4} | {overall_sm_d:>14.4f} | {overall_st_d1:>10.4f} | {overall_sm_iou:>14.4f} | {overall_st_iou1:>10.4f} | {'N/A':>16}")
    
    # Lesion-Only Macro Average (excluding 20 Normal cases -> 98 cases: 66 Benign + 32 Malignant)
    lesion_res = [res for res in results if res["class"] in ("benign", "malignant")]
    lesion_sm_d = np.mean([r["dice_smoothed"] for r in lesion_res])
    lesion_st_d1 = np.mean([r["dice_standard_empty1"] for r in lesion_res])
    lesion_sm_iou = np.mean([r["iou_smoothed"] for r in lesion_res])
    lesion_st_iou1 = np.mean([r["iou_standard_empty1"] for r in lesion_res])
    print(f"{'Lesion-Only (98)':<18} | {len(lesion_res):>4} | {lesion_sm_d:>14.4f} | {lesion_st_d1:>10.4f} | {lesion_sm_iou:>14.4f} | {lesion_st_iou1:>10.4f} | {lesion_st_d1:>16.4f}")
    
if __name__ == "__main__":
    analyze_all_test_cases()
