from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from backend.schemas.patient import PatientResponse

class UploadedImageResponse(BaseModel):
    id: int
    study_id: str
    image_type: str
    file_name: str
    file_url: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ModelResultResponse(BaseModel):
    id: int
    model_name: str
    predicted_class: str
    confidence: Optional[float] = None
    output_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DiagnosisCreate(BaseModel):
    modality: str  # 'ultrasound', 'mammography', 'dual'
    patient_id: Optional[str] = None

class DiagnosisResponse(BaseModel):
    id: int
    study_id: str
    patient_id: Optional[str] = None
    modality: str
    created_at: datetime
    status: str
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    report_path: Optional[str] = None
    report_url: Optional[str] = None
    birads_category: Optional[str] = None
    recommended_action: Optional[str] = None
    lesion_area: Optional[float] = None
    aspect_ratio: Optional[float] = None
    margin: Optional[str] = None
    orientation: Optional[str] = None
    findings_summary: Optional[str] = None
    patient: Optional[PatientResponse] = None
    images: List[UploadedImageResponse] = []
    model_results: List[ModelResultResponse] = []

    class Config:
        from_attributes = True

class DiagnosisHistoryItem(BaseModel):
    study_id: str
    patient_id: Optional[str] = None
    date: datetime
    modality: str
    prediction: Optional[str]
    confidence: Optional[float]
    status: str
    birads_category: Optional[str]

    class Config:
        from_attributes = True
