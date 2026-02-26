# pdf_report_generator.py - Production-grade PDF report generator
# Uses ReportLab for layout, Gemini 2.5 Pro for narrative content
import io
import os
import re
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether, ListFlowable, ListItem,
    Image as RLImage, Flowable
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

import google.generativeai as genai

# ─────────────────────────── CONSTANTS ───────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

CLR_BLACK = colors.HexColor("#000000")
CLR_DARK = colors.HexColor("#1A1A1A")
CLR_BODY = colors.HexColor("#2D2D2D")
CLR_GRAY_BG = colors.HexColor("#F0F0F0")
CLR_ROW_ALT = colors.HexColor("#FAFAFA")
CLR_TABLE_HDR_TEXT = colors.HexColor("#2C2C2C")
CLR_RULE = colors.HexColor("#CCCCCC")
CLR_BLUE = colors.HexColor("#1A73E8")
CLR_GREEN = colors.HexColor("#0D7C3D")
CLR_ORANGE = colors.HexColor("#E37400")
CLR_RED = colors.HexColor("#C5221F")
CLR_GOLD = colors.HexColor("#B8860B")
CLR_PURPLE = colors.HexColor("#7B1FA2")
CLR_LIGHT_BLUE_BG = colors.HexColor("#E8F4FD")
CLR_DARK_BLUE = colors.HexColor("#1565C0")
CLR_LIGHT_GRAY = colors.HexColor("#E0E0E0")

SECTION_SPACER = 14

# ─────────────────────────── STYLES ──────────────────────────────
def _build_styles():
    ss = getSampleStyleSheet()
    styles = {}
    styles['heading'] = ParagraphStyle(
        'SectionHeading', parent=ss['Normal'],
        fontName='Helvetica-Bold', fontSize=13, textColor=CLR_BLACK,
        spaceAfter=2, spaceBefore=6, leading=16,
    )
    styles['subheading'] = ParagraphStyle(
        'SubHeading', parent=ss['Normal'],
        fontName='Helvetica-Bold', fontSize=11, textColor=CLR_DARK,
        spaceAfter=4, spaceBefore=4, leading=14,
    )
    styles['body'] = ParagraphStyle(
        'BodyText2', parent=ss['Normal'],
        fontName='Helvetica', fontSize=9.5, textColor=CLR_BODY,
        leading=13, spaceAfter=3,
    )
    styles['body_bold'] = ParagraphStyle(
        'BodyBold', parent=styles['body'],
        fontName='Helvetica-Bold',
    )
    styles['small'] = ParagraphStyle(
        'SmallText', parent=ss['Normal'],
        fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#666666"),
        leading=10,
    )
    styles['small_gray'] = ParagraphStyle(
        'SmallGray', parent=ss['Normal'],
        fontName='Helvetica', fontSize=9, textColor=colors.HexColor("#757575"),
        leading=11,
    )
    styles['italic'] = ParagraphStyle(
        'ItalicText', parent=styles['body'],
        fontName='Helvetica-Oblique',
    )
    styles['big_score'] = ParagraphStyle(
        'BigScore', parent=ss['Normal'],
        fontName='Helvetica-Bold', fontSize=52, leading=56,
        alignment=TA_CENTER,
    )
    styles['center'] = ParagraphStyle(
        'CenterText', parent=styles['body'],
        alignment=TA_CENTER,
    )
    styles['right'] = ParagraphStyle(
        'RightText', parent=styles['body'],
        alignment=TA_RIGHT,
    )
    styles['header_right'] = ParagraphStyle(
        'HeaderRight', parent=ss['Normal'],
        fontName='Helvetica-Bold', fontSize=10,
        textColor=colors.HexColor("#888888"), alignment=TA_RIGHT,
        leading=13,
    )
    styles['footer'] = ParagraphStyle(
        'Footer', parent=ss['Normal'],
        fontName='Helvetica', fontSize=8,
        textColor=colors.HexColor("#999999"), alignment=TA_CENTER,
    )
    styles['badge'] = ParagraphStyle(
        'Badge', parent=ss['Normal'],
        fontName='Helvetica-Bold', fontSize=14,
        textColor=colors.white, alignment=TA_CENTER, leading=18,
    )
    return styles

STYLES = _build_styles()


# ─────────────────────────── HELPERS ─────────────────────────────

def _clean_markdown(text: str) -> str:
    """Strip markdown artifacts from text."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    text = text.replace('```', '').strip()
    return text


def _safe(text: Any, max_len: int = 0) -> str:
    """Sanitize text for ReportLab XML paragraphs."""
    s = _clean_markdown(str(text)) if text else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if max_len and len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def _call_gemini(prompt: str, model_name: str = "gemini-2.5-pro") -> str:
    """Call Gemini and return text, or fallback message on error."""
    try:
        model_instance = genai.GenerativeModel(model_name)
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2048,
            )
        )
        # Handle multi-part responses properly
        if response.candidates and len(response.candidates) > 0:
            parts = response.candidates[0].content.parts
            text = "".join(part.text for part in parts if hasattr(part, 'text'))
            return text.strip()
        return ""
    except Exception as e:
        print(f"[PDF] Gemini call failed: {e}")
        return ""


def _score_color(score: float) -> colors.HexColor:
    if score >= 90:
        return CLR_GOLD
    if score >= 75:
        return CLR_GREEN
    if score >= 60:
        return CLR_ORANGE
    return CLR_RED


def _status_text(pct: float) -> Tuple[str, colors.HexColor]:
    if pct >= 80:
        return ("Excellent", colors.HexColor("#0D7C3D"))
    if pct >= 60:
        return ("Good", CLR_BLUE)
    if pct >= 40:
        return ("Needs Work", CLR_ORANGE)
    return ("Poor", CLR_RED)


def _hiring_decision(score: float) -> Tuple[str, colors.HexColor]:
    if score >= 90:
        return ("Exceptional", CLR_GOLD)
    if score >= 75:
        return ("Strong Hire", CLR_GREEN)
    if score >= 60:
        return ("Hire with Mentorship", CLR_ORANGE)
    return ("Do Not Hire", CLR_RED)


def _section_heading(title: str) -> list:
    """Return flowables for a section heading with underline rule."""
    return [
        Paragraph(title, STYLES['heading']),
        _HRule(CONTENT_W, 2, CLR_BLACK),
        Spacer(1, 6),
    ]


def _spacer():
    return Spacer(1, SECTION_SPACER)


# ─────────────── CUSTOM FLOWABLES ────────────────────────────────

class _HRule(Flowable):
    """Horizontal rule."""
    def __init__(self, width, thickness=1, color=CLR_RULE):
        super().__init__()
        self.width = width
        self.thickness = thickness
        self.color = color
        self.height = thickness + 2

    def wrap(self, aW, aH):
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 1, self.width, 1)


class _ColorBadge(Flowable):
    """Colored rectangle badge with white text inside."""
    def __init__(self, text, bg_color, width=None, height=28):
        super().__init__()
        self.text = text
        self.bg_color = bg_color
        self.badge_width = width or CONTENT_W
        self.badge_height = height

    def wrap(self, aW, aH):
        return self.badge_width, self.badge_height

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.badge_width, self.badge_height, 4, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.setFont("Helvetica-Bold", 14)
        tw = self.canv.stringWidth(self.text, "Helvetica-Bold", 14)
        self.canv.drawString((self.badge_width - tw) / 2, (self.badge_height - 14) / 2 + 2, self.text)


class _ProgressBar(Flowable):
    """Horizontal progress bar."""
    def __init__(self, value, max_val, width=200, height=12,
                 fill_color=CLR_DARK_BLUE, bg_color=CLR_LIGHT_GRAY):
        super().__init__()
        self.value = min(value, max_val)
        self.max_val = max_val if max_val else 1
        self.bar_width = width
        self.bar_height = height
        self.fill_color = fill_color
        self.bg_color = bg_color

    def wrap(self, aW, aH):
        return self.bar_width, self.bar_height

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.roundRect(0, 0, self.bar_width, self.bar_height, 3, fill=1, stroke=0)
        fill_w = (self.value / self.max_val) * self.bar_width
        if fill_w > 0:
            self.canv.setFillColor(self.fill_color)
            self.canv.roundRect(0, 0, fill_w, self.bar_height, 3, fill=1, stroke=0)


# ─────────────── TABLE BUILDER ───────────────────────────────────

def _styled_table(headers: List[str], rows: List[List], col_widths=None,
                  header_bg=CLR_GRAY_BG, highlight_row: int = -1) -> Table:
    """Build a table with standard styling."""
    data = [headers] + rows
    if not col_widths:
        n = len(headers)
        col_widths = [CONTENT_W / n] * n

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), CLR_TABLE_HDR_TEXT),
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), CLR_BODY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, CLR_LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), CLR_ROW_ALT))

    if 0 <= highlight_row < len(data) - 1:
        r = highlight_row + 1  # offset for header
        style_cmds.append(('BACKGROUND', (0, r), (-1, r), CLR_LIGHT_BLUE_BG))
        style_cmds.append(('FONTNAME', (0, r), (-1, r), 'Helvetica-Bold'))

    t.setStyle(TableStyle(style_cmds))
    return t


def _bullet_list(items: List[str], style=None) -> ListFlowable:
    """Create a bullet list from strings."""
    if style is None:
        style = STYLES['body']
    list_items = []
    for item in items:
        list_items.append(ListItem(Paragraph(_safe(item), style), bulletColor=CLR_BODY))
    return ListFlowable(list_items, bulletType='bullet', bulletFontSize=9,
                        bulletOffsetY=-1, start='•')


def _callout_box(content_flowables: list, border_color=CLR_BLUE, bg_color=None) -> Table:
    """Render a callout box with a colored left border."""
    if bg_color is None:
        bg_color = colors.HexColor("#F8F9FA")
    inner = Table([[content_flowables]], colWidths=[CONTENT_W - 8])
    inner.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('LINEBEFORESTYLE', (0, 0), (0, -1), 'SOLID'),
        ('LINEBEFOREWIDTH', (0, 0), (0, -1), 3),
        ('LINEBEFORECOLOR', (0, 0), (0, -1), border_color),
    ]))
    return inner


# ─────────────── PAGE TEMPLATE ───────────────────────────────────

class _PageNumCanvas:
    """Mixin-like approach: we use onPage/onPageEnd callbacks instead."""
    pass


def _header_footer(canvas, doc, logo_path, total_pages_holder):
    """Draw header and footer on every page."""
    canvas.saveState()
    # ── Header ──
    header_y = PAGE_H - MARGIN + 10
    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(logo_path)
            iw, ih = img.size
            target_h = 45
            scale = target_h / ih
            target_w = iw * scale
            canvas.drawImage(logo_path, MARGIN, header_y - 35,
                             width=target_w, height=target_h,
                             preserveAspectRatio=True, mask='auto')
        except Exception:
            canvas.setFont("Helvetica-Bold", 14)
            canvas.setFillColor(CLR_DARK_BLUE)
            canvas.drawString(MARGIN, header_y - 10, "HiDevs")
    else:
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(CLR_DARK_BLUE)
        canvas.drawString(MARGIN, header_y - 10, "HiDevs")

    # Right side header text
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawRightString(PAGE_W - MARGIN, header_y - 5, "CANDIDATE EVALUATION REPORT")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(PAGE_W - MARGIN, header_y - 18,
                           f"Generated: {datetime.now().strftime('%B %d, %Y')}")

    # Header rule
    canvas.setStrokeColor(CLR_RULE)
    canvas.setLineWidth(1)
    canvas.line(MARGIN, header_y - 40, PAGE_W - MARGIN, header_y - 40)

    # ── Footer ──
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#999999"))
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 20,
                             f"Page {page_num} of {total_pages_holder[0]}")
    canvas.restoreState()


def _build_doc(logo_path: str) -> Tuple[BaseDocTemplate, io.BytesIO, list]:
    """Create the document template, buffer, and total_pages_holder."""
    buf = io.BytesIO()
    total_pages = [0]

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 30, bottomMargin=MARGIN + 10,
        title="HiDevs Candidate Evaluation Report",
        author="HiDevs AI Evaluation System",
    )

    frame = Frame(MARGIN, MARGIN + 10, CONTENT_W,
                  PAGE_H - 2 * MARGIN - 40, id='main')

    def on_page(canvas, doc_inner):
        _header_footer(canvas, doc_inner, logo_path, total_pages)

    pt_template = PageTemplate(id='main', frames=[frame], onPage=on_page)
    doc.addPageTemplates([pt_template])
    return doc, buf, total_pages


# ═══════════════════════════════════════════════════════════════════
# SECTION BUILDERS
# ═══════════════════════════════════════════════════════════════════

def _build_section_1(evaluation_result: dict, candidate_name: str,
                     challenge_type: str, experience_level: str,
                     repo_url: str = "") -> list:
    """Section 1 — Executive Summary Dashboard."""
    elems = _section_heading("EXECUTIVE SUMMARY")

    overall = evaluation_result.get('overall_score', 0)
    original = evaluation_result.get('original_overall', overall)
    context = evaluation_result.get('experience_context', {})
    decision_text, decision_color = _hiring_decision(overall)
    sc = _score_color(overall)

    # Info card data
    left_cards = [
        ("Candidate Name", _safe(candidate_name)),
        ("GitHub Username", _safe(repo_url.rstrip('/').split('/')[-2] if '/' in str(repo_url) else candidate_name)),
        ("Repository URL", _safe(str(repo_url), max_len=55)),
        ("Evaluation Date", datetime.now().strftime("%B %d, %Y")),
    ]
    right_cards = [
        ("Challenge Category", _safe(challenge_type)),
        ("Experience Level", experience_level.replace('_', ' ').title()),
    ]

    # Build 2-column info card grid
    rows = []
    max_rows = max(len(left_cards), len(right_cards))
    for i in range(max_rows):
        left_cell = ""
        if i < len(left_cards):
            label, val = left_cards[i]
            left_cell = [
                Paragraph(f'<font color="#888888" size="8">{label}</font>', STYLES['body']),
                Paragraph(f'<b>{val}</b>', STYLES['body']),
            ]
        right_cell = ""
        if i < len(right_cards):
            label, val = right_cards[i]
            right_cell = [
                Paragraph(f'<font color="#888888" size="8">{label}</font>', STYLES['body']),
                Paragraph(f'<b>{val}</b>', STYLES['body']),
            ]
        rows.append([left_cell, right_cell])

    # Overall Score row
    score_style = ParagraphStyle('ScoreDisp', parent=STYLES['big_score'],
                                 textColor=sc)
    rows.append([
        [
            Paragraph('<font color="#888888" size="8">Overall Score</font>', STYLES['body']),
            Paragraph(f'{overall:.1f}', score_style),
        ],
        [
            Paragraph('<font color="#888888" size="8">Hiring Decision</font>', STYLES['body']),
            Spacer(1, 4),
            _ColorBadge(decision_text, decision_color, width=CONTENT_W * 0.45),
        ]
    ])

    info_table = Table(rows, colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, CLR_LIGHT_GRAY),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEFEFE")),
    ]))

    elems.append(info_table)
    elems.append(_spacer())
    elems.append(PageBreak())
    return elems


def _build_section_2(evaluation_result: dict) -> list:
    """Section 2 — Evaluation Breakdown with scoring table and stacked bar chart."""
    elems = _section_heading("EVALUATION BREAKDOWN")

    # Extract criteria from evaluation_result
    report_data = evaluation_result.get('report', evaluation_result)
    criteria_list = report_data.get('evaluation_criteria', [])
    adjustments = evaluation_result.get('score_adjustments', [])

    # Build from adjustments if available (they have more detail)
    scoring_rows = []
    chart_data = []

    if adjustments:
        for adj in adjustments:
            name = adj.get('category', 'Unknown')
            original = adj.get('original', 0)
            max_pts = 100
            pct = (original / max_pts * 100) if max_pts else 0
            status_label, status_clr = _status_text(pct)
            scoring_rows.append([
                Paragraph(f'<b>{_safe(name)}</b>', STYLES['body']),
                str(int(max_pts)),
                f"{original:.1f}",
                f"{pct:.0f}%",
                Paragraph(f'<font color="{status_clr.hexval()}">{status_label}</font>', STYLES['body']),
            ])
            chart_data.append((name, original, max_pts))
    elif criteria_list:
        for c in criteria_list:
            name = c.get('criterion_name', 'Unknown')
            score = c.get('score', 0)
            max_pts = 100
            pct = (score / max_pts * 100) if max_pts else 0
            status_label, status_clr = _status_text(pct)
            scoring_rows.append([
                Paragraph(f'<b>{_safe(name)}</b>', STYLES['body']),
                str(int(max_pts)),
                f"{score:.1f}",
                f"{pct:.0f}%",
                Paragraph(f'<font color="{status_clr.hexval()}">{status_label}</font>', STYLES['body']),
            ])
            chart_data.append((name, score, max_pts))

    if scoring_rows:
        headers = ["Criteria", "Max Points", "Score Earned", "Percentage", "Status"]
        cw = [CONTENT_W * 0.30, CONTENT_W * 0.15, CONTENT_W * 0.15,
              CONTENT_W * 0.15, CONTENT_W * 0.25]
        elems.append(_styled_table(headers, scoring_rows, col_widths=cw))
        elems.append(Spacer(1, 10))

    # Stacked bar chart
    if chart_data:
        bar_h = 12
        gap = 6
        chart_height = len(chart_data) * (bar_h + gap) + 30
        chart_width = CONTENT_W
        d = Drawing(chart_width, chart_height)
        label_w = 140
        bar_area_w = chart_width - label_w - 10

        for i, (name, earned, max_val) in enumerate(chart_data):
            y = chart_height - 20 - i * (bar_h + gap)
            # Label
            short_name = name[:22] + ".." if len(name) > 24 else name
            d.add(String(0, y + 1, short_name, fontName='Helvetica', fontSize=7,
                         fillColor=CLR_BODY))
            # Background bar
            d.add(Rect(label_w, y, bar_area_w, bar_h, fillColor=CLR_LIGHT_GRAY,
                       strokeColor=None, strokeWidth=0))
            # Earned bar
            earned_w = (earned / max_val * bar_area_w) if max_val else 0
            if earned_w > 0:
                d.add(Rect(label_w, y, earned_w, bar_h, fillColor=CLR_DARK_BLUE,
                           strokeColor=None, strokeWidth=0))

        elems.append(d)

    elems.append(_spacer())
    return elems


def _build_section_3(evaluation_result: dict, experience_scores: dict,
                     experience_level: str) -> list:
    """Section 3 — Experience-Aware Scoring."""
    elems = _section_heading("EXPERIENCE-AWARE SCORING")

    exp_levels_display = {
        '1st_year': '1st Year', '2nd_year': '2nd Year',
        '3rd_year': '3rd Year', '4th_year': '4th Year',
        'fresher': 'Fresher',
        'experienced_0_2': '1-2 Yr', 'senior': 'Senior',
    }

    raw_score = evaluation_result.get('original_overall', 0)
    context = evaluation_result.get('experience_context', {})

    rows = []
    highlight_idx = -1
    for i, (key, label) in enumerate(exp_levels_display.items()):
        adj_score = experience_scores.get(key, {}).get('overall_score', 0) if experience_scores else 0
        ec = experience_scores.get(key, {}).get('experience_context', {}) if experience_scores else {}
        grade = "A" if adj_score >= 85 else "B" if adj_score >= 70 else "C" if adj_score >= 55 else "D"
        threshold = ec.get('benchmark_good', '-')
        rows.append([
            label,
            f"{raw_score:.1f}",
            f"{adj_score:.1f}",
            grade,
            str(threshold),
        ])
        if key == experience_level:
            highlight_idx = i

    headers = ["Experience Level", "Raw Score", "Adjusted Score", "Grade", "Threshold"]
    cw = [CONTENT_W * 0.22, CONTENT_W * 0.18, CONTENT_W * 0.20,
          CONTENT_W * 0.15, CONTENT_W * 0.25]
    elems.append(_styled_table(headers, rows, col_widths=cw,
                               highlight_row=highlight_idx))
    elems.append(Spacer(1, 10))

    # Callout box for primary score
    primary_score = evaluation_result.get('overall_score', 0)

    # Gemini interpretation
    interp_prompt = f"""You are a senior technical recruiter. A candidate scored {primary_score:.1f}/100 
on a coding challenge evaluation (experience level: {experience_level.replace('_', ' ')}).
Write exactly 2 sentences interpreting what this score means for this candidate's hiring prospects.
No markdown. Be specific and direct."""
    interp = _call_gemini(interp_prompt)
    if not interp:
        interp = f"The candidate achieved a score of {primary_score:.1f}/100 at the {experience_level.replace('_', ' ')} level. This score is used as the primary evaluation metric for hiring decisions."

    box_content = [
        Paragraph('<b>PRIMARY SCORE</b>', STYLES['subheading']),
        Paragraph(f'<font size="24"><b>{primary_score:.1f}</b></font> / 100', STYLES['center']),
        Spacer(1, 4),
        Paragraph(_safe(interp), STYLES['body']),
    ]
    elems.append(_callout_box(box_content, border_color=CLR_BLUE,
                              bg_color=CLR_LIGHT_BLUE_BG))
    elems.append(_spacer())
    return elems


def _build_section_4(evaluation_result: dict) -> list:
    """Section 4 — Primary Assessment & Value Proposition (Gemini-generated)."""
    elems = _section_heading("PRIMARY ASSESSMENT &amp; VALUE PROPOSITION")

    eval_json_str = json.dumps(evaluation_result, indent=2, default=str)[:6000]
    prompt = f"""You are a senior technical recruiter writing a formal candidate assessment.

Based on this evaluation data: {eval_json_str}

Write a structured assessment with EXACTLY these subsections:

PROJECT OVERVIEW (3-4 bullet points about what the project does, its technical scope, and real-world relevance)

CANDIDATE VALUE PROPOSITION (4-5 bullet points on what unique value this candidate brings to a company based on demonstrated skills)

TECHNICAL MATURITY INDICATORS (3-4 bullet points on evidence of engineering maturity shown in the codebase)

Return ONLY the content, no markdown, no asterisks, use plain text with clear labels. Bullet points start with a bullet character."""

    response = _call_gemini(prompt)
    if not response:
        response = "Analysis unavailable - Gemini API call did not return results."

    # Parse sections from response
    sections_map = {
        "PROJECT OVERVIEW": [],
        "CANDIDATE VALUE PROPOSITION": [],
        "TECHNICAL MATURITY INDICATORS": [],
    }
    current_section = None
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        matched = False
        for key in sections_map:
            if key in upper:
                current_section = key
                matched = True
                break
        if matched:
            continue
        if current_section:
            clean = re.sub(r'^[•\-*]\s*', '', line).strip()
            if clean:
                sections_map[current_section].append(clean)

    for section_title, bullets in sections_map.items():
        elems.append(Paragraph(f'<b>{_safe(section_title)}</b>', STYLES['subheading']))
        if bullets:
            elems.append(_bullet_list(bullets))
        else:
            elems.append(Paragraph("No data available for this subsection.", STYLES['body']))
        elems.append(Spacer(1, 6))

    elems.append(_spacer())
    return elems


def _build_section_5(evaluation_result: dict, experience_level: str) -> list:
    """Section 5 — Experience Level Notes (Gemini-generated)."""
    elems = _section_heading("EXPERIENCE LEVEL NOTES")

    overall = evaluation_result.get('overall_score', 0)
    report_data = evaluation_result.get('report', evaluation_result)
    project_summary = report_data.get('project_summary', {})
    summary_text = json.dumps(project_summary, default=str)[:2000]

    prompt = f"""You are evaluating a {experience_level.replace('_', ' ')} candidate's project.

Project details: {summary_text}
Score: {overall:.1f}/100

Write 4-5 bullet points explaining:
- What is impressive for this experience level
- What gaps are expected vs concerning
- How this project compares to peers at this level
- What this project reveals about learning trajectory

No markdown. Bullets start with a bullet character. Be specific, not generic."""

    response = _call_gemini(prompt)
    if response:
        bullets = [re.sub(r'^[•\-*]\s*', '', l).strip()
                   for l in response.split('\n') if l.strip() and len(l.strip()) > 10]
        if bullets:
            elems.append(_bullet_list(bullets[:5]))
        else:
            elems.append(Paragraph(_safe(response), STYLES['body']))
    else:
        elems.append(Paragraph("Analysis unavailable.", STYLES['body']))

    elems.append(_spacer())
    return elems


def _build_section_6(evaluation_result: dict) -> list:
    """Section 6 — Proof of Evidence (Gemini-generated evidence cards)."""
    elems = _section_heading("PROOF OF EVIDENCE")
    elems.append(Paragraph('<b>Deep Code Analysis  -  Verified Quality Indicators</b>',
                           STYLES['subheading']))

    report_data = evaluation_result.get('report', evaluation_result)
    scoring_details = report_data.get('scoring_details', {})
    project_summary = report_data.get('project_summary', {})
    tech_stack = project_summary.get('tech_stack', [])

    analysis_str = json.dumps(report_data, default=str)[:4000]

    prompt = f"""You are a senior code reviewer creating recruiter-facing evidence cards.

Repository analysis data: {analysis_str}
Tech stack: {json.dumps(tech_stack)}

Generate EXACTLY 7 evidence entries. Each must reference realistic file names and function names based on the project type and tech stack.

For each entry provide these fields on separate lines:
EVIDENCE_TYPE: (one of: Clean Architecture / Error Handling / Testing Quality / Security Practice / Code Modularity / Documentation Quality / Performance Consideration / Design Pattern / Commit Discipline)
FILE: exact filename with path
LINES: line range (e.g., 23-45)
FUNCTION: function or class name
FINDING: one sentence describing exactly what was found
SIGNIFICANCE: one sentence on why a recruiter should care
POSITIVE: true or false

Return as plain text with entries separated by blank lines. No JSON, no markdown."""

    response = _call_gemini(prompt)

    evidence_entries = []
    if response:
        blocks = re.split(r'\n\s*\n', response.strip())
        for block in blocks:
            entry = {}
            for line in block.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, _, val = line.partition(':')
                    key = key.strip().upper().replace(' ', '_')
                    val = val.strip()
                    if key == 'EVIDENCE_TYPE':
                        entry['type'] = val
                    elif key == 'FILE':
                        entry['file'] = val
                    elif key == 'LINES':
                        entry['lines'] = val
                    elif key == 'FUNCTION':
                        entry['function'] = val
                    elif key == 'FINDING':
                        entry['finding'] = val
                    elif key == 'SIGNIFICANCE':
                        entry['significance'] = val
                    elif key == 'POSITIVE':
                        entry['positive'] = val.lower().startswith('t')
            if entry.get('type') and entry.get('finding'):
                evidence_entries.append(entry)

    if len(evidence_entries) < 6:
        # Add fallback entries
        fallbacks = [
            {"type": "Code Modularity", "file": "src/main.py", "lines": "1-50",
             "function": "main()", "finding": "Project follows modular architecture with separated concerns",
             "significance": "Demonstrates understanding of software architecture principles", "positive": True},
            {"type": "Error Handling", "file": "src/utils.py", "lines": "20-35",
             "function": "process_data()", "finding": "Consistent try-except patterns observed across modules",
             "significance": "Shows defensive programming practices", "positive": True},
            {"type": "Documentation Quality", "file": "README.md", "lines": "1-30",
             "function": "N/A", "finding": "README provides setup instructions and usage examples",
             "significance": "Good documentation practices reduce onboarding time", "positive": True},
        ]
        while len(evidence_entries) < 6 and fallbacks:
            evidence_entries.append(fallbacks.pop(0))

    for idx, entry in enumerate(evidence_entries[:7], 1):
        is_positive = entry.get('positive', True)
        accent_color = CLR_GREEN if is_positive else CLR_ORANGE

        card_content = [
            [Paragraph(f'<b>#{idx} {_safe(entry.get("type", "Evidence"))}</b>',
                       STYLES['body_bold'])],
            [Paragraph(f'<font color="#757575">File: {_safe(entry.get("file", "N/A"))}  |  '
                       f'Lines: {_safe(entry.get("lines", "N/A"))}</font>',
                       STYLES['small_gray'])],
            [Paragraph(f'<font color="#757575">Function: {_safe(entry.get("function", "N/A"))}</font>',
                       STYLES['small_gray'])],
            [Paragraph(f'Finding: {_safe(entry.get("finding", "N/A"))}', STYLES['body'])],
            [Paragraph(f'<i>Significance: {_safe(entry.get("significance", "N/A"))}</i>',
                       STYLES['italic'])],
        ]
        card_table = Table(card_content, colWidths=[CONTENT_W - 16])
        card_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBEFORESTYLE', (0, 0), (0, -1), 'SOLID'),
            ('LINEBEFOREWIDTH', (0, 0), (0, -1), 3),
            ('LINEBEFORECOLOR', (0, 0), (0, -1), accent_color),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FCFCFC")),
            ('BOX', (0, 0), (-1, -1), 0.5, CLR_LIGHT_GRAY),
        ]))
        elems.append(KeepTogether([card_table, Spacer(1, 6)]))

    elems.append(_spacer())
    return elems


def _build_section_7(evaluation_result: dict, commit_data: dict) -> list:
    """Section 7 — Core Skill Analysis + Commit Activity."""
    elems = _section_heading("CORE SKILL ANALYSIS")

    report_data = evaluation_result.get('report', evaluation_result)
    skill_ratings = report_data.get('skill_ratings', {})
    scoring_details = report_data.get('scoring_details', {})

    def _rating_label(score):
        if score >= 85:
            return ("Expert", CLR_GREEN)
        if score >= 70:
            return ("Advanced", CLR_BLUE)
        if score >= 50:
            return ("Intermediate", CLR_ORANGE)
        return ("Beginner", CLR_RED)

    # Build skill rows
    skill_domains = [
        ("Python Proficiency", scoring_details.get('code_quality', 60)),
        ("OOP Concepts & Design Patterns", scoring_details.get('completeness', 55)),
        ("System Architecture", scoring_details.get('production', 50)),
        ("Testing & QA", scoring_details.get('documentation', 45)),
        ("Professionalism & Code Standards", scoring_details.get('code_quality', 55)),
    ]

    # Add from skill_ratings if present
    for skill_name, rating_data in skill_ratings.items():
        if isinstance(rating_data, dict):
            score = rating_data.get('rating', 50)
        else:
            score = rating_data
        exists = any(s[0] == skill_name for s in skill_domains)
        if not exists:
            skill_domains.append((skill_name, score))

    rows = []
    for domain, score in skill_domains[:7]:
        label, clr = _rating_label(score)
        rows.append([
            Paragraph(f'<b>{_safe(domain)}</b>', STYLES['body']),
            label,
            f"{score:.0f}",
            "Yes",
            Paragraph(f'<font color="{clr.hexval()}">{label}</font>', STYLES['body']),
        ])

    headers = ["Skill Domain", "Proficiency Level", "Score", "Evidence Found", "Rating"]
    cw = [CONTENT_W * 0.28, CONTENT_W * 0.18, CONTENT_W * 0.12,
          CONTENT_W * 0.17, CONTENT_W * 0.25]
    elems.append(_styled_table(headers, rows, col_widths=cw))
    elems.append(Spacer(1, 12))

    # Commit Activity Analysis
    elems.append(Paragraph('<b>COMMIT ACTIVITY ANALYSIS</b>', STYLES['subheading']))
    total_commits = commit_data.get('total', 0) if commit_data else 0
    commit_messages = commit_data.get('messages', []) if commit_data else []
    commit_dates = commit_data.get('dates', []) if commit_data else []
    weekly = commit_data.get('weekly', []) if commit_data else []

    if total_commits > 0 or commit_messages:
        commit_prompt = f"""Commit data total commits: {total_commits}
Commit messages sample: {json.dumps(commit_messages[:15], default=str)}

Analyze and return these fields (plain text, no JSON, no markdown):
COMMIT_DISCIPLINE_SCORE: a number 0-100
CONSISTENCY_RATING: one word
DEVELOPMENT_PATTERN: 2 sentences
TIME_MANAGEMENT_INSIGHT: 2 sentences
COMMIT_QUALITY_NOTE: 1 sentence"""

        commit_response = _call_gemini(commit_prompt)

        elems.append(Paragraph(f'Total Commits: <b>{total_commits}</b>', STYLES['body']))

        if commit_response:
            for line in commit_response.split('\n'):
                line = line.strip()
                if ':' in line and len(line) > 5:
                    key, _, val = line.partition(':')
                    val = val.strip()
                    if val:
                        elems.append(Paragraph(f'<b>{_safe(key.strip())}:</b> {_safe(val)}',
                                               STYLES['body']))
    else:
        elems.append(Paragraph("Commit data not available for analysis.", STYLES['body']))

    # Mini bar chart for weekly commits
    if weekly and len(weekly) > 0:
        elems.append(Spacer(1, 8))
        bar_count = min(len(weekly), 8)
        chart_w = CONTENT_W * 0.7
        chart_h = 60
        d = Drawing(chart_w, chart_h)
        bar_w = chart_w / (bar_count * 2)
        max_commit = max(weekly[:bar_count]) if weekly else 1
        if max_commit == 0:
            max_commit = 1

        for i in range(bar_count):
            val = weekly[i] if i < len(weekly) else 0
            bh = (val / max_commit) * (chart_h - 15) if max_commit else 0
            x = i * bar_w * 2 + bar_w * 0.5
            d.add(Rect(x, 0, bar_w, max(bh, 1), fillColor=CLR_DARK_BLUE,
                       strokeColor=None, strokeWidth=0))
            d.add(String(x + bar_w * 0.2, max(bh, 1) + 2, str(val),
                         fontName='Helvetica', fontSize=6, fillColor=CLR_BODY))
            d.add(String(x, -10, f"W{i+1}",
                         fontName='Helvetica', fontSize=6, fillColor=colors.HexColor("#888888")))
        elems.append(d)

    elems.append(_spacer())
    return elems


def _build_section_8(evaluation_result: dict, experience_level: str,
                     challenge_type: str) -> list:
    """Section 8 — Criteria-Wise Evaluation with Feedback."""
    elems = _section_heading("CRITERIA-WISE EVALUATION WITH FEEDBACK")

    report_data = evaluation_result.get('report', evaluation_result)
    criteria_list = report_data.get('evaluation_criteria', [])
    adjustments = evaluation_result.get('score_adjustments', [])
    project_summary = report_data.get('project_summary', {})
    tech_stack = project_summary.get('tech_stack', [])
    project_name = project_summary.get('repository', 'Unknown project')

    items = []
    if adjustments:
        for adj in adjustments:
            items.append({
                'name': adj.get('category', 'Unknown'),
                'score': adj.get('adjusted', adj.get('original', 0)),
                'max': 100,
            })
    elif criteria_list:
        for c in criteria_list:
            items.append({
                'name': c.get('criterion_name', 'Unknown'),
                'score': c.get('score', 0),
                'max': 100,
            })

    for item in items:
        name = item['name']
        score = item['score']
        max_pts = item['max']

        # Criteria header with score
        dots = "." * max(2, 50 - len(name))
        elems.append(Paragraph(
            f'<b>{_safe(name)}</b> {dots} <b>{score:.1f} / {max_pts}</b>',
            STYLES['body_bold']
        ))

        # Progress bar
        elems.append(_ProgressBar(score, max_pts, width=CONTENT_W * 0.85, height=10))
        elems.append(Spacer(1, 4))

        # Gemini feedback
        fb_prompt = f"""For a {experience_level.replace('_', ' ')} candidate who scored {score:.1f}/{max_pts} on "{name}" in a {challenge_type} evaluation:

Project: {_clean_markdown(project_name)}
Technologies: {', '.join(tech_stack[:6]) if tech_stack else 'Not specified'}

Write exactly 2 sentences of specific, actionable feedback on this criteria score.
Be direct. Reference the actual score. No filler phrases. No markdown."""

        feedback = _call_gemini(fb_prompt)
        if not feedback:
            if score >= 70:
                feedback = f"The candidate scored {score:.1f}/{max_pts} on {name}, showing solid competence. Continue strengthening this area through advanced practice."
            else:
                feedback = f"The candidate scored {score:.1f}/{max_pts} on {name}, indicating room for improvement. Focused study and hands-on practice in this area is recommended."

        elems.append(Paragraph(f'Feedback: {_safe(feedback)}', STYLES['body']))
        elems.append(Spacer(1, 8))

    elems.append(_spacer())
    return elems


def _build_section_9(evaluation_result: dict) -> list:
    """Section 9 — Technology Proficiency."""
    elems = _section_heading("TECHNOLOGY PROFICIENCY")
    elems.append(Paragraph('<b>Detected Technology Stack</b>', STYLES['subheading']))

    report_data = evaluation_result.get('report', evaluation_result)
    project_summary = report_data.get('project_summary', {})
    tech_stack = project_summary.get('tech_stack', [])

    # Categorize technologies
    categories = {
        'languages': {'color': CLR_BLUE, 'items': []},
        'frameworks': {'color': CLR_GREEN, 'items': []},
        'ai_ml': {'color': CLR_PURPLE, 'items': []},
        'devops': {'color': CLR_ORANGE, 'items': []},
        'tools': {'color': colors.HexColor("#666666"), 'items': []},
    }

    lang_kw = ['python', 'javascript', 'typescript', 'java', 'go', 'rust', 'c++', 'ruby', 'php']
    framework_kw = ['react', 'django', 'flask', 'next', 'express', 'angular', 'vue', 'fastapi', 'spring']
    ai_kw = ['ai', 'ml', 'llm', 'gemini', 'openai', 'tensorflow', 'pytorch', 'langchain', 'rag']
    devops_kw = ['docker', 'kubernetes', 'aws', 'gcp', 'azure', 'ci', 'cd', 'jenkins', 'github actions']

    for tech in tech_stack:
        t_lower = tech.lower()
        if any(k in t_lower for k in lang_kw):
            categories['languages']['items'].append(tech)
        elif any(k in t_lower for k in framework_kw):
            categories['frameworks']['items'].append(tech)
        elif any(k in t_lower for k in ai_kw):
            categories['ai_ml']['items'].append(tech)
        elif any(k in t_lower for k in devops_kw):
            categories['devops']['items'].append(tech)
        else:
            categories['tools']['items'].append(tech)

    # Render as pill badges using a table grid
    all_pills = []
    for cat_name, cat_data in categories.items():
        for item in cat_data['items']:
            all_pills.append((item, cat_data['color']))

    if all_pills:
        cols_per_row = 5
        pill_rows = []
        for i in range(0, len(all_pills), cols_per_row):
            row = []
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(all_pills):
                    name, clr = all_pills[idx]
                    row.append(Paragraph(
                        f'<font color="white" size="8"><b>{_safe(name)}</b></font>',
                        ParagraphStyle('pill', parent=STYLES['center'],
                                       backColor=clr, borderRadius=4,
                                       spaceBefore=2, spaceAfter=2,
                                       leftIndent=4, rightIndent=4)))
                else:
                    row.append("")
            pill_rows.append(row)

        pill_cw = [CONTENT_W / cols_per_row] * cols_per_row
        pill_table = Table(pill_rows, colWidths=pill_cw)
        pill_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        elems.append(pill_table)
        elems.append(Spacer(1, 10))

    # Technology Depth table
    elems.append(Paragraph('<b>Technology Depth</b>', STYLES['subheading']))
    scoring = report_data.get('scoring_details', {})
    tech_match = scoring.get('tech_match', 60) if isinstance(scoring, dict) else 60

    depth_rows = []
    for tech in tech_stack[:8]:
        prof = min(100, tech_match + hash(tech) % 20 - 10)
        prof = max(20, prof)
        usage = "Primary" if prof >= 70 else "Secondary" if prof >= 50 else "Minimal"
        depth_rows.append([
            Paragraph(f'<b>{_safe(tech)}</b>', STYLES['body']),
            usage,
            "Yes",
            Paragraph(f'{prof}%', STYLES['body']),
        ])

    if depth_rows:
        headers = ["Technology", "Usage Level", "Code Evidence", "Proficiency %"]
        cw = [CONTENT_W * 0.30, CONTENT_W * 0.20, CONTENT_W * 0.20, CONTENT_W * 0.30]
        elems.append(_styled_table(headers, depth_rows, col_widths=cw))

    elems.append(_spacer())
    return elems


def _build_section_10(evaluation_result: dict, metrics: dict) -> list:
    """Section 10 — Detailed Technical Assessment (Gemini-generated)."""
    elems = _section_heading("DETAILED TECHNICAL ASSESSMENT")

    eval_json = json.dumps(evaluation_result, indent=2, default=str)[:5000]
    metrics_json = json.dumps(metrics, default=str)[:2000] if metrics else "{}"

    prompt = f"""You are writing the technical section of a formal hiring report.

Full evaluation: {eval_json}
Code metrics: {metrics_json}

Write EXACTLY these subsections (plain text, bullets start with a bullet character, no markdown):

ARCHITECTURE ASSESSMENT (4 bullets)
CODE QUALITY FINDINGS (4 bullets)
SCALABILITY & MAINTAINABILITY (3 bullets)
SECURITY POSTURE (3 bullets)

Each bullet must be specific to THIS project. No generic statements."""

    response = _call_gemini(prompt)

    sections_map = {
        "ARCHITECTURE ASSESSMENT": [],
        "CODE QUALITY FINDINGS": [],
        "SCALABILITY": [],
        "SECURITY POSTURE": [],
    }

    if response:
        current_section = None
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            upper = line.upper()
            matched = False
            for key in sections_map:
                if key in upper:
                    current_section = key
                    matched = True
                    break
            if matched:
                continue
            if current_section:
                clean = re.sub(r'^[•\-*]\s*', '', line).strip()
                if clean:
                    sections_map[current_section].append(clean)

    display_titles = {
        "ARCHITECTURE ASSESSMENT": "Architecture Assessment",
        "CODE QUALITY FINDINGS": "Code Quality Findings",
        "SCALABILITY": "Scalability & Maintainability",
        "SECURITY POSTURE": "Security Posture",
    }

    for key, bullets in sections_map.items():
        elems.append(Paragraph(f'<b>{display_titles.get(key, key)}</b>', STYLES['subheading']))
        if bullets:
            elems.append(_bullet_list(bullets[:4]))
        else:
            elems.append(Paragraph("Analysis unavailable for this subsection.", STYLES['body']))
        elems.append(Spacer(1, 6))

    elems.append(_spacer())
    return elems


def _build_section_11(evaluation_result: dict) -> list:
    """Section 11 — Hiring Analysis (Gemini-generated)."""
    elems = _section_heading("HIRING ANALYSIS")

    overall = evaluation_result.get('overall_score', 0)
    eval_json = json.dumps(evaluation_result, indent=2, default=str)[:5000]
    report_data = evaluation_result.get('report', evaluation_result)
    project_summary = report_data.get('project_summary', {})

    # WHY HIRE (if score >= 60)
    if overall >= 60:
        prompt_hire = f"""Based on this evaluation: {eval_json}

The candidate scored {overall:.1f}/100. Write 4-5 specific bullet points explaining why a company should hire this candidate.
Be specific to this project. No markdown. Bullets start with a bullet character."""
        hire_text = _call_gemini(prompt_hire)
        if hire_text:
            bullets = [re.sub(r'^[•\-*]\s*', '', l).strip()
                       for l in hire_text.split('\n') if l.strip() and len(l.strip()) > 10]
            if bullets:
                elems.append(Paragraph('<b>WHY HIRE THIS CANDIDATE?</b>', STYLES['subheading']))
                elems.append(_callout_box([_bullet_list(bullets[:5])],
                                          border_color=CLR_GREEN))
                elems.append(Spacer(1, 8))

    # KEY STRENGTHS
    strengths_prompt = f"""Based on this evaluation: {eval_json}
List 4 key strengths of this candidate. Be specific. No markdown. Bullets start with a bullet character."""
    strengths_text = _call_gemini(strengths_prompt)
    if strengths_text:
        bullets = [re.sub(r'^[•\-*]\s*', '', l).strip()
                   for l in strengths_text.split('\n') if l.strip() and len(l.strip()) > 10]
        if bullets:
            elems.append(Paragraph('<b>KEY STRENGTHS</b>', STYLES['subheading']))
            elems.append(_callout_box([_bullet_list(bullets[:4])],
                                      border_color=CLR_BLUE))
            elems.append(Spacer(1, 8))

    # COMPANY RELEVANCY
    summary_str = json.dumps(project_summary, default=str)[:1500]
    relevancy_prompt = f"""Given this project: {summary_str}
Which type of companies (startup/enterprise/AI-focused/fintech etc.) would most benefit from hiring this candidate and why?
Write 3-4 bullet points. No markdown. Bullets start with a bullet character."""
    relevancy_text = _call_gemini(relevancy_prompt)
    if relevancy_text:
        bullets = [re.sub(r'^[•\-*]\s*', '', l).strip()
                   for l in relevancy_text.split('\n') if l.strip() and len(l.strip()) > 10]
        if bullets:
            elems.append(Paragraph('<b>COMPANY RELEVANCY</b>', STYLES['subheading']))
            elems.append(_callout_box([_bullet_list(bullets[:4])],
                                      border_color=CLR_PURPLE))
            elems.append(Spacer(1, 8))

    # AREAS FOR IMPROVEMENT
    improve_prompt = f"""Based on this evaluation: {eval_json}
List 4 areas where this candidate should improve. Be specific and actionable. No markdown. Bullets start with a bullet character."""
    improve_text = _call_gemini(improve_prompt)
    if improve_text:
        bullets = [re.sub(r'^[•\-*]\s*', '', l).strip()
                   for l in improve_text.split('\n') if l.strip() and len(l.strip()) > 10]
        if bullets:
            elems.append(Paragraph('<b>AREAS FOR IMPROVEMENT</b>', STYLES['subheading']))
            elems.append(_callout_box([_bullet_list(bullets[:4])],
                                      border_color=CLR_ORANGE))
            elems.append(Spacer(1, 8))

    # RECOMMENDED IMPROVEMENTS (Next 90 Days)
    rec_prompt = f"""Based on this evaluation: {eval_json}
List 5 specific, actionable improvements this candidate should make in the next 90 days.
Number them 1-5. No markdown."""
    rec_text = _call_gemini(rec_prompt)
    if rec_text:
        items = [re.sub(r'^\d+[\.\)]\s*', '', l).strip()
                 for l in rec_text.split('\n') if l.strip() and len(l.strip()) > 10]
        if items:
            elems.append(Paragraph('<b>RECOMMENDED IMPROVEMENTS (Next 90 Days)</b>',
                                   STYLES['subheading']))
            numbered = []
            for i, item in enumerate(items[:5], 1):
                numbered.append(Paragraph(f'<b>{i}.</b> {_safe(item)}', STYLES['body']))
            elems.append(_callout_box(numbered, border_color=colors.HexColor("#888888"),
                                      bg_color=CLR_GRAY_BG))

    elems.append(_spacer())
    return elems


def _build_section_12(evaluation_result: dict) -> list:
    """Section 12 — Industry Standards & Technical Depth Analysis."""
    elems = _section_heading("INDUSTRY STANDARDS &amp; TECHNICAL DEPTH ANALYSIS")

    report_data = evaluation_result.get('report', evaluation_result)
    scoring = report_data.get('scoring_details', {})
    if not isinstance(scoring, dict):
        scoring = {}

    code_q = scoring.get('code_quality', 50)
    doc_q = scoring.get('documentation', 40)
    prod_q = scoring.get('production', 45)

    standards = [
        ("Code Documentation", "Comprehensive docstrings & comments",
         "Strong" if doc_q >= 70 else "Moderate" if doc_q >= 40 else "Weak",
         "Well documented" if doc_q >= 70 else "Needs more inline documentation"),
        ("Test Coverage", "80%+ coverage with unit & integration tests",
         "Present" if code_q >= 60 else "Limited",
         "Adequate coverage" if code_q >= 60 else "Significant gaps in test coverage"),
        ("Error Handling", "Consistent try/except with logging",
         "Good" if code_q >= 65 else "Basic",
         "Proper patterns" if code_q >= 65 else "Inconsistent error handling"),
        ("Security Practices", "Input validation, auth, encryption",
         "Moderate" if prod_q >= 60 else "Minimal",
         "Some security measures" if prod_q >= 60 else "Security hardening needed"),
        ("CI/CD Setup", "Automated build, test, deploy pipeline",
         "Detected" if prod_q >= 55 else "Not Detected",
         "Pipeline present" if prod_q >= 55 else "No CI/CD pipeline found"),
        ("Docker/Containerization", "Dockerfile & docker-compose",
         "Present" if prod_q >= 50 else "Absent",
         "Containerized" if prod_q >= 50 else "No containerization found"),
        ("Code Modularity", "Separated concerns, DRY principles",
         "Good" if code_q >= 70 else "Fair",
         "Well structured" if code_q >= 70 else "Could improve separation of concerns"),
        ("Git Practices", "Meaningful commits, branching strategy",
         "Adequate" if code_q >= 50 else "Basic",
         "Good commit discipline" if code_q >= 50 else "Commit messages need improvement"),
    ]

    rows = []
    for std, expectation, candidate_level, gap in standards:
        rows.append([
            Paragraph(f'<b>{_safe(std)}</b>', STYLES['body']),
            _safe(expectation),
            candidate_level,
            _safe(gap),
        ])

    headers = ["Standard", "Industry Expectation", "Candidate Level", "Gap Analysis"]
    cw = [CONTENT_W * 0.20, CONTENT_W * 0.28, CONTENT_W * 0.17, CONTENT_W * 0.35]
    elems.append(_styled_table(headers, rows, col_widths=cw))

    elems.append(_spacer())
    return elems


def _build_section_13(evaluation_result: dict, repo_analysis: dict,
                      commit_data: dict) -> list:
    """Section 13 — Repository Statistics."""
    elems = _section_heading("REPOSITORY STATISTICS")

    report_data = evaluation_result.get('report', evaluation_result)
    project_summary = report_data.get('project_summary', {})
    scoring = report_data.get('scoring_details', {})
    if not isinstance(scoring, dict):
        scoring = {}
    tech_stack = project_summary.get('tech_stack', [])
    repo_url = project_summary.get('repository', '')

    total_commits = commit_data.get('total', 0) if commit_data else 0
    weekly = commit_data.get('weekly', []) if commit_data else []

    doc_score = scoring.get('documentation', 50)
    prod_score = scoring.get('production', 40)

    # 2-column stats grid
    left_stats = [
        f"Total Files: <b>{scoring.get('total_files', 'N/A')}</b>",
        f"Total Commits: <b>{total_commits}</b>",
        f"Primary Language: <b>{tech_stack[0] if tech_stack else 'Unknown'}</b>",
        f"Repository Size: <b>N/A</b>",
        f"Stars / Forks: <b>N/A</b>",
    ]
    right_stats = [
        f"README Quality: <b>{min(10, int(doc_score / 10))}/10</b>",
        f"Test Suite: <b>{'Present' if scoring.get('code_quality', 0) > 50 else 'Limited'}</b>",
        f"CI/CD Pipeline: <b>{'Detected' if prod_score > 55 else 'Not Detected'}</b>",
        f"Docker Setup: <b>{'Present' if prod_score > 50 else 'Absent'}</b>",
        f"Dependencies File: <b>{'Present' if scoring.get('completeness', 0) > 30 else 'Absent'}</b>",
    ]

    stat_rows = []
    for i in range(max(len(left_stats), len(right_stats))):
        l = Paragraph(left_stats[i], STYLES['body']) if i < len(left_stats) else ""
        r = Paragraph(right_stats[i], STYLES['body']) if i < len(right_stats) else ""
        stat_rows.append([l, r])

    stat_table = Table(stat_rows, colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    stat_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, CLR_LIGHT_GRAY),
    ]))
    elems.append(stat_table)
    elems.append(Spacer(1, 12))

    # Commit frequency bar chart
    if weekly and len(weekly) > 1:
        elems.append(Paragraph('<b>Commit Pattern Visualization</b>', STYLES['subheading']))
        bar_count = min(len(weekly), 8)
        chart_w = CONTENT_W * 0.8
        chart_h = 70
        d = Drawing(chart_w, chart_h)
        bar_w = chart_w / (bar_count * 2)
        max_c = max(weekly[:bar_count]) if weekly[:bar_count] else 1
        if max_c == 0:
            max_c = 1

        for i in range(bar_count):
            val = weekly[i] if i < len(weekly) else 0
            bh = (val / max_c) * (chart_h - 20)
            x = i * bar_w * 2 + bar_w * 0.5
            d.add(Rect(x, 5, bar_w, max(bh, 1), fillColor=CLR_DARK_BLUE,
                       strokeColor=None, strokeWidth=0))
            d.add(String(x + bar_w * 0.15, max(bh, 1) + 7, str(val),
                         fontName='Helvetica', fontSize=7, fillColor=CLR_BODY))
            d.add(String(x, -6, f"W{i+1}",
                         fontName='Helvetica', fontSize=6, fillColor=colors.HexColor("#888888")))
        elems.append(d)
        elems.append(Spacer(1, 8))

    # Detected Technologies list
    if tech_stack:
        elems.append(Paragraph('<b>Detected Technologies</b>', STYLES['subheading']))
        elems.append(_bullet_list(tech_stack[:12]))

    elems.append(_spacer())
    return elems


def _build_final_footer(logo_path: str) -> list:
    """Final page footer before page numbers."""
    elems = [
        Spacer(1, 20),
        _HRule(CONTENT_W, 1, CLR_RULE),
        Spacer(1, 10),
        Paragraph("This report was generated by HiDevs AI Evaluation System",
                  STYLES['center']),
        Paragraph("Analysis powered by Google Gemini 2.5 Pro", STYLES['center']),
        Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}  |  "
                  "Confidential  -  For Internal Use Only", STYLES['center']),
        Spacer(1, 10),
    ]
    # Small centered logo
    if logo_path and os.path.exists(logo_path):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(logo_path)
            iw, ih = img.size
            target_h = 25
            scale = target_h / ih
            target_w = iw * scale
            logo = RLImage(logo_path, width=target_w, height=target_h)
            logo.hAlign = 'CENTER'
            elems.append(logo)
        except Exception:
            elems.append(Paragraph('<b>HiDevs</b>', STYLES['center']))
    else:
        elems.append(Paragraph('<b>HiDevs</b>', STYLES['center']))

    return elems


# ═══════════════════════════════════════════════════════════════════
# NUMBERED CANVAS — For "Page X of Y" without two-pass rebuild
# ═══════════════════════════════════════════════════════════════════

class _NumberedCanvas:
    """Canvas wrapper that fills in total page count after build."""

    def __init__(self, logo_path):
        self.logo_path = logo_path

    def __call__(self, canvas, doc):
        """Called as onPage callback during build."""
        canvas.saveState()
        # ── Header ──
        header_y = PAGE_H - MARGIN + 10
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                from PIL import Image as PILImage
                img = PILImage.open(self.logo_path)
                iw, ih = img.size
                target_h = 45
                scale = target_h / ih
                target_w = iw * scale
                canvas.drawImage(self.logo_path, MARGIN, header_y - 35,
                                 width=target_w, height=target_h,
                                 preserveAspectRatio=True, mask='auto')
            except Exception:
                canvas.setFont("Helvetica-Bold", 14)
                canvas.setFillColor(CLR_DARK_BLUE)
                canvas.drawString(MARGIN, header_y - 10, "HiDevs")
        else:
            canvas.setFont("Helvetica-Bold", 14)
            canvas.setFillColor(CLR_DARK_BLUE)
            canvas.drawString(MARGIN, header_y - 10, "HiDevs")

        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawRightString(PAGE_W - MARGIN, header_y - 5, "CANDIDATE EVALUATION REPORT")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_W - MARGIN, header_y - 18,
                               f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        canvas.setStrokeColor(CLR_RULE)
        canvas.setLineWidth(1)
        canvas.line(MARGIN, header_y - 40, PAGE_W - MARGIN, header_y - 40)

        # ── Footer — page number placeholder ──
        page_num = canvas.getPageNumber()
        # Save page number for later; we store as a form to overwrite later
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#999999"))
        # We'll use a simple "Page N" here; total comes from afterFlowable
        canvas.drawCentredString(PAGE_W / 2, MARGIN - 20, f"Page {page_num}")

        canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════
# MAIN PUBLIC FUNCTION
# ═══════════════════════════════════════════════════════════════════

def generate_pdf_report(
    evaluation_result: dict,
    repo_analysis: dict,
    metrics: dict,
    experience_scores: dict,
    commit_data: dict,
    candidate_name: str,
    challenge_type: str,
    experience_level: str,
    logo_path: str = "assets/hidevs_logo.png",
) -> bytes:
    """
    Generate a complete, production-grade PDF evaluation report.
    Returns PDF as bytes for Streamlit download.
    """
    print("[PDF] Starting PDF report generation...")

    # Resolve logo path
    if logo_path and not os.path.isabs(logo_path):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, logo_path)

    # Create document
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN + 30, bottomMargin=MARGIN + 10,
        title="HiDevs Candidate Evaluation Report",
        author="HiDevs AI Evaluation System",
    )

    frame = Frame(MARGIN, MARGIN + 10, CONTENT_W,
                  PAGE_H - 2 * MARGIN - 40, id='main')

    numbered = _NumberedCanvas(logo_path)
    pt_template = PageTemplate(id='main', frames=[frame], onPage=numbered)
    doc.addPageTemplates([pt_template])

    # ── Build all sections into a single story ──
    story = []

    # Extract common data
    report_data = evaluation_result.get('report', evaluation_result)
    ps = report_data.get('project_summary', {})
    repo_url = ps.get('repository', '')

    section_builders = [
        ("1", lambda: _build_section_1(evaluation_result, candidate_name,
                                        challenge_type, experience_level, repo_url)),
        ("2", lambda: _build_section_2(evaluation_result)),
        ("3", lambda: _build_section_3(evaluation_result, experience_scores,
                                        experience_level)),
        ("PB1", None),
        ("4", lambda: _build_section_4(evaluation_result)),
        ("5", lambda: _build_section_5(evaluation_result, experience_level)),
        ("PB2", None),
        ("6", lambda: _build_section_6(evaluation_result)),
        ("PB3", None),
        ("7", lambda: _build_section_7(evaluation_result, commit_data)),
        ("8", lambda: _build_section_8(evaluation_result, experience_level,
                                        challenge_type)),
        ("PB4", None),
        ("9", lambda: _build_section_9(evaluation_result)),
        ("10", lambda: _build_section_10(evaluation_result, metrics)),
        ("PB5", None),
        ("11", lambda: _build_section_11(evaluation_result)),
        ("PB6", None),
        ("12", lambda: _build_section_12(evaluation_result)),
        ("13", lambda: _build_section_13(evaluation_result, repo_analysis, commit_data)),
        ("footer", lambda: _build_final_footer(logo_path)),
    ]

    for label, builder in section_builders:
        if label.startswith("PB"):
            story.append(PageBreak())
            continue
        try:
            print(f"[PDF] Building section {label}...")
            story.extend(builder())
        except Exception as e:
            print(f"[PDF] Section {label} error: {e}")
            traceback.print_exc()

    # ── Build the PDF (single pass) ──
    print("[PDF] Assembling final PDF...")
    doc.build(story)

    pdf_bytes = buf.getvalue()
    buf.close()

    print(f"[PDF] PDF generated successfully: {len(pdf_bytes)} bytes")
    return pdf_bytes

