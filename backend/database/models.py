from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class PatientClinicalDetails(Base):
    __tablename__ = "patient_clinical_details"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    menopause_status = Column(String(50), nullable=True)  # Premenopausal, Perimenopausal, Postmenopausal, etc.
    breast_density = Column(String(100), nullable=True)  # Category A, B, C, D, Unknown
    family_history = Column(String(20), nullable=True)   # Yes, No, Unknown
    breast_side = Column(String(30), nullable=True)      # Left, Right, Both, Not Specified
    symptoms = Column(Text, nullable=True)               # JSON string or comma-separated list
    other_symptoms = Column(String(255), nullable=True)  # If Other selected
    previous_biopsy = Column(String(20), nullable=True)  # Yes, No, Unknown
    clinical_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    diagnoses = relationship("Diagnosis", back_populates="patient")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), ForeignKey("patient_clinical_details.patient_id"), index=True, nullable=True)
    modality = Column(String(20), nullable=False)  # 'ultrasound', 'mammography', 'dual'
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    prediction = Column(String(50), nullable=True)  # 'Benign', 'Malignant', etc.
    confidence = Column(Float, nullable=True)
    report_path = Column(String(255), nullable=True)
    
    # Clinical and Explainability findings
    birads_category = Column(String(50), nullable=True)
    recommended_action = Column(Text, nullable=True)
    lesion_area = Column(Float, nullable=True)
    aspect_ratio = Column(Float, nullable=True)
    margin = Column(String(50), nullable=True)
    orientation = Column(String(50), nullable=True)
    findings_summary = Column(Text, nullable=True)

    patient = relationship("PatientClinicalDetails", back_populates="diagnoses")
    images = relationship("UploadedImages", back_populates="diagnosis", cascade="all, delete-orphan")
    model_results = relationship("ModelResults", back_populates="diagnosis", cascade="all, delete-orphan")
    reports = relationship("Reports", back_populates="diagnosis", cascade="all, delete-orphan")


class UploadedImages(Base):
    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String(50), ForeignKey("diagnoses.study_id"), index=True, nullable=False)
    image_type = Column(String(20), nullable=False)  # 'ultrasound', 'mammography'
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    diagnosis = relationship("Diagnosis", back_populates="images")


class ModelResults(Base):
    __tablename__ = "model_results"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String(50), ForeignKey("diagnoses.study_id"), index=True, nullable=False)
    model_name = Column(String(50), nullable=False)  # 'YOLOv8', 'EfficientNetB0', 'MultimodalFusion'
    predicted_class = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    output_path = Column(String(500), nullable=True)  # Detection image or heatmap path
    raw_data = Column(Text, nullable=True)  # JSON formatted details (boxes, scores, coordinates)
    created_at = Column(DateTime, default=datetime.utcnow)

    diagnosis = relationship("Diagnosis", back_populates="model_results")


class Reports(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String(50), ForeignKey("diagnoses.study_id"), index=True, nullable=False)
    report_path = Column(String(500), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    diagnosis = relationship("Diagnosis", back_populates="reports")


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), unique=True, index=True, nullable=False)
    modality = Column(String(50), nullable=False)
    dataset_name = Column(String(100), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    specificity = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc = Column(Float, nullable=True)
    map50 = Column(Float, nullable=True)
    map50_95 = Column(Float, nullable=True)
    model_status = Column(String(50), default="Available")  # 'Trained & Active', 'Untrained / Pending Paired Data'
    evaluation_date = Column(DateTime, default=datetime.utcnow)
