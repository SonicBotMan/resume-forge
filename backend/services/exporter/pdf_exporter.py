from pathlib import Path
from typing import Dict, Any
import asyncio
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Register Chinese font - use ReportLab built-in CID font
_font_name = "Helvetica"  # fallback
try:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    _font_name = 'STSong-Light'
except Exception:
    pass


async def export_to_pdf(content: Dict[str, Any], template_id: str, name: str) -> str:
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{name}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = {
        "title": ParagraphStyle(
            "Title", fontName=_font_name, fontSize=18, alignment=TA_CENTER, spaceAfter=20
        ),
        "section": ParagraphStyle(
            "Section",
            fontName=_font_name,
            fontSize=12,
            textColor=colors.HexColor("#333333"),
            spaceBefore=15,
            spaceAfter=8,
            borderPadding=(0, 0, 3, 0),
            borderColor=colors.HexColor("#cccccc"),
            borderWidth=0,
        ),
        "summary": ParagraphStyle(
            "Summary",
            fontName=_font_name,
            fontSize=10,
            backColor=colors.HexColor("#f5f5f5"),
            spaceBefore=10,
            spaceAfter=10,
            padding=8,
        ),
        "project_title": ParagraphStyle(
            "ProjectTitle", fontName=_font_name, fontSize=11, textColor=colors.HexColor("#333333")
        ),
        "meta": ParagraphStyle(
            "Meta", fontName=_font_name, fontSize=9, textColor=colors.HexColor("#666666")
        ),
        "field": ParagraphStyle(
            "Field", fontName=_font_name, fontSize=9, textColor=colors.HexColor("#555555")
        ),
        "skill": ParagraphStyle("Skill", fontName=_font_name, fontSize=9),
    }

    story = []

    story.append(Paragraph(name, styles["title"]))
    story.append(Spacer(1, 5 * mm))

    summary = content.get("summary", "")
    if summary:
        story.append(Paragraph(summary, styles["summary"]))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("项目经历", styles["section"]))

    for project in content.get("projects", []):
        project_rows = [
            [Paragraph(f"<b>{project.get('name', '')}</b>", styles["project_title"])],
        ]
        role_text = project.get('role', '')
        start_date = project.get('start_date', '')
        end_date = project.get('end_date', '')
        if role_text or start_date or end_date:
            project_rows.append(
                [Paragraph(
                    f"角色: {role_text} | 时间: {start_date} - {end_date}",
                    styles["meta"],
                )]
            )
        star_fields = [
            ("背景", "situation"),
            ("任务", "task"),
            ("行动", "action"),
            ("成果", "result"),
        ]
        has_star = any(project.get(k) for _, k in star_fields)
        if has_star:
            for label, key in star_fields:
                val = project.get(key, '')
                if val:
                    project_rows.append([Paragraph(f"<b>{label}:</b> {val}", styles["field"])])
        elif project.get('description'):
            project_rows.append([Paragraph(project['description'], styles["field"])])
        project_data = project_rows
        table = Table(project_data, colWidths=[170 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#007bff")),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("技能", styles["section"]))

    skills = content.get("skills") or []
    if isinstance(skills, dict):
        flat = []
        for v in skills.values():
            if isinstance(v, list):
                flat.extend(v)
            elif isinstance(v, str):
                flat.append(v)
        skills = flat
    skills_text = " | ".join(str(s) for s in skills) if skills else ""
    story.append(Paragraph(skills_text, styles["skill"]))

    experience = content.get("experience", [])
    if experience:
        story.append(Paragraph("工作经历", styles["section"]))
        for exp in experience:
            if isinstance(exp, str):
                story.append(Paragraph(exp, styles["field"]))
            elif isinstance(exp, dict):
                exp_text = f"{exp.get('company', exp.get('name', ''))} | {exp.get('role', exp.get('position', ''))} | {exp.get('period', exp.get('time', ''))}"
                story.append(Paragraph(exp_text, styles["meta"]))
                if exp.get("highlights"):
                    for h in exp["highlights"]:
                        story.append(Paragraph(f"• {h}", styles["field"]))
                elif exp.get("description"):
                    story.append(Paragraph(exp.get("description", ""), styles["field"]))

    education = content.get("education", [])
    if education:
        story.append(Paragraph("教育背景", styles["section"]))
        for edu in education:
            if isinstance(edu, str):
                story.append(Paragraph(edu, styles["field"]))
            elif isinstance(edu, dict):
                edu_text = f"{edu.get('school', edu.get('name', ''))} | {edu.get('major', '')} | {edu.get('degree', '')} | {edu.get('period', edu.get('time', ''))}"
                story.append(Paragraph(edu_text, styles["meta"]))

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, doc.build, story)
    return str(output_path)
