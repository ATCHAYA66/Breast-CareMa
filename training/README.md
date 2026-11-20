# Breast CARE-MA BUSI research training (Windows / Antigravity)

This adds two independent training tracks while preserving the existing application and production weights:

1. EfficientNet-B0, 3-class image classification: Benign / Malignant / Normal.
2. A compact binary U-Net, lesion-mask segmentation.

**Nothing in this folder overwrites `backend/weights/best.pt`, `yolov8n.pt`, the database, uploads, reports, frontend, or existing model files.** New checkpoints are written as `research_busi_classifier_best.pth` and `research_busi_unet_best.pth`.

## 1. Extract the dataset

From the project root, create `datasets/BUSI/` and extract the supplied BUSI archive so that this exists:

```
datasets/BUSI/Dataset_BUSI_with_GT/benign/
datasets/BUSI/Dataset_BUSI_with_GT/malignant/
datasets/BUSI/Dataset_BUSI_with_GT/normal/
```

Keep original images and every `_mask*.png` file. Do not rename or delete masks. The preparation script accepts `datasets/BUSI` or the nested dataset folder.

## 2. Environment

Use Python 3.10 or 3.11 on Windows. In Antigravity, open the project root `cancer/` and run commands in its integrated terminal. For NVIDIA GPU, first install the CUDA-compatible PyTorch build selected by the official PyTorch install selector; otherwise the CPU build works but training will be slower. Then install:

```
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r training\requirements-training.txt
```

## 3. Prepare and inspect split

```
python training\prepare_busi.py --data datasets\BUSI
```

This writes `training/manifests/busi_manifest.csv`. Splitting occurs by original image ID, so an image and all its masks remain in one split. The split is stratified within each class (approximately 70/15/15). Review the printed counts before training.

## 4. Train classification

```
python training\train_classifier.py --pretrained --epochs 25 --batch-size 8
```

`--pretrained` downloads ImageNet EfficientNet-B0 initialization. Omit it to train from random initialization without a model download. Lower batch size to 4 or 2 if GPU memory is limited. Outputs:

- `backend/weights/research_busi_classifier_best.pth`
- `backend/weights/research_busi_classifier_best.metrics.json`

The checkpoint stores class order `[Benign, Malignant, Normal]` and preprocessing image size.

## 5. Train segmentation

```
python training\train_segmenter.py --epochs 30 --batch-size 4
```

All masks associated with an image are merged by pixel-wise union. Images without a mask (including normal cases) get an all-zero mask. Outputs `backend/weights/research_busi_unet_best.pth`. Validation and held-out test Dice are printed. Segmentation outputs represent dataset-mask overlap, not a clinical measurement.

## Important research safeguards

- Do not point the current YOLO detector at the classifier or U-Net checkpoint; they are different architectures and tasks.
- Do not replace `backend/weights/best.pt` yet. The existing FastAPI inference code expects YOLO weights.
- Do not display classification softmax as a calibrated cancer probability. It is a model score from a small, imbalanced dataset.
- BUSI image-level splits are used here. If patient identifiers are available, replace this with patient-level grouping before claiming independent generalization. Dataset-level metrics are not clinical validation.
- No frontend or database changes are made by these scripts.

## Antigravity instruction

Open the project root in Antigravity and ask it to: "Review training/README.md, verify the BUSI folder structure, run prepare_busi.py, inspect the split counts and mask overlays, then train classification and segmentation in separate commands. Do not edit frontend, database, existing weights, uploads, reports, or production inference. Stop and report any error rather than fabricating metrics."
