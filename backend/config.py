import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'database' / 'breast_care_ma.db'}"

UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"
WEIGHTS_DIR = BASE_DIR / "weights"

# Ensure directories exist
for directory in [UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, WEIGHTS_DIR, BASE_DIR / "database"]:
    directory.mkdir(parents=True, exist_ok=True)

# Set Ultralytics config directory locally inside backend to prevent AppData Permission/Access Denied errors
ULTRALYTICS_DIR = BASE_DIR / ".ultralytics"
ULTRALYTICS_DIR.mkdir(parents=True, exist_ok=True)
os.environ["YOLO_CONFIG_DIR"] = str(ULTRALYTICS_DIR)

# Allowed file types and max upload size (30MB)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
MAX_FILE_SIZE_BYTES = 30 * 1024 * 1024

# Model weights filenames
YOLO_WEIGHTS_PATH = WEIGHTS_DIR / "best.pt"
EFFICIENTNET_WEIGHTS_PATH = WEIGHTS_DIR / "efficientnet_b0_mammography.pth"
FUSION_WEIGHTS_PATH = WEIGHTS_DIR / "multimodal_fusion.pth"
