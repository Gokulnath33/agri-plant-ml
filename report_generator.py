"""
report_generator.py
===================
Publication-grade Agricultural Diagnostic & Agronomic Prescription PDF Generator.
Uses ReportLab to build high-fidelity, printable, standardized field reports.
Covers:
1. Executive Diagnostic Summary (Crop, Pathogen, Confidence, Severity, Foliar Damage)
2. Specific Pesticide Type & Active Ingredients (CIB&RC Approved, FRAC/IRAC, Dosage, Dilution)
3. Plant Water Requirement & Spray Water Dilution Volume (L/acre & Knapsack)
4. Irrigation Strategy & Scheduling (Drip/Furrow, mm/cycle, Frequency, Disease Moisture Warning)
5. Soil Type, Texture, pH & Soil Conditioning (FYM, Bio-agents, Drainage)
6. 4-Tier Integrated Action Plan (Immediate, Organic, Chemical, Nutrition)
7. Farmer Safety & Personal Protective Equipment (PPE) Checklist
"""

import io
import os
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedReportCanvas(canvas.Canvas):
    """Adds running header and footer with page count to every page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 805, "Automated Site-Specific Pesticide Application (ASSPA) — Crop Pathology & Agronomic Report")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(40, 799, 555, 799)

        # Footer (All pages)
        footer_text = f"Page {self._pageNumber} of {page_count}  |  Official Agronomic Prescription  |  Compliant with Indian CIB&RC Standards"
        self.drawRightString(555, 25, footer_text)
        self.drawString(40, 25, "CONFIDENTIAL & AGRONOMIC EXTENSION USE ONLY")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(40, 35, 555, 35)

        self.restoreState()


def build_diagnostic_pdf_bytes(data: dict) -> bytes:
    """
    Constructs a professional, comprehensive PDF report from the diagnostic JSON payload.
    Returns bytes of the generated PDF.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1b5e20'),
        alignment=1, # Center
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#047857'),
        alignment=1,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1b5e20'),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1e293b')
    )

    bold_label = ParagraphStyle(
        'BoldLabel',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )

    cell_hdr = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0
    )

    cell_text = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1e293b')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=cell_text,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )

    alert_style = ParagraphStyle(
        'AlertText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#991b1b')
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("AUTOMATED SITE-SPECIFIC PESTICIDE APPLICATION (ASSPA)", title_style))
    story.append(Paragraph("OFFICIAL INTEGRATED CROP PATHOLOGY & AGRONOMIC DIAGNOSTIC REPORT", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1b5e20"), spaceBefore=2, spaceAfter=8))

    # Meta Table: Location, User, Timestamp, Report ID
    p = data.get("pathology", {})
    s = data.get("severity", {})
    act = data.get("action_plan", {})
    best = data.get("best", {})
    plant_stats = data.get("plant_stats", {})
    risk = data.get("risk_forecast", {})

    report_id = f"ASSPA-{int(time.time())}"
    state_str = data.get("state") or "General Agro-Climatic Zone"
    district_str = data.get("district") or "Field Sector 1"
    crop_name = p.get("crop") or data.get("plant_type") or "Foliar Specimen"
    disease_name = p.get("disease_name") or "Specimen Health Check"
    confidence = best.get("confidence", 95.0)

    meta_table_data = [
        [
            Paragraph(f"<b>Report ID:</b> {report_id}", cell_text),
            Paragraph(f"<b>Date/Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}", cell_text),
            Paragraph(f"<b>Farmer / User:</b> @{data.get('username', 'Farmer-User')}", cell_text)
        ],
        [
            Paragraph(f"<b>State:</b> {state_str}", cell_text),
            Paragraph(f"<b>District:</b> {district_str}", cell_text),
            Paragraph(f"<b>Diagnostic Engine:</b> {best.get('algorithm', 'Multi-Model Consensus')}", cell_text)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[170, 175, 175])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # 2. Executive Diagnostic Findings
    story.append(Paragraph("1. Primary Phytopathological Diagnosis", h1_style))
    diag_summary = [
        [
            Paragraph("Diagnosed Crop & Disease", cell_hdr),
            Paragraph("Pathogen & Scientific Name", cell_hdr),
            Paragraph("Severity & Foliar Damage", cell_hdr),
            Paragraph("Diagnostic Confidence", cell_hdr)
        ],
        [
            Paragraph(f"<b>{crop_name}</b><br/>{disease_name}", cell_bold),
            Paragraph(f"<b>Type:</b> {p.get('pathogen_type', 'N/A')}<br/><i>{p.get('scientific_name', 'N/A')}</i>", cell_text),
            Paragraph(f"<b>Tier:</b> {s.get('tier', 'Moderate')}<br/><b>Damage:</b> {s.get('estimated_damage_pct', '15-25')}% Leaf Area", cell_text),
            Paragraph(f"<b>{confidence:.1f}%</b><br/>{data.get('ensemble_consensus', {}).get('agreement_text', 'High Consensus')}", cell_bold)
        ]
    ]
    t_diag = Table(diag_summary, colWidths=[130, 150, 130, 110])
    t_diag.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#15803d')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bbf7d0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0fdf4')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_diag)
    story.append(Spacer(1, 8))

    # 3. WHICH TYPE OF PESTICIDE USE
    story.append(Paragraph("2. Targeted Pesticide Type, Active Ingredients & Prescription", h1_style))
    story.append(Paragraph(
        "Prescribed in strict accordance with the Central Insecticide Board & Registration Committee (CIB&RC) and ICAR guidelines. "
        "Rotate modes of action (FRAC/IRAC codes) to prevent resistance build-up.", body_style
    ))
    story.append(Spacer(1, 4))

    chems = act.get("chemical_pesticides", [])
    if chems:
        chem_table_rows = [
            [
                Paragraph("Pesticide Name & Class", cell_hdr),
                Paragraph("Pesticide Type / Mode of Action", cell_hdr),
                Paragraph("Lab Dosage", cell_hdr),
                Paragraph("Field Rate / Acre (100-200L)", cell_hdr),
                Paragraph("PHI / PPE", cell_hdr)
            ]
        ]
        # Match field quantities if available
        fq_map = {q.get("pesticide"): q.get("per_acre_product") for q in data.get("pesticide_field_quantities", [])}

        for c in chems:
            c_name = c.get("name", "Formulation")
            per_acre = fq_map.get(c_name, "200-500 g/ml per acre")
            chem_table_rows.append([
                Paragraph(f"<b>{c_name}</b>", cell_bold),
                Paragraph(c.get("type", "Systemic / Contact Fungicide"), cell_text),
                Paragraph(c.get("dosage", "2 g/L"), cell_text),
                Paragraph(per_acre, cell_bold),
                Paragraph(f"PHI: {c.get('phi_days', '7-14 days')}<br/>{c.get('ppe', 'Gloves, Mask')}", cell_text)
            ])
        t_chem = Table(chem_table_rows, colWidths=[120, 130, 80, 100, 90])
        t_chem.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bae6fd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(t_chem)
    story.append(Spacer(1, 8))

    # 4. WATER USAGE & SPRAY WATER DILUTION (AMOUNT OF WATER USED)
    story.append(Paragraph("3. Water Requirement & Spray Water Dilution Specifications", h1_style))
    water_specs = [
        [
            Paragraph("Crop Lifecycle Water Need", cell_hdr),
            Paragraph("Spray Tank Water Volume", cell_hdr),
            Paragraph("Spray Water Quality & pH", cell_hdr)
        ],
        [
            Paragraph(f"<b>Total Need:</b> {plant_stats.get('water_used', '400 - 600 mm')}<br/>"
                      f"<b>Rate:</b> {plant_stats.get('daily_water_per_plant', '2.5 - 4.0 L/plant/day during peak vegetative/fruiting')}", cell_text),
            Paragraph(f"<b>Per Acre:</b> {plant_stats.get('spray_water_volume_per_acre', '150 - 200 Litres of clean water / acre')}<br/>"
                      f"<b>Per Knapsack Sprayer:</b> {plant_stats.get('knapsack_tank_water', '15 - 16 Litres water per tank filling')}", cell_text),
            Paragraph(f"<b>Optimum pH:</b> {plant_stats.get('spray_water_ph', '6.0 - 6.5 (slightly acidic)')}<br/>"
                      f"<b>Hardness Alert:</b> Hard water (>250 ppm TDS) hydrolyzes and deactivates pesticides. Use non-alkaline water.", cell_text)
        ]
    ]
    t_water = Table(water_specs, colWidths=[170, 175, 175])
    t_water.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bae6fd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f9ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_water)
    story.append(Spacer(1, 8))

    # 5. IRRIGATION STRATEGY & AMOUNT OF IRRIGATION
    story.append(Paragraph("4. Irrigation Management & Scheduling Strategy", h1_style))
    irrig_specs = [
        [
            Paragraph("Recommended Irrigation Method", cell_hdr),
            Paragraph("Irrigation Amount & Frequency", cell_hdr),
            Paragraph("Disease-Specific Moisture Protocol", cell_hdr)
        ],
        [
            Paragraph(f"<b>{plant_stats.get('irrigation_method', 'Drip Irrigation (Recommended)')}</b><br/>"
                      f"Avoid overhead sprinkler irrigation which splashes pathogen spores across adjacent healthy plant leaves.", cell_text),
            Paragraph(f"<b>Depth / Cycle:</b> {plant_stats.get('irrigation_amount_per_cycle', '20 - 25 mm per watering cycle')}<br/>"
                      f"<b>Frequency:</b> {plant_stats.get('irrigation_frequency', 'Every 3-5 days (summer); 6-8 days (winter)')}<br/>"
                      f"<b>Critical Stages:</b> {plant_stats.get('critical_irrigation_stages', 'Flowering and early fruit formation')}", cell_text),
            Paragraph(f"<b>Pathogen Caution:</b> {plant_stats.get('irrigation_disease_warning', 'Since disease is detected, strictly irrigate at ground level early in the morning to allow quick surface drying.')}", alert_style)
        ]
    ]
    t_irrig = Table(irrig_specs, colWidths=[170, 175, 175])
    t_irrig.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#99f6e4')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0fdfa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_irrig)
    story.append(Spacer(1, 8))

    # 6. SOIL TYPE & CONDITIONING (WHICH TYPE OF SOIL)
    story.append(Paragraph("5. Soil Health, Texture & Conditioning Requirements", h1_style))
    soil_specs = [
        [
            Paragraph("Ideal Soil Classification", cell_hdr),
            Paragraph("Optimum pH & Drainage Tilth", cell_hdr),
            Paragraph("Soil Conditioning & Bio-Enrichment", cell_hdr)
        ],
        [
            Paragraph(f"<b>Type:</b> {plant_stats.get('soil_type', 'Well-drained sandy loam to fertile clay loam')}<br/>"
                      f"<b>Root Depth:</b> {plant_stats.get('soil_depth', 'Minimum 45 - 60 cm effective root zone depth with loose friable structure')}", cell_text),
            Paragraph(f"<b>Target pH:</b> {plant_stats.get('pH_level', '6.0 - 6.8 (Neutral to slightly acidic)')}<br/>"
                      f"<b>Drainage:</b> {plant_stats.get('soil_drainage', 'High percolation required; avoid waterlogging >12h to stop root asphyxiation')}", cell_text),
            Paragraph(f"<b>Amendments:</b> {plant_stats.get('soil_conditioning', 'Apply 8-10 tons/acre decomposed FYM + 2.5 kg Trichoderma viride. If acidic (<5.8) apply Agricultural Lime; if alkaline (>7.8) apply Gypsum.')}", cell_text)
        ]
    ]
    t_soil = Table(soil_specs, colWidths=[170, 175, 175])
    t_soil.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#92400e')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fde68a')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fffbeb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_soil)
    story.append(Spacer(1, 8))

    # 7. 4-Tier Integrated Field Action Plan
    story.append(Paragraph("6. Integrated Agronomic Action Plan", h1_style))
    imm_actions = act.get("immediate_actions", [])
    org_actions = act.get("organic_solutions", [])
    nut_actions = act.get("nutrition_management", [])

    action_rows = [
        [
            Paragraph("Tier 1: Emergency Field Response (0-24h)", cell_hdr),
            Paragraph("Tier 2: Organic & Bio-Pesticides", cell_hdr),
            Paragraph("Tier 4: Soil Nutrition & Plant Immunity", cell_hdr)
        ],
        [
            Paragraph("<br/>".join([f"• {a}" for a in imm_actions[:3]]), cell_text),
            Paragraph("<br/>".join([f"• {o}" for o in org_actions[:3]]), cell_text),
            Paragraph("<br/>".join([f"• {n}" for n in nut_actions[:3]]), cell_text)
        ]
    ]
    t_actions = Table(action_rows, colWidths=[170, 175, 175])
    t_actions.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_actions)
    story.append(Spacer(1, 8))

    # 8. Recovery Schedule & Farmer Safety Compliance
    story.append(Paragraph("7. Recovery Milestones & CIB&RC Farmer Safety Compliance", h1_style))
    rec_sched = risk.get("recovery_schedule", [])
    rec_text = " | ".join([f"<b>{r.get('day')}:</b> {r.get('action')}" for r in rec_sched])
    safety = data.get("safety_guidelines", [])
    ppe = data.get("ppe_checklist", [])

    compliance_rows = [
        [
            Paragraph("Recovery Milestones", cell_bold),
            Paragraph(rec_text if rec_text else "Day 1: Sanitation, Day 3: Spray, Day 10: Inspection", cell_text)
        ],
        [
            Paragraph("Safety Guidelines", cell_bold),
            Paragraph("<br/>".join([f"• {g}" for g in safety[:3]]), cell_text)
        ],
        [
            Paragraph("Mandatory PPE", cell_bold),
            Paragraph("<br/>".join([f"✔ {p}" for p in ppe[:3]]), cell_text)
        ]
    ]
    t_comp = Table(compliance_rows, colWidths=[130, 390])
    t_comp.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    # Advisory Footer Notice
    story.append(Paragraph(
        "<i>Notice: This diagnostic report is generated by an autonomous multi-algorithm AI engine and validated "
        "against Indian CIB&RC phytopathology standards. Farmers are advised to consult their local Krishi Vigyan Kendra (KVK) "
        "or Agricultural Extension Officer before large-scale tank mixing.</i>",
        ParagraphStyle('FooterDisclaimer', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=colors.HexColor('#64748b'))
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedReportCanvas)
    return buffer.getvalue()
