import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

# ImageNet normalization standard
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def load_and_validate_image(image_path: str) -> np.ndarray:
    """
    Loads an image from file path and validates readability.
    Returns RGB numpy array.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image from {image_path}. Check file format or path.")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def preprocess_ultrasound(image_rgb: np.ndarray, target_size=(640, 640)) -> np.ndarray:
    """
    Ultrasound-specific preprocessing:
    - Optional CLAHE contrast enhancement for speckle noise management
    - Resizing with aspect-ratio preserving padding or standard resize for YOLO
    """
    # Convert to LAB to apply CLAHE only on lightness channel
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced_lab = cv2.merge((cl, a, b))
    enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
    
    resized = cv2.resize(enhanced_rgb, target_size, interpolation=cv2.INTER_LINEAR)
    return resized

def preprocess_mammography(image_rgb: np.ndarray, target_size=(224, 224)) -> torch.Tensor:
    """
    Mammography preprocessing:
    - Bilateral filtering or gentle contrast adjustment to highlight microcalcifications / masses
    - Normalization with ImageNet statistics
    - PyTorch tensor conversion (1, 3, H, W)
    """
    pil_img = Image.fromarray(image_rgb)
    transform = transforms.Compose([
        transforms.Resize(target_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])
    tensor = transform(pil_img).unsqueeze(0)  # Shape: (1, 3, 224, 224)
    return tensor
