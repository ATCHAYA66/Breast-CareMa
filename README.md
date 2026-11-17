# BREAST CARE-MA
## Multimodal Breast Cancer Diagnostic System
### Deep Learning • Multimodal Feature Fusion • Explainable AI (Grad-CAM)

**BREAST CARE-MA** is an academic research platform integrating Breast Ultrasound (BUSI) and Mammography (CBIS-DDSM) imaging using Deep Convolutional Neural Networks, Multimodal Feature Fusion, and Explainable AI.

---

## 1. Project Overview & Research Architecture

```
                       [ Patient Imaging Exam ]
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [ Ultrasound Image ]             [ Mammography Image ]
                 │                               │
                 ▼                               ▼
     [ YOLOv8 Tumor Detector ]        [ EfficientNet-B0 Classifier ]
     - Lesion Localization            - Feature Extraction (1280-dim)
     - Bounding Box Annotations       - Grad-CAM Heatmap Activation
     - Morphological Biomarkers                  │
                 │                               │
                 ▼                               ▼
      Ultrasound Features (F_US)      Mammography Features (F_MG)
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                     [ Feature Concatenation ]
                       F_Fused = [F_US || F_MG]
                                 │
                                 ▼
                    [ Multimodal Fusion MLP ]
                                 │
                                 ▼
                 [ Dual-Mode Diagnostic Consensus ]
                 - Benign vs. Malignant
                 - Quantitative Morphological Findings
                 - BI-RADS Evidence Criteria
                 - PDF Diagnostic Report Generation
```

### Mathematical Model
$$\mathbf{F}_{\text{US}} = \text{Ultrasound\_Encoder}(\mathbf{I}_{\text{US}})$$
$$\mathbf{F}_{\text{MG}} = \text{Mammography\_Encoder}(\mathbf{I}_{\text{MG}})$$
$$\mathbf{F}_{\text{Fused}} = \text{Concatenate}(\mathbf{F}_{\text{US}}, \mathbf{F}_{\text{MG}})$$
$$\mathbf{Y} = \text{MLP}(\mathbf{F}_{\text{Fused}})$$

---

## 2. Research Team & Work Allotment

Aligned directly with the project work allotment:

| Team Member | Role | Key Contributions |
| :--- | :--- | :--- |
| **Partha Sarathy C** | **Team Lead & System Architect** | System planning, FastAPI backend integration, SQLite/SQLAlchemy schema, multi-agent workflow orchestration, deployment. |
| **Atchaya M** | **AI/ML Engineer (Detection & Classification)** | Agent 1: YOLOv8 Tumor Detection, Agent 2: EfficientNetB0 Classification, BUSI & CBIS-DDSM dataset pipelines, benchmark evaluation. |
| **Kalaiarasi C** | **Frontend & Explainability Engineer** | React + Vite UI, 9-screen clinical workflow, Agent 3: Grad-CAM XAI visualization, Recharts analytics, user experience. |
| **Hariharasudhan S** | **Knowledge & Risk Analysis Engineer** | Agent 4: Clinical Evidence Retrieval (RAG), Agent 5: Risk Assessment, Agent 6: Report Generation, BI-RADS criteria logic. |

---

## 3. Technology Stack (100% Free & Open-Source)

- **Frontend:** React 19, Vite, Tailwind CSS, React Router DOM v7, Axios, Lucide React, Recharts, jsPDF
- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLAlchemy, SQLite
- **AI/ML & Vision:** PyTorch, Ultralytics YOLOv8, EfficientNetB0, Grad-CAM, OpenCV, Torchvision, Scikit-learn
- **Diagnostic Reports:** ReportLab 5.1 (Automated server-side vector PDF generation)

---

## 4. Nine Major Application Screens

1. **Landing Page (`/`):** Hero section with medical previews, features, team attribution, free-tools disclosure.
2. **Dashboard (`/dashboard`):** Statistics cards, Recharts donut modality breakdown, live AI engine telemetry, recent patient studies.
3. **New Diagnosis – Select Modality (`/diagnosis/new`):** Select between Ultrasound, Mammography, or Dual Scan.
4. **Upload Scan Images (`/diagnosis/upload`):** Drag-and-drop file uploaders with real-time validation (MIME, file size, extension).
5. **AI Analysis – Processing (`/diagnosis/processing/:study_id`):** Multi-stage progress tracking across preprocessing, feature extraction, YOLOv8 inference, EfficientNet inference, and feature fusion.
6. **Analysis Results (`/diagnosis/results/:study_id`):** Annotated YOLOv8 lesion bounding boxes, EfficientNet probabilities, Grad-CAM heatmaps, and multimodal concordance.
7. **Detailed Results & Explainability (`/diagnosis/explainability/:study_id`):** 4 interactive tabs (Side-by-Side, Heatmap, Segmentation Boundary Disclosure, Region of Interest) plus quantitative morphological metrics table.
8. **Clinical Decision Support (`/diagnosis/cds/:study_id`):** Recommended clinical next steps, BI-RADS evidence criteria, and mandatory clinical disclaimer.
9. **Report Generation & Download (`/diagnosis/report/:study_id`):** Interactive diagnostic sheet, official downloadable PDF report, and print/share tools.

---

## 5. Quick Start Instructions

### Option A: Run Full-Stack Unified Server (Recommended)
FastAPI serves both the backend API and the built production React frontend:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Open your browser to: **http://localhost:8000**

### Option B: Run with Vite Hot-Reload (Development)
Terminal 1 (Backend):
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
Open your browser to: **http://localhost:5173**

---

## 6. Verification & Automated Test Suite
To execute the automated end-to-end diagnostic pipeline test:
```bash
python -m backend.test_pipeline
```
This verifies:
- Database creation & table indexes
- YOLOv8 weights loading & lesion detection
- EfficientNet feature embedding extraction
- Grad-CAM heatmap generation and overlay
- Multimodal feature fusion concatenation
- ReportLab PDF generation and file integrity

---

## 7. Mandatory Medical Disclaimer
> **Academic Research Protocol:** This system is designed for academic research and AI-assisted decision support. It is not a substitute for professional medical diagnosis. All findings must be reviewed and correlated with standard clinical protocols by qualified healthcare professionals.
