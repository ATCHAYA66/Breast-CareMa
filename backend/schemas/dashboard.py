from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_scans: int
    ultrasound_scans: int
    mammography_scans: int
    dual_scans: int
    modality_distribution: List[Dict[str, Any]]
    class_distribution: List[Dict[str, Any]]
    ai_engine_status: Dict[str, Any]

class ModelMetricResponse(BaseModel):
    model_name: str
    modality: str
    dataset_name: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    specificity: Optional[float] = None
    f1_score: Optional[float] = None
    auc: Optional[float] = None
    map50: Optional[float] = None
    map50_95: Optional[float] = None
    model_status: str
    evaluation_date: datetime

    class Config:
        from_attributes = True
