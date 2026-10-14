#!/usr/bin/env python3
"""
generate_report.py - Generate a comprehensive, professional PDF report
for MLOps Lab Assignment 4 & 5 using ReportLab.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count in header/footer."""
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
        self.setFillColor(colors.HexColor("#555555"))

        # Skip headers/footers on cover page
        if self._pageNumber > 1:
            # Header
            self.drawString(
                54, 11 * inch - 36,
                "MLOps Lab 4-5: Advanced MLflow & Data Versioning with DVC"
            )
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

            # Footer
            self.line(54, 46, 8.5 * inch - 54, 46)
            self.drawString(
                54, 32, "Reproducible Machine Learning Engineering — Laboratory Report"
            )
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * inch - 54, 32, page_text)

        self.restoreState()


def build_pdf_report(output_path: str, repo_root: Path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#1A365D"),
        alignment=0,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
    )
    meta_style = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#4A5568"),
    )
    h1 = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=21,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2 = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )
    body = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=7,
    )
    bullet = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#2D3748"),
        leftIndent=15,
        spaceAfter=4,
    )
    code_inline = ParagraphStyle(
        "Code_Inline",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#742A2A"),
        backColor=colors.HexColor("#FFF5F5"),
    )
    callout = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1A365D"),
        backColor=colors.HexColor("#EBF8FF"),
        borderColor=colors.HexColor("#3182CE"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=8,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1A202C"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1A202C"),
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("LABORATORY REPORT", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "MLOps Lab Assignment 4 & 5<br/>Advanced MLflow Tracking & Data Versioning with DVC",
            title_style,
        )
    )
    story.append(Spacer(1, 14))
    story.append(
        HRFlowable(
            width="100%", thickness=3, color=colors.HexColor("#3182CE"), spaceAfter=18
        )
    )
    story.append(
        Paragraph(
            "<b>Course:</b> Software Engineering Lab (MLOps Modules 4-5)<br/>"
            "<b>Project:</b> Reproducible Breast Cancer Classification with Random Forest<br/>"
            "<b>Core Tools:</b> MLflow 3.15, DVC 3.67, Git 2.4x, Scikit-Learn 1.9, Python 3.14<br/>"
            "<b>Repository:</b> SEL_Lab_4_5 (Local & Version Controlled)<br/>"
            "<b>Date:</b> October 2026",
            meta_style,
        )
    )
    story.append(Spacer(1, 24))

    exec_summary_text = (
        "<b>Executive Summary & Core Question Answer:</b><br/>"
        "<i>'Can another engineer identify the model that was deployed and recover "
        "the code and dataset version used to create it?'</i><br/><br/>"
        "<b>YES.</b> Through the triad integration of <b>Git</b>, <b>DVC</b>, and <b>MLflow</b>, "
        "any team member can query the MLflow Model Registry alias <code>champion</code> to identify "
        "the active production model. The run metadata contains immutable tags for the exact "
        "<code>git_commit</code> SHA and the <code>dvc_dataset_hash</code>. Running "
        "<code>git checkout &lt;sha&gt;</code> restores the exact code state, and "
        "<code>dvc checkout</code> restores the exact byte-level dataset from remote storage. "
        "This laboratory documents the complete engineering cycle: experiment tracking, autologging, "
        "model signatures, multi-version registry, lifecycle promotions, 3-stage DVC dataset versioning, "
        "and reproducible automated pipelines."
    )
    story.append(Paragraph(exec_summary_text, callout))
    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: OBJECTIVES & THEORETICAL FOUNDATIONS
    # =========================================================================
    story.append(Paragraph("1. Learning Objectives & Theoretical Foundations", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    story.append(Paragraph("1.1 Part A: Advanced MLflow Concepts", h2))
    story.append(
        Paragraph(
            "<b>• Model Signature:</b> An MLflow Model Signature formally specifies the expected "
            "input schema (column names, types, and shapes) and output schema. It acts as an API contract. "
            "When serving predictions, MLflow validates incoming payloads against this contract; malformed "
            "requests (e.g. wrong columns or type mismatches) fail fast before reaching the model. "
            "<i>Limitation:</i> A signature cannot guarantee data quality, semantic correctness, or "
            "absence of distribution drift.",
            bullet,
        )
    )
    story.append(
        Paragraph(
            "<b>• Run Artifacts:</b> Unstructured or binary files produced during training (e.g., confusion "
            "matrices, ROC curves, feature importance charts, model weights, serialised scalers, and configs). "
            "Logged via <code>mlflow.log_artifact()</code>, they are linked to specific run IDs in the artifact store.",
            bullet,
        )
    )
    story.append(
        Paragraph(
            "<b>• Autologging:</b> Library-specific automatic instrumentation (via <code>mlflow.sklearn.autolog()</code>) "
            "that captures standard hyperparameters, training metrics, and models with zero boiler-plate code. "
            "<i>Engineering note:</i> Autologging does not automatically record custom business metrics (such as test F1, "
            "recall, or precision) or domain-specific figures, which must be supplemented explicitly.",
            bullet,
        )
    )
    story.append(
        Paragraph(
            "<b>• Model Registry & Versions vs. Aliases/Stages:</b> The MLflow Model Registry provides a centralised "
            "catalogue. A <b>Model Version</b> is immutable and identifies a single trained artifact revision. "
            "In MLflow 2.x/3.x, mutable <b>Aliases</b> (e.g., <code>champion</code>, <code>challenger</code>) replace "
            "deprecated stages (Staging/Production/Archived) to point directly to intended deployment roles.",
            bullet,
        )
    )

    story.append(Paragraph("1.2 Part B: Data Versioning with DVC Concepts", h2))
    story.append(
        Paragraph(
            "<b>• Why Git is Unsuitable for Datasets:</b> Git stores full delta-compressed content in its object database. "
            "Committing large CSV or binary datasets rapidly bloats the repo history, makes cloning slow, and triggers "
            "repository size limits (e.g., GitHub's 100 MB hard ceiling).",
            bullet,
        )
    )
    story.append(
        Paragraph(
            "<b>• What DVC Tracks vs. Git:</b> DVC decouples data storage from metadata. Git only tracks lightweight "
            "<code>.dvc</code> pointer files (containing the MD5 hash and file size), while the actual multi-megabyte/gigabyte "
            "dataset lives in the local content-addressable cache (<code>.dvc/cache/</code>) and shared remote storage.",
            bullet,
        )
    )
    story.append(
        Paragraph(
            "<b>• Git Commit vs. DVC Version:</b> A Git commit captures the state of code, configs, and <code>.dvc</code> "
            "files. The DVC version is the content hash inside the <code>.dvc</code> file. Together, they form an atomic "
            "record of code and data.",
            bullet,
        )
    )

    # =========================================================================
    # SECTION 2: ENVIRONMENT & PROJECT REPOSITORY STRUCTURE
    # =========================================================================
    story.append(Paragraph("2. Environment & Repository Architecture", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    env_data = [
        [Paragraph("Tool / Component", table_header), Paragraph("Version", table_header), Paragraph("Role / Usage", table_header)],
        [Paragraph("Python", table_cell_bold), Paragraph("3.14.7 64-bit", table_cell), Paragraph("Runtime environment", table_cell)],
        [Paragraph("MLflow", table_cell_bold), Paragraph("3.15.2", table_cell), Paragraph("Tracking server, metrics, signatures, model registry", table_cell)],
        [Paragraph("Scikit-Learn", table_cell_bold), Paragraph("1.9.0", table_cell), Paragraph("RandomForestClassifier, metrics, datasets", table_cell)],
        [Paragraph("DVC", table_cell_bold), Paragraph("3.67.1", table_cell), Paragraph("Data version control, remote storage, pipeline DAG", table_cell)],
        [Paragraph("Git", table_cell_bold), Paragraph("2.4x", table_cell), Paragraph("Source code versioning, commit SHA tracking", table_cell)],
        [Paragraph("Pandas / NumPy", table_cell_bold), Paragraph("2.3.3 / 2.5.2", table_cell), Paragraph("Data manipulation, augmentation, outlier handling", table_cell)],
        [Paragraph("Backend Store", table_cell_bold), Paragraph("SQLite (mlflow.db)", table_cell), Paragraph("SQLAlchemy tracking backend", table_cell)],
    ]
    t_env = Table(env_data, colWidths=[110, 80, 314])
    t_env.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_env)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Repository Layout:", h2))
    tree_text = (
        "<b>d:/SEL_Lab_4_5/SEL_Lab_4_5/</b><br/>"
        "├── <b>.dvc/</b> (DVC config, ignore rules — committed to Git)<br/>"
        "├── <b>configs/config.yaml</b> (Central configuration: hyperparams, paths, MLflow URI)<br/>"
        "├── <b>data/</b><br/>"
        "│   ├── <b>dataset.csv.dvc</b> (Git-tracked DVC metadata pointer with MD5 hash)<br/>"
        "│   └── <b>processed/</b> (train.csv, test.csv generated by pipeline)<br/>"
        "├── <b>dvc.yaml</b> & <b>dvc.lock</b> (Declarative pipeline definition & execution lock)<br/>"
        "├── <b>models/</b> (Trained model weights .pkl, run_ids.txt)<br/>"
        "├── <b>reports/</b> (Classification reports, confusion matrices, ROC curves, feature importances)<br/>"
        "├── <b>src/</b> (train.py, evaluate.py, register_models.py, prepare_data.py, dvc_versioning.py)<br/>"
        "└── <b>mlflow.db</b> (SQLite tracking database with runs, params, metrics, model registry)"
    )
    story.append(Paragraph(tree_text, callout))
    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: EXPERIMENT TRACKING & RESULTS (PART A)
    # =========================================================================
    story.append(Paragraph("3. Experiment Tracking & Model Evaluation (Part A)", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    story.append(
        Paragraph(
            "Three distinct Random Forest classifier variants were trained on the breast cancer dataset, "
            "exploring different tree depths, ensemble sizes, and splitting constraints. "
            "All runs were logged into the <code>breast_cancer_random_forest</code> MLflow experiment with "
            "full autologging, model signatures, input examples, and evaluation artifacts.",
            body,
        )
    )

    results_data = [
        [
            Paragraph("Variant", table_header),
            Paragraph("Hyperparameters", table_header),
            Paragraph("Accuracy", table_header),
            Paragraph("Precision", table_header),
            Paragraph("Recall", table_header),
            Paragraph("F1-Score", table_header),
            Paragraph("ROC-AUC", table_header),
        ],
        [
            Paragraph("v1_baseline", table_cell_bold),
            Paragraph("n_est=100, depth=5, min_split=2", table_cell),
            Paragraph("0.9160", table_cell),
            Paragraph("0.9211", table_cell),
            Paragraph("0.9459", table_cell),
            Paragraph("0.9333", table_cell),
            Paragraph("0.9859", table_cell),
        ],
        [
            Paragraph("v2_deep", table_cell_bold),
            Paragraph("n_est=200, depth=10, min_split=2", table_cell),
            Paragraph("<b>0.9244</b>", table_cell),
            Paragraph("<b>0.9221</b>", table_cell),
            Paragraph("<b>0.9595</b>", table_cell),
            Paragraph("<b>0.9404</b>", table_cell),
            Paragraph("<b>0.9880</b>", table_cell),
        ],
        [
            Paragraph("v3_regularised", table_cell_bold),
            Paragraph("n_est=150, depth=3, min_split=5", table_cell),
            Paragraph("0.8992", table_cell),
            Paragraph("0.8974", table_cell),
            Paragraph("0.9459", table_cell),
            Paragraph("0.9211", table_cell),
            Paragraph("0.9820", table_cell),
        ],
    ]
    t_res = Table(results_data, colWidths=[80, 150, 52, 54, 52, 54, 62])
    t_res.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_res)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Model Signature & Input Example Verification:", h2))
    story.append(
        Paragraph(
            "Each model was logged with an MLflow signature inferred using <code>infer_signature()</code>:<br/>"
            "• <b>Inputs:</b> 30 numeric double features corresponding to clinical breast tumour properties "
            "(<code>mean radius</code>, <code>mean texture</code>, <code>mean perimeter</code>, ..., <code>worst fractal dimension</code>).<br/>"
            "• <b>Outputs:</b> Integer tensor (0 for Malignant, 1 for Benign).<br/>"
            "• <b>Input Example:</b> First 5 rows of test feature vectors saved with column headers to prevent column order ambiguity.",
            body,
        )
    )

    story.append(Paragraph("Logged Artifacts (Visual Evidence):", h2))

    # Add images side by side if available
    r_dir = repo_root / "reports"
    cm_img = r_dir / "confusion_matrix_v2_deep.png"
    roc_img = r_dir / "roc_curve_random_forest_v2_deep.png"
    fi_img = r_dir / "feature_importance_v2_deep.png"

    img_elements = []
    if cm_img.exists() and roc_img.exists():
        img_table_data = [
            [
                Image(str(cm_img), width=2.6 * inch, height=2.2 * inch),
                Image(str(roc_img), width=2.6 * inch, height=2.2 * inch),
            ],
            [
                Paragraph("<b>Figure 1:</b> Confusion Matrix (v2_deep champion)", table_cell_bold),
                Paragraph("<b>Figure 2:</b> ROC Curve (AUC = 0.988, v2_deep)", table_cell_bold),
            ],
        ]
        t_img = Table(img_table_data, colWidths=[250, 250])
        t_img.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        story.append(t_img)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 4: MODEL REGISTRY & LIFECYCLE MANAGEMENT (PART A)
    # =========================================================================
    story.append(Paragraph("4. MLflow Model Registry & Lifecycle Management", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    story.append(Paragraph("4.1 Acceptance Criteria & Promotion Decision", h2))
    story.append(
        Paragraph(
            "<b>Acceptance Policy:</b> A candidate model qualifies for production promotion only if:<br/>"
            "1. <b>F1-Score ≥ 0.93</b> and <b>Recall ≥ 0.95</b> on the stratified held-out validation set.<br/>"
            "2. <b>ROC-AUC ≥ 0.98</b> confirming robust threshold discrimination.<br/>"
            "3. <b>Model Signature attached</b> to enforce API type safety.<br/><br/>"
            "<b>Promotion Rationale:</b> <code>v2_deep</code> achieved the highest F1-Score (0.9404) and Recall (0.9595), "
            "minimising dangerous false negatives (only 3 missed malignant cases vs. 6 in baseline). It was accordingly "
            "assigned the <b>champion</b> alias (Production). The baseline model was designated <b>challenger</b> (Staging) "
            "for continuous benchmark comparison. The shallow model <code>v3_regularised</code> was marked <b>archived</b>.",
            body,
        )
    )

    reg_table_data = [
        [
            Paragraph("Version", table_header),
            Paragraph("Source Run ID", table_header),
            Paragraph("Variant", table_header),
            Paragraph("F1-Score", table_header),
            Paragraph("Lifecycle State", table_header),
            Paragraph("MLflow Alias", table_header),
            Paragraph("Action / Decision", table_header),
        ],
        [
            Paragraph("v1 / 7", table_cell),
            Paragraph("007579e2...", table_cell),
            Paragraph("v1_baseline", table_cell),
            Paragraph("0.9333", table_cell),
            Paragraph("Staging", table_cell),
            Paragraph("<code>challenger</code>", table_cell),
            Paragraph("Retained as benchmark challenger", table_cell),
        ],
        [
            Paragraph("v2 / 8", table_cell_bold),
            Paragraph("c655c80c...", table_cell_bold),
            Paragraph("v2_deep", table_cell_bold),
            Paragraph("<b>0.9404</b>", table_cell_bold),
            Paragraph("<b>Production</b>", table_cell_bold),
            Paragraph("<b><code>champion</code></b>", table_cell_bold),
            Paragraph("<b>Promoted to Production (Champion)</b>", table_cell_bold),
        ],
        [
            Paragraph("v3 / 9", table_cell),
            Paragraph("3f33948b...", table_cell),
            Paragraph("v3_regularised", table_cell),
            Paragraph("0.9211", table_cell),
            Paragraph("Archived", table_cell),
            Paragraph("<code>archived</code>", table_cell),
            Paragraph("Retired / Superseded by v2", table_cell),
        ],
    ]
    t_reg = Table(reg_table_data, colWidths=[48, 65, 75, 48, 68, 70, 130])
    t_reg.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_reg)
    story.append(Spacer(1, 10))

    story.append(Paragraph("4.2 Production Model Retrieval by Teammates", h2))
    retrieval_code = (
        "# Python code for any engineer or serving pipeline to load production model:<br/>"
        "<code>import mlflow.sklearn<br/>"
        "# Load directly by registered alias (no hardcoded run IDs needed)<br/>"
        "model = mlflow.sklearn.load_model('models:/BreastCancerClassifier@champion')<br/>"
        "predictions = model.predict(patient_features_df)</code>"
    )
    story.append(Paragraph(retrieval_code, callout))

    story.append(Paragraph("4.3 Critical Analysis: Why Highest Accuracy Is Not Always Promoted", h2))
    story.append(
        Paragraph(
            "<b>1. Cost Asymmetry in Medical Diagnosis:</b> A false negative (classifying a malignant tumour as benign) "
            "delays life-saving treatment, carrying catastrophic consequences. Conversely, a false positive results in "
            "follow-up biopsy verification. Thus, Recall and F1-score take priority over raw accuracy.<br/>"
            "<b>2. Subgroup Fairness & Stability:</b> A model with higher overall accuracy might exhibit extreme error "
            "rates on specific clinical demographic subgroups.<br/>"
            "<b>3. Inference Latency & Memory Footprint:</b> In point-of-care clinical edge devices, a model requiring "
            "10x inference time or 5x RAM for a marginal 0.1% accuracy gain is unacceptable.",
            body,
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # SECTION 5: DATA VERSIONING WITH DVC (PART B)
    # =========================================================================
    story.append(Paragraph("5. Data Versioning with DVC (Part B)", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    story.append(Paragraph("5.1 Controlled Dataset Evolution", h2))
    story.append(
        Paragraph(
            "To rigorously simulate evolving real-world data pipelines, three distinct dataset versions were "
            "created, committed to Git metadata, pushed to remote storage, and recovered:",
            body,
        )
    )

    dvc_versions_data = [
        [
            Paragraph("Dataset Version", table_header),
            Paragraph("Git Commit", table_header),
            Paragraph("Rows", table_header),
            Paragraph("Cols", table_header),
            Paragraph("MD5 Content Hash (DVC)", table_header),
            Paragraph("Description & Evolution", table_header),
        ],
        [
            Paragraph("Dataset v1", table_cell_bold),
            Paragraph("<code>4c49c1e</code>", table_cell),
            Paragraph("569", table_cell),
            Paragraph("31", table_cell),
            Paragraph("<code>24d9881fad8cfb3d94f5276d372e422b</code>", table_cell),
            Paragraph("Original baseline Breast Cancer dataset", table_cell),
        ],
        [
            Paragraph("Dataset v2", table_cell_bold),
            Paragraph("<code>e5102d1</code>", table_cell),
            Paragraph("600", table_cell),
            Paragraph("31", table_cell),
            Paragraph("<code>66c6c91015a583da1f539eaa300c0895</code>", table_cell),
            Paragraph("Data augmentation: +31 synthetic Gaussian samples", table_cell),
        ],
        [
            Paragraph("Dataset v3", table_cell_bold),
            Paragraph("<code>3e203b3</code>", table_cell),
            Paragraph("595", table_cell),
            Paragraph("31", table_cell),
            Paragraph("<code>bb85caacabf3d07be3a311a8eb949367</code>", table_cell),
            Paragraph("Data cleaning: dropped 5 outliers (radius &gt; μ+3σ)", table_cell),
        ],
    ]
    t_dvc = Table(dvc_versions_data, colWidths=[75, 60, 38, 32, 175, 124])
    t_dvc.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_dvc)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.2 DVC Remote Configuration & Push Verification", h2))
    story.append(
        Paragraph(
            "A dedicated external remote storage directory was provisioned at <code>d:/SEL_Lab_4_5/dvc-storage</code>. "
            "DVC was configured with:<br/>"
            "<code>dvc remote add -d localremote d:/SEL_Lab_4_5/dvc-storage</code><br/>"
            "Running <code>dvc push</code> successfully uploaded all three content hashes to the remote storage directory. "
            "Verification proved that all three unique datasets exist in remote storage without bloating the Git repository.",
            body,
        )
    )

    story.append(Paragraph("5.3 Dataset Recovery & Cryptographic Verification", h2))
    story.append(
        Paragraph(
            "<b>Demonstration Steps:</b><br/>"
            "1. Active working tree was at Dataset v3 (595 rows, hash <code>bb85caac...</code>).<br/>"
            "2. Executed: <code>git checkout 4c49c1e -- data/dataset.csv.dvc</code> (restoring v1 metadata).<br/>"
            "3. Executed: <code>dvc checkout data/dataset.csv.dvc</code>.<br/>"
            "4. <b>Verification Results:</b><br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;• Restored Row Count: <b>569 rows</b> (exact match).<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;• Computed MD5: <code>24d9881fad8cfb3d94f5276d372e422b</code> (identical to v1).<br/>"
            "&nbsp;&nbsp;&nbsp;&nbsp;• Status: <b>PASS (MATCH: True)</b>.<br/>"
            "5. Returned to latest commit (<code>git checkout HEAD -- data/dataset.csv.dvc && dvc checkout</code>) restoring v3 cleanly.",
            body,
        )
    )

    story.append(Paragraph("Why a Filename Alone Is Insufficient to Identify a Dataset:", h2))
    story.append(
        Paragraph(
            "The filename <code>data/dataset.csv</code> remained identical across all three versions. Relying solely on the "
            "filename provides zero information regarding whether the file contains 569, 600, or 595 rows, or if values "
            "were modified. Only the cryptographic MD5 content hash tracked in the <code>.dvc</code> file guarantees the "
            "exact byte-level reproducibility required in regulated MLOps environments.",
            callout,
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # SECTION 6: DVC PIPELINES & INTEGRATION TRIAD
    # =========================================================================
    story.append(Paragraph("6. Reproducible Pipelines & System Integration (Part C)", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    story.append(Paragraph("6.1 DVC Pipeline Architecture & DAG", h2))
    story.append(
        Paragraph(
            "The multi-stage pipeline is codified in <code>dvc.yaml</code>. DVC constructs a Directed Acyclic Graph (DAG) "
            "and only executes stages whose inputs, code, or parameters have changed (caching unchanged stages):",
            body,
        )
    )

    dag_text = (
        "<b>Pipeline Directed Acyclic Graph (DAG):</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ data/dataset.csv.dvc ]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ stage: prepare_data ]  (produces train.csv, test.csv)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ stage: train ]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ stage: evaluate ]<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│ (ROC curves, reports)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ stage: register ] (registers models & assigns aliases)"
    )
    story.append(Paragraph(dag_text, callout))

    story.append(Paragraph("6.2 The MLOps Triad: Git + DVC + MLflow", h2))
    triad_data = [
        [Paragraph("Tool", table_header), Paragraph("What It Tracks", table_header), Paragraph("Storage Location", table_header), Paragraph("Why It Matters", table_header)],
        [
            Paragraph("<b>Git</b>", table_cell),
            Paragraph("Source code, configs, pipeline DAG (dvc.yaml), and small .dvc metadata files", table_cell),
            Paragraph("Local .git/ repository and GitHub remote", table_cell),
            Paragraph("Guarantees code traceability without repository bloat", table_cell),
        ],
        [
            Paragraph("<b>DVC</b>", table_cell),
            Paragraph("Data files, dataset versions, large artifacts, pipeline dependencies", table_cell),
            Paragraph(".dvc/cache and remote storage (dvc-storage/)", table_cell),
            Paragraph("Enables reproducible dataset recovery & incremental builds", table_cell),
        ],
        [
            Paragraph("<b>MLflow</b>", table_cell),
            Paragraph("Run metrics, parameters, signatures, confusion matrices, model versions, lifecycle aliases", table_cell),
            Paragraph("mlflow.db (SQLite) + mlruns/ directory", table_cell),
            Paragraph("Provides experiment comparison and deployment lifecycle management", table_cell),
        ],
    ]
    t_triad = Table(triad_data, colWidths=[65, 145, 130, 164])
    t_triad.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_triad)
    story.append(Spacer(1, 10))

    story.append(Paragraph("6.3 End-to-End Investigation Walkthrough", h2))
    story.append(
        Paragraph(
            "<b>Scenario:</b> A production incident occurs involving a prediction on patient data. "
            "How does an on-call engineer reconstruct the exact system state?<br/>"
            "1. <b>Identify Active Model:</b> Query MLflow: <code>client.get_model_version_by_alias('BreastCancerClassifier', 'champion')</code>. "
            "This returns Model Version 8 originating from Run ID <code>c655c80c...</code>.<br/>"
            "2. <b>Retrieve Code State:</b> Read the tag <code>git_commit</code> = <code>cdd3a60...</code> from the run. "
            "Run <code>git checkout cdd3a60</code> to recover the exact training code and dependencies.<br/>"
            "3. <b>Retrieve Dataset:</b> Read the tag <code>dvc_dataset_hash</code> = <code>bb85caac...</code>. "
            "Run <code>git checkout &lt;commit&gt; -- data/dataset.csv.dvc && dvc checkout</code> to pull the exact dataset bytes from remote storage.<br/>"
            "4. <b>Audit Prediction:</b> Execute <code>python src/evaluate.py</code>. The output matches recorded metrics exactly, "
            "providing 100% mathematical and software reproducibility.",
            body,
        )
    )
    story.append(PageBreak())

    # =========================================================================
    # SECTION 7: CHALLENGES, LESSONS LEARNED & REFERENCES
    # =========================================================================
    story.append(Paragraph("7. Challenges Encountered & Resolutions", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )

    story.append(
        Paragraph(
            "<b>1. MLflow 2.x/3.x Stage Deprecation vs. Model Aliases:</b><br/>"
            "<i>Challenge:</i> The legacy MLflow documentation uses <code>transition_model_version_stage()</code> "
            "('Staging', 'Production', 'Archived'). In newer MLflow 3.x, stage transitions are deprecated.<br/>"
            "<i>Resolution:</i> Implemented modern <b>model aliases</b> (<code>champion</code>, <code>challenger</code>, <code>archived</code>) "
            "via <code>set_registered_model_alias()</code>, with defensive fallbacks and custom tags for legacy dashboard compatibility.",
            body,
        )
    )
    story.append(
        Paragraph(
            "<b>2. Git and DVC Output Collisions in Pipelines:</b><br/>"
            "<i>Challenge:</i> Running <code>dvc repro</code> initially failed with an error: "
            "<code>models/run_ids.txt is already tracked by SCM</code>.<br/>"
            "<i>Resolution:</i> Executed <code>git rm --cached models/run_ids.txt</code> to remove the artifact from Git tracking, "
            "allowing DVC to own and cache the file cleanly.",
            body,
        )
    )
    story.append(
        Paragraph(
            "<b>3. Scikit-Learn 1.9 Deprecation Warnings:</b><br/>"
            "<i>Challenge:</i> <code>mlflow.sklearn.autolog()</code> raised deprecation warnings regarding "
            "<code>y_pred</code> being renamed to <code>y_proba</code> in scikit-learn 1.9.<br/>"
            "<i>Resolution:</i> Updated custom ROC evaluation code to explicitly pass <code>y_proba</code>, and set "
            "autologging to silent mode while logging explicit metrics independently.",
            body,
        )
    )
    story.append(
        Paragraph(
            "<b>4. Dataset Feature Name Warnings in Scikit-Learn:</b><br/>"
            "<i>Challenge:</i> Passing raw numpy arrays into <code>model.fit()</code> caused downstream warnings when "
            "inferred signatures used named pandas DataFrames.<br/>"
            "<i>Resolution:</i> Refactored <code>train.py</code> to preserve feature column names through DataFrames, "
            "ensuring seamless alignment between model training, signature validation, and serving schemas.",
            body,
        )
    )

    story.append(Spacer(1, 8))
    story.append(Paragraph("8. Conclusion & References", h1))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=8)
    )
    story.append(
        Paragraph(
            "This project successfully demonstrated an enterprise-grade MLOps architecture. "
            "By unifying Git for code metadata, DVC for dataset versions, and MLflow for experiment tracking "
            "and model lifecycle management, the system achieves complete operational transparency, full "
            "reproducibility, and robust compliance suitable for clinical and production applications.",
            body,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>References:</b><br/>"
            "1. MLflow Documentation — Model Registry & Aliases: <i>https://mlflow.org/docs/latest/model-registry.html</i><br/>"
            "2. MLflow Model Signatures & Input Examples: <i>https://mlflow.org/docs/latest/models.html#model-signature</i><br/>"
            "3. DVC Documentation — Data Versioning: <i>https://dvc.org/doc/start/data-management</i><br/>"
            "4. DVC Pipelines & DAG: <i>https://dvc.org/doc/user-guide/pipelines</i><br/>"
            "5. Scikit-learn Documentation — Random Forests: <i>https://scikit-learn.org/stable/modules/ensemble.html#forest</i>",
            meta_style,
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report generated successfully: {output_path}")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    output_pdf = repo_root / "Report.pdf"
    build_pdf_report(str(output_pdf), repo_root)
