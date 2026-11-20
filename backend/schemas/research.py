"""Pydantic schemas for the isolated BUSI research API."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class BUSIClassifierOutput(BaseModel):
    status: str = Field(..., description="'success', 'error', or 'unavailable'")
    predicted_class: Optional[str] = Field(None, description="'Benign', 'Malignant', or 'Normal'")
    confidence: Optional[float] = Field(None, description="Maximum softmax score (0.0 to 1.0)")
    class_probabilities: Optional[Dict[str, float]] = Field(None, description="Softmax probabilities for each class")
    confidence_type: str = Field("uncalibrated_softmax", description="Clarifies that score is uncalibrated model output, not cancer probability")
    error: Optional[str] = Field(None, description="Error detail if classification failed")


class BUSISegmentationOutput(BaseModel):
    status: str = Field(..., description="'success', 'error', or 'unavailable'")
    mask_detected: bool = Field(False, description="True if any lesion pixels exceed the probability threshold")
    lesion_area_percentage: Optional[float] = Field(None, description="Percentage of total image area covered by lesion mask")
    threshold: float = Field(0.5, description="Sigmoid cutoff threshold used for binarization")
    mask_overlay_url: Optional[str] = Field(None, description="URL path to the generated overlay visualization")
    interpretation: str = Field(..., description="Guidance regarding mask detection status and safety rules")
    error: Optional[str] = Field(None, description="Error detail if segmentation failed")


class BUSISafetyGuardrails(BaseModel):
    segmentation_overrides_classifier: bool = Field(False, description="Strict rule: segmentation can never override classifier")
    empty_mask_implies_normal: bool = Field(False, description="Strict rule: missing mask does not mean scan is normal")
    clinical_triage_authorized: bool = Field(False, description="Model output is not approved for patient triage")


class BUSIResearchResponse(BaseModel):
    status: str = Field("success", description="'success' or 'partial_success' or 'error'")
    study_id: Optional[str] = Field(None, description="Study ID if associated with an existing study")
    filename: str = Field(..., description="Name of the analyzed image file")
    image_dimensions: Dict[str, int] = Field(..., description="Original image width, height, and channels")
    classifier: BUSIClassifierOutput
    segmentation: BUSISegmentationOutput
    safety_guardrails: BUSISafetyGuardrails
    disclaimer: str = Field(
        "ACADEMIC RESEARCH ONLY: Experimental research models (EfficientNet-B0 and compact U-Net trained on the BUSI dataset). "
        "Outputs are uncalibrated and NOT validated for diagnostic decisions, patient triage, or malignancy exclusion. "
        "Clinical diagnosis must be made by a qualified radiologist."
    )
