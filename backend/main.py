import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import UPLOADS_DIR, OUTPUTS_DIR, REPORTS_DIR, BASE_DIR
from backend.database.connection import engine, Base, run_migrations
from backend.api import diagnosis, dashboard, models_api, reports, patients, research

# Initialize database schema and run backward-compatible migrations
Base.metadata.create_all(bind=engine)
run_migrations()

app = FastAPI(
    title="BREAST CARE-MA API",
    description="Multimodal Breast Cancer Diagnostic System (Ultrasound + Mammography + Grad-CAM + Feature Fusion)",
    version="1.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for data assets
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# Include Routers
app.include_router(patients.router)
app.include_router(diagnosis.router)
app.include_router(dashboard.router)
app.include_router(models_api.router)
app.include_router(reports.router)
app.include_router(research.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "BREAST CARE-MA Backend",
        "version": "1.1.0",
        "models_loaded": True
    }

# Frontend SPA integration
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
