from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class PatientBase(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=50, description="Unique anonymized patient identifier")
    age: int = Field(..., ge=18, le=100, description="Patient age between 18 and 100")
    menopause_status: Optional[str] = "Unknown"
    breast_density: Optional[str] = "Unknown / Not Available"
    family_history: Optional[str] = "Unknown"
    breast_side: Optional[str] = "Not Specified"
    symptoms: Optional[List[str]] = []
    other_symptoms: Optional[str] = None
    previous_biopsy: Optional[str] = "Unknown"
    clinical_notes: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=18, le=100)
    menopause_status: Optional[str] = None
    breast_density: Optional[str] = None
    family_history: Optional[str] = None
    breast_side: Optional[str] = None
    symptoms: Optional[List[str]] = None
    other_symptoms: Optional[str] = None
    previous_biopsy: Optional[str] = None
    clinical_notes: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
