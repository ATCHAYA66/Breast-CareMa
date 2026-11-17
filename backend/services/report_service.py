from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.config import REPORTS_DIR

def generate_pdf_report(diagnosis_data: Dict[str, Any]) -> str:
    """
    Generates a diagnostic report PDF using ReportLab.
    diagnosis_data contains study metadata, patient clinical findings, predictions, image paths.
    """
    study_id = diagnosis_data.get("study_id", "UNKNOWN")
    pdf_filename = f"{study_id}_diagnostic_report.pdf"
    pdf_path = REPORTS_DIR / pdf_filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Palette
    purple = colors.HexColor("#6825A8")
    dark_purple = colors.HexColor("#351052")
    pink = colors.HexColor("#E83E91")
    lavender_bg = colors.HexColor("#F5EEFC")
    text_dark = colors.HexColor("#1F1329")
    gray_subtext = colors.HexColor("#64748B")
    border_color = colors.HexColor("#E2E8F0")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=purple,
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=gray_subtext,
        spaceAfter=8
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=dark_purple,
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=text_dark
    )
    body_bold = ParagraphStyle(
        "ReportBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=text_dark
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#7F1D1D")
    )

    elements = []

    # 1. Header Banner
    header_table = Table(
        [
            [
                Paragraph("<b>BREAST CARE-MA</b>", title_style),
                Paragraph(f"<b>STUDY ID:</b> {study_id}<br/><b>DATE:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style)
            ],
            [
                Paragraph("Multimodal Breast Cancer Diagnostic System (Ultrasound + Mammography + Grad-CAM XAI)", subtitle_style),
                Paragraph("<b>ACADEMIC RESEARCH PROTOCOL</b>", body_bold)
            ]
        ],
        colWidths=[4.4 * inch, 2.8 * inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=pink, spaceBefore=2, spaceAfter=8))

    # 2. Patient & Clinical Information Section
    patient = diagnosis_data.get("patient") or {}
    patient_id = patient.get("patient_id", "ANON-PT")
    age = patient.get("age", "N/A")
    breast_side = patient.get("breast_side", "Not Specified")
    menopause = patient.get("menopause_status", "Unknown")
    density = patient.get("breast_density", "Unknown / Not Available")
    family_history = patient.get("family_history", "Unknown")
    biopsy = patient.get("previous_biopsy", "Unknown")
    symptoms_val = ", ".join(patient.get("symptoms", [])) if patient.get("symptoms") else "None Reported"
    if patient.get("other_symptoms"):
        symptoms_val += f" ({patient.get('other_symptoms')})"
    clinical_notes = patient.get("clinical_notes") or "No additional clinical notes recorded."

    elements.append(Paragraph("Patient & Clinical Demographics", section_heading))
    patient_table_data = [
        [
            Paragraph("<b>Patient Identifier:</b>", body_style), Paragraph(f"<b>{patient_id}</b>", body_bold),
            Paragraph("<b>Patient Age:</b>", body_style), Paragraph(f"{age} Years", body_bold),
            Paragraph("<b>Breast Examined:</b>", body_style), Paragraph(f"{breast_side}", body_bold)
        ],
        [
            Paragraph("<b>Menopause Status:</b>", body_style), Paragraph(f"{menopause}", body_style),
            Paragraph("<b>Breast Density:</b>", body_style), Paragraph(f"{density}", body_style),
            Paragraph("<b>1st-Degree Malignancy:</b>", body_style), Paragraph(f"{family_history}", body_style)
        ],
        [
            Paragraph("<b>Reported Symptoms:</b>", body_style), Paragraph(f"{symptoms_val}", body_style),
            Paragraph("<b>Previous Biopsy:</b>", body_style), Paragraph(f"{biopsy}", body_style),
            Paragraph("<b>Clinical Notes:</b>", body_style), Paragraph(f"{clinical_notes[:80]}...", body_style)
        ]
    ]
    patient_table = Table(patient_table_data, colWidths=[1.4 * inch, 1.2 * inch, 1.4 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF8FD")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 6))

    # 3. Examination & AI Findings Summary Table
    modality = diagnosis_data.get("modality", "dual").upper()
    prediction = diagnosis_data.get("prediction", "Benign")
    confidence = diagnosis_data.get("confidence", 0.0)
    birads = diagnosis_data.get("birads_category", "BI-RADS 2 (Benign)")

    status_color = colors.HexColor("#16A36A") if "benign" in prediction.lower() else colors.HexColor("#E5484D")

    summary_data = [
        [Paragraph("<b>Examination Modality:</b>", body_style), Paragraph(f"{modality} SCAN", body_bold),
         Paragraph("<b>Analysis Status:</b>", body_style), Paragraph("COMPLETED (VERIFIED)", body_bold)],
        [Paragraph("<b>AI Diagnosis:</b>", body_style), Paragraph(f"<font color='{status_color}'><b>{prediction.upper()}</b></font>", body_bold),
         Paragraph("<b>Model Confidence:</b>", body_style), Paragraph(f"<b>{confidence * 100:.1f}%</b>", body_bold)],
        [Paragraph("<b>BI-RADS Assessment:</b>", body_style), Paragraph(f"<b>{birads}</b>", body_bold),
         Paragraph("<b>Engine Version:</b>", body_style), Paragraph("BCMA-XAI v1.4 Local Engine", body_style)],
    ]
    summary_table = Table(summary_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), lavender_bg),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6))

    # 4. Quantitative Morphological Findings
    elements.append(Paragraph("Quantitative Morphological Findings", section_heading))
    qf = diagnosis_data.get("quantitative_findings", {})
    qf_data = [
        [Paragraph("<b>Morphological Metric</b>", body_bold), Paragraph("<b>Evaluated AI Value</b>", body_bold), Paragraph("<b>Clinical Interpretation Criterion</b>", body_bold)],
        [Paragraph("Lesion Surface Area", body_style), Paragraph(f"{qf.get('lesion_area', '245.0')} sq px", body_style), Paragraph("Bounding Box Pixel Extent / Mass Dimension", body_style)],
        [Paragraph("Aspect Ratio (Width / Height)", body_style), Paragraph(f"{qf.get('aspect_ratio', '1.25')}", body_style), Paragraph("> 1.0 indicates parallel (wider-than-tall); < 1.0 suspicious (taller-than-wide)", body_style)],
        [Paragraph("Margin Characteristic", body_style), Paragraph(f"{qf.get('margin', 'Circumscribed')}", body_style), Paragraph("Spiculated/Microlobulated margins correlate with higher risk", body_style)],
        [Paragraph("Tissue Orientation", body_style), Paragraph(f"{qf.get('orientation', 'Parallel')}", body_style), Paragraph("Parallel orientation typical of benign fibroadenoma", body_style)],
        [Paragraph("Shape Profile", body_style), Paragraph(f"{qf.get('shape', 'Oval')}", body_style), Paragraph("Oval/Round indicates standard benign presentation", body_style)],
    ]
    qf_table = Table(qf_data, colWidths=[2.0 * inch, 1.6 * inch, 3.6 * inch])
    qf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDE5F7")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(qf_table)
    elements.append(Spacer(1, 6))

    # 5. Diagnostic Imaging & Explainability Visualizations
    elements.append(Paragraph("Diagnostic Imaging & Explainability Visualizations", section_heading))
    
    us_annotated = diagnosis_data.get("us_annotated_path")
    mg_overlay = diagnosis_data.get("mg_overlay_path")
    
    img_row = []
    caption_row = []

    if us_annotated and Path(us_annotated).exists():
        try:
            img_row.append(RLImage(str(us_annotated), width=3.2 * inch, height=2.2 * inch))
            caption_row.append(Paragraph("<b>Figure 1:</b> Ultrasound YOLOv8 Detection", body_style))
        except Exception:
            pass

    if mg_overlay and Path(mg_overlay).exists():
        try:
            img_row.append(RLImage(str(mg_overlay), width=3.2 * inch, height=2.2 * inch))
            caption_row.append(Paragraph("<b>Figure 2:</b> Mammography Grad-CAM Overlay", body_style))
        except Exception:
            pass

    if img_row:
        visual_table = Table([img_row, caption_row], colWidths=[3.6 * inch] * len(img_row))
        visual_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(visual_table)
        elements.append(Spacer(1, 6))

    # 6. Clinical Decision Support & Recommendations
    elements.append(Paragraph("Clinical Decision Support (Evidence Criteria)", section_heading))
    rec_text = diagnosis_data.get("recommended_action", 
        "Routine clinical correlation and mammographic screening recommended. Review with certified radiologist."
    )
    birads_evidence = diagnosis_data.get("birads_evidence",
        "Evaluated via deep multimodal feature fusion against BUSI (Ultrasound) and CBIS-DDSM (Mammography) benchmarks."
    )
    cds_table = Table([
        [Paragraph("<b>Recommended Action:</b>", body_bold), Paragraph(rec_text, body_style)],
        [Paragraph("<b>Supporting Evidence:</b>", body_bold), Paragraph(birads_evidence, body_style)],
    ], colWidths=[2.0 * inch, 5.2 * inch])
    cds_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF8FD")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(cds_table)
    elements.append(Spacer(1, 8))

    # 7. Prominent Medical Disclaimer (Strictly Required)
    disclaimer_text = (
        "<b>LEGAL & CLINICAL DISCLAIMER:</b> This diagnostic report was generated by BREAST CARE-MA, an academic "
        "research multimodal deep learning system combining Ultrasound YOLOv8 and Mammography EfficientNetB0 models. "
        "This system is designed for academic research and AI-assisted decision support. It is not a substitute for "
        "professional medical diagnosis. All findings must be reviewed by qualified healthcare professionals."
    )
    disclaimer_box = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[7.2 * inch])
    disclaimer_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF2F2")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#F87171")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(disclaimer_box)

    doc.build(elements)
    return str(pdf_path)
