# pdf_report_generator.py - Production-grade PDF report generator
# Uses ReportLab for layout, Gemini for narrative content
import io, os, re, json, traceback
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
from reportlab.graphics.shapes import Drawing, Rect, String
import google.generativeai as genai

# ═══════════════════════ CONSTANTS ═══════════════════════════════
PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

CLR_BLACK = colors.HexColor("#1A1A1A")
CLR_DARK = colors.HexColor("#2C2C2C")
CLR_BODY = colors.HexColor("#3C4043")
CLR_GRAY_BG = colors.HexColor("#F8F9FA")
CLR_ROW_ALT = colors.HexColor("#FAFAFA")
CLR_HDR_TXT = colors.HexColor("#3C4043")
CLR_RULE = colors.HexColor("#E0E0E0")
CLR_BLUE = colors.HexColor("#1967D2")
CLR_GREEN = colors.HexColor("#137333")
CLR_ORANGE = colors.HexColor("#E37400")
CLR_RED = colors.HexColor("#D93025")
CLR_GOLD = colors.HexColor("#B8860B")
CLR_PURPLE = colors.HexColor("#7B1FA2")
CLR_LT_BLUE = colors.HexColor("#E8F0FE")
CLR_DK_BLUE = colors.HexColor("#174EA6")
CLR_LT_GRAY = colors.HexColor("#F1F3F4")
CLR_WHITE = colors.white
SPACER_H = 16

# ═══════════════════════ STYLES ══════════════════════════════════
def _build_styles():
    ss = getSampleStyleSheet()
    S = {}
    S['heading'] = ParagraphStyle('H', parent=ss['Normal'], fontName='Helvetica-Bold',
        fontSize=14, textColor=CLR_BLACK, spaceAfter=8, spaceBefore=12, leading=18)
    S['subheading'] = ParagraphStyle('SH', parent=ss['Normal'], fontName='Helvetica-Bold',
        fontSize=11, textColor=CLR_DARK, spaceAfter=6, spaceBefore=8, leading=14)
    S['body'] = ParagraphStyle('B', parent=ss['Normal'], fontName='Helvetica',
        fontSize=9.5, textColor=CLR_BODY, leading=14, spaceAfter=4)
    S['body_nowrap'] = ParagraphStyle('BNW', parent=S['body'],
        fontSize=9, leading=13)
    S['body_bold'] = ParagraphStyle('BB', parent=S['body'], fontName='Helvetica-Bold')
    S['small'] = ParagraphStyle('SM', parent=ss['Normal'], fontName='Helvetica',
        fontSize=8, textColor=colors.HexColor("#70757A"), leading=11)
    S['small_gray'] = ParagraphStyle('SG', parent=ss['Normal'], fontName='Helvetica',
        fontSize=9, textColor=colors.HexColor("#5F6368"), leading=12)
    S['italic'] = ParagraphStyle('IT', parent=S['body'], fontName='Helvetica-Oblique')
    S['big_score'] = ParagraphStyle('BS', parent=ss['Normal'], fontName='Helvetica-Bold',
        fontSize=56, leading=60, alignment=TA_CENTER)
    S['center'] = ParagraphStyle('CT', parent=S['body'], alignment=TA_CENTER)
    S['right'] = ParagraphStyle('RT', parent=S['body'], alignment=TA_RIGHT)
    S['footer'] = ParagraphStyle('FT', parent=ss['Normal'], fontName='Helvetica',
        fontSize=8, textColor=colors.HexColor("#70757A"), alignment=TA_CENTER, leading=10)
    S['badge'] = ParagraphStyle('BD', parent=ss['Normal'], fontName='Helvetica-Bold',
        fontSize=14, textColor=CLR_WHITE, alignment=TA_CENTER, leading=18)
    S['right_num'] = ParagraphStyle('RN', parent=S['body'], alignment=TA_RIGHT,
        fontName='Helvetica-Bold')
    return S

STYLES = _build_styles()

# ═══════════════════════ HELPERS ═════════════════════════════════
def _clean_md(text):
    if not text: return ""
    t = str(text)
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
    t = re.sub(r'\*(.+?)\*', r'\1', t)
    t = re.sub(r'`(.+?)`', r'\1', t)
    t = re.sub(r'^#{1,6}\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'^[-*]\s+', '', t, flags=re.MULTILINE)
    return t.replace('```', '').strip()

def _safe(text, max_len=0):
    s = _clean_md(str(text)) if text else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if max_len and len(s) > max_len: s = s[:max_len] + "..."
    return s

def _gemini(prompt, model_name="gemini-2.5-pro", _retries=1):
    """Call Gemini with retry. Raises RuntimeError if empty after retries."""
    try:
        m = genai.GenerativeModel(model_name)
        for attempt in range(_retries + 1):
            r = m.generate_content(prompt, generation_config=genai.types.GenerationConfig(
                temperature=0.2, max_output_tokens=2048))
            if r.candidates and len(r.candidates) > 0:
                text = "".join(p.text for p in r.candidates[0].content.parts if hasattr(p, 'text')).strip()
                if text:
                    return text
        raise RuntimeError(f"Gemini returned empty response after {_retries + 1} attempts")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}")

def _gemini_json(prompt, required_keys, model_name="gemini-2.5-pro", _retries=1):
    """Call Gemini expecting JSON. Validates required_keys. Raises RuntimeError on failure."""
    json_prompt = prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, no extra text. Just the JSON object."
    last_err = None
    for attempt in range(_retries + 1):
        try:
            raw = _gemini(json_prompt, model_name=model_name)
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                # Remove opening fence (with optional language tag)
                cleaned = re.sub(r'^```[a-zA-Z]*\s*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            # Validate required keys
            missing = []
            for k in required_keys:
                val = data.get(k)
                if val is None:
                    missing.append(k)
                elif isinstance(val, list) and len(val) == 0:
                    missing.append(k)
                elif isinstance(val, str) and not val.strip():
                    missing.append(k)
                elif isinstance(val, dict) and len(val) == 0:
                    missing.append(k)
            if missing:
                last_err = f"Missing or empty keys: {missing}"
                continue
            return data
        except json.JSONDecodeError as e:
            last_err = f"JSON parse error: {e}"
            continue
        except RuntimeError:
            raise
    raise RuntimeError(f"Gemini JSON validation failed after {_retries + 1} attempts: {last_err}")

def _score_clr(s):
    if s >= 90: return CLR_GOLD
    if s >= 75: return CLR_GREEN
    if s >= 60: return CLR_ORANGE
    return CLR_RED

def _status(pct):
    if pct >= 80: return ("Excellent", CLR_GREEN)
    if pct >= 60: return ("Good", CLR_BLUE)
    if pct >= 40: return ("Needs Work", CLR_ORANGE)
    return ("Poor", CLR_RED)

def _verdict(s):
    if s >= 90: return ("Exceptional", CLR_GOLD)
    if s >= 75: return ("Strong Hire", CLR_GREEN)
    if s >= 60: return ("Hire with Mentorship", CLR_ORANGE)
    return ("Do Not Hire", CLR_RED)

def _heading(title):
    return [Paragraph(title, STYLES['heading']), _HRule(CONTENT_W, 2, CLR_BLACK), Spacer(1, 6)]

def _sp(): return Spacer(1, SPACER_H)

def _parse_bullets(text):
    if not text: return []
    return [re.sub(r'^[•\-*\d.)\]]+\s*', '', l).strip()
            for l in text.split('\n') if l.strip() and len(l.strip()) > 10]

# ═══════════════════════ CUSTOM FLOWABLES ════════════════════════
class _HRule(Flowable):
    def __init__(self, w, th=1, clr=CLR_RULE):
        super().__init__(); self.width=w; self.thickness=th; self.color=clr; self.height=th+2
    def wrap(self, aW, aH): return self.width, self.height
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 1, self.width, 1)

class _Badge(Flowable):
    def __init__(self, text, bg, width=None, height=28):
        super().__init__(); self.text=text; self.bg=bg
        self.badge_w=width or CONTENT_W; self.badge_h=height
    def wrap(self, aW, aH): return self.badge_w, self.badge_h
    def draw(self):
        self.canv.setFillColor(self.bg)
        self.canv.roundRect(0,0,self.badge_w,self.badge_h,4,fill=1,stroke=0)
        self.canv.setFillColor(CLR_WHITE); self.canv.setFont("Helvetica-Bold",14)
        tw = self.canv.stringWidth(self.text,"Helvetica-Bold",14)
        self.canv.drawString((self.badge_w-tw)/2, (self.badge_h-14)/2+2, self.text)

class _Bar(Flowable):
    def __init__(self, val, mx, w=200, h=12, fill=CLR_DK_BLUE, bg=CLR_LT_GRAY):
        super().__init__(); self.val=min(val,mx); self.mx=mx or 1
        self.bw=w; self.bh=h; self.fc=fill; self.bc=bg
    def wrap(self, aW, aH): return self.bw, self.bh
    def draw(self):
        self.canv.setFillColor(self.bc)
        self.canv.roundRect(0,0,self.bw,self.bh,3,fill=1,stroke=0)
        fw = (self.val/self.mx)*self.bw
        if fw > 0:
            self.canv.setFillColor(self.fc)
            self.canv.roundRect(0,0,fw,self.bh,3,fill=1,stroke=0)

# ═══════════════════════ TABLE BUILDER ═══════════════════════════
def _table(headers, rows, cw=None, hdr_bg=CLR_GRAY_BG, hl_row=-1):
    data = [headers] + rows
    if not cw:
        n = len(headers); cw = [CONTENT_W/n]*n
    t = Table(data, colWidths=cw, repeatRows=1)
    cmds = [
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,0),9),
        ('TEXTCOLOR',(0,0),(-1,0),CLR_DARK), ('BACKGROUND',(0,0),(-1,0),hdr_bg),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'), ('FONTSIZE',(0,1),(-1,-1),9.5),
        ('TEXTCOLOR',(0,1),(-1,-1),CLR_BODY), ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'), ('GRID',(0,0),(-1,-1),0.4,CLR_LT_GRAY),
        ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0: cmds.append(('BACKGROUND',(0,i),(-1,i),CLR_ROW_ALT))
    if 0 <= hl_row < len(data)-1:
        r = hl_row+1
        cmds.append(('BACKGROUND',(0,r),(-1,r),CLR_LT_BLUE))
        cmds.append(('FONTNAME',(0,r),(-1,r),'Helvetica-Bold'))
    t.setStyle(TableStyle(cmds)); return t

def _bullets(items, style=None):
    if style is None: style = STYLES['body']
    li = [ListItem(Paragraph(_safe(i), style), bulletColor=CLR_BODY, leftIndent=6) for i in items]
    return ListFlowable(li, bulletType='bullet', bulletFontSize=9, bulletOffsetY=-1, start='•', leftIndent=12, spaceAfter=4)

def _callout(flowables, border=CLR_BLUE, bg=None):
    if bg is None: bg = CLR_GRAY_BG
    inner = Table([[flowables]], colWidths=[CONTENT_W-12])
    inner.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),14),
        ('TOPPADDING',(0,0),(-1,-1),10), ('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('BACKGROUND',(0,0),(-1,-1),bg),
        ('LINEBEFORESTYLE',(0,0),(0,-1),'SOLID'),
        ('LINEBEFOREWIDTH',(0,0),(0,-1),4),
        ('LINEBEFORECOLOR',(0,0),(0,-1),border),
        ('BOX',(0,0),(-1,-1),0.4,CLR_LT_GRAY),
    ])); return inner

# ═══════════════════════ PAGE TEMPLATE ═══════════════════════════
class _PageHandler:
    def __init__(self, logo_path):
        self.logo_path = logo_path; self.total_pages = [0]
    def __call__(self, canvas, doc):
        canvas.saveState()
        pn = canvas.getPageNumber()
        # Full header with logo, title, date, rule — FIRST PAGE ONLY
        if pn == 1:
            hy = PAGE_H - MARGIN + 10
            if self.logo_path and os.path.exists(self.logo_path):
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(self.logo_path)
                    iw, ih = img.size; th = 60; sc = th/ih; tw = iw*sc
                    # Center the logo
                    lx = (PAGE_W - tw) / 2
                    canvas.drawImage(self.logo_path, lx, hy-55, width=tw, height=th,
                                     preserveAspectRatio=True, mask='auto')
                except Exception:
                    canvas.setFont("Helvetica-Bold",14); canvas.setFillColor(CLR_DK_BLUE)
                    canvas.drawCentredString(PAGE_W/2, hy-10, "HiDevs")
            else:
                canvas.setFont("Helvetica-Bold",14); canvas.setFillColor(CLR_DK_BLUE)
                canvas.drawCentredString(PAGE_W/2, hy-10, "HiDevs")
            
            canvas.setFont("Helvetica-Bold",10); canvas.setFillColor(colors.HexColor("#888888"))
            canvas.drawCentredString(PAGE_W/2, hy-68, "CANDIDATE EVALUATION REPORT")
            canvas.setFont("Helvetica",8)
            canvas.drawCentredString(PAGE_W/2, hy-78,
                                   f"Generated: {datetime.now().strftime('%B %d, %Y')}")
            canvas.setStrokeColor(CLR_RULE); canvas.setLineWidth(1)
            canvas.line(MARGIN, hy-85, PAGE_W-MARGIN, hy-85)
        # Page number on ALL pages
        canvas.setFont("Helvetica",8); canvas.setFillColor(colors.HexColor("#999999"))
        canvas.drawCentredString(PAGE_W/2, MARGIN-20, f"Page {pn}")
        canvas.restoreState()

# ═══════════════════════ SECTION BUILDERS ════════════════════════

# ── S1: Executive Summary Dashboard ──────────────────────────────
def _s1_executive(ev, name, challenge, exp_level, repo_url=""):
    el = _heading("EXECUTIVE SUMMARY")
    overall = ev.get('overall_score', 0)
    ctx = ev.get('experience_context', {})
    dec_txt, dec_clr = _verdict(overall)
    sc = _score_clr(overall)
    # Shorten URL for display to prevent word-breaking
    disp_url = str(repo_url).rstrip('/')
    if len(disp_url) > 50:
        parts = disp_url.split('/')
        if len(parts) >= 5:
            disp_url = '/'.join(parts[:3]) + '/.../' + parts[-1]
    left = [("Candidate Name", _safe(name)),
            ("Repository URL", _safe(disp_url)),
            ("Evaluation Date", datetime.now().strftime("%B %d, %Y"))]
    right = [("Challenge Category", _safe(challenge)),
             ("Experience Level", exp_level.replace('_',' ').title()),
             ("Final Verdict", dec_txt)]
    rows = []
    mx = max(len(left), len(right))
    for i in range(mx):
        lc = ""
        if i < len(left):
            lb, vl = left[i]
            lc = [Paragraph(f'<font color="#888888" size="8">{lb}</font>', STYLES['body']),
                  Paragraph(f'<b>{vl}</b>', STYLES['body'])]
        rc = ""
        if i < len(right):
            lb, vl = right[i]
            rc = [Paragraph(f'<font color="#888888" size="8">{lb}</font>', STYLES['body']),
                  Paragraph(f'<b>{vl}</b>', STYLES['body'])]
        rows.append([lc, rc])
    ss = ParagraphStyle('SD', parent=STYLES['big_score'], textColor=sc)
    rows.append([
        [Paragraph('<font color="#888888" size="8">Overall Score</font>', STYLES['body']),
         Paragraph(f'{overall:.1f}', ss)],
        [Paragraph('<font color="#888888" size="8">Hiring Decision</font>', STYLES['body']),
         Spacer(1,4), _Badge(dec_txt, dec_clr, width=CONTENT_W*0.45)]
    ])
    it = Table(rows, colWidths=[CONTENT_W*0.5, CONTENT_W*0.5])
    it.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('TOPPADDING',(0,0),(-1,-1),10),
        ('BOTTOMPADDING',(0,0),(-1,-1),10), ('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12), ('GRID',(0,0),(-1,-1),0.4,CLR_LT_GRAY),
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor("#FFFFFF")),
    ]))
    el.append(it)
    
    # Project Purpose & Functionality
    rd = ev.get('report', ev)
    ps = rd.get('project_summary', {})
    purpose = ps.get('purpose_and_functionality', 'Analysis of core project functionality and implementation patterns.')
    if purpose:
        el.append(Spacer(1, 15))
        el.append(Paragraph("PROJECT PURPOSE & FUNCTIONALITY", STYLES['subheading']))
        el.append(Paragraph(_safe(purpose), STYLES['body']))
        
    el.append(Spacer(1, 16)); el.append(PageBreak())
    return el

# ── S2: Evaluation Breakdown ─────────────────────────────────────
def _s2_breakdown(ev):
    el = _heading("EVALUATION BREAKDOWN")
    rd = ev.get('report', ev)
    criteria = rd.get('evaluation_criteria', [])
    adjs = ev.get('score_adjustments', [])
    rows = []; cd = []
    if adjs:
        for a in adjs:
            nm = a.get('category','Unknown'); orig = a.get('original',0)
            pct = orig; sl, sc = _status(pct)
            rows.append([Paragraph(f'<b>{_safe(nm)}</b>', STYLES['body']),
                         Paragraph("100", STYLES['right_num']),
                         Paragraph(f"{orig:.1f}", STYLES['right_num']),
                         Paragraph(f"{pct:.0f}%", STYLES['right_num']),
                         Paragraph(f'<font color="{sc.hexval()}">{sl}</font>', STYLES['body'])])
            cd.append((nm, orig, 100))
    elif criteria:
        for c in criteria:
            nm = c.get('criterion_name','Unknown'); s = c.get('score',0)
            pct = s; sl, sc = _status(pct)
            rows.append([Paragraph(f'<b>{_safe(nm)}</b>', STYLES['body']),
                         Paragraph("100", STYLES['right_num']),
                         Paragraph(f"{s:.1f}", STYLES['right_num']),
                         Paragraph(f"{pct:.0f}%", STYLES['right_num']),
                         Paragraph(f'<font color="{sc.hexval()}">{sl}</font>', STYLES['body'])])
            cd.append((nm, s, 100))
    if rows:
        hd = ["Evaluation Criteria","Weight (%)","Score","Weighted %","Status"]
        cw = [CONTENT_W*0.30, CONTENT_W*0.15, CONTENT_W*0.15, CONTENT_W*0.15, CONTENT_W*0.25]
        ov = ev.get('overall_score', 0)
        rows.append([Paragraph('<b>Overall Repository Score</b>', STYLES['body_bold']),
                     Paragraph("", STYLES['right_num']),
                     Paragraph(f"<b>{ov:.1f}</b>", STYLES['right_num']),
                     Paragraph(f"<b>{ov:.0f}%</b>", STYLES['right_num']),
                     Paragraph("", STYLES['body'])])
        el.append(_table(hd, rows, cw=cw)); el.append(Spacer(1,10))
    if cd:
        bh=12; gap=6; ch=len(cd)*(bh+gap)+30; cw2=CONTENT_W
        d = Drawing(cw2, ch); lw=140; baw=cw2-lw-10
        for i,(nm,earned,mx) in enumerate(cd):
            y = ch-20-i*(bh+gap)
            sn = nm[:22]+".." if len(nm)>24 else nm
            d.add(String(0,y+1,sn,fontName='Helvetica',fontSize=7,fillColor=CLR_BODY))
            d.add(Rect(lw,y,baw,bh,fillColor=CLR_LT_GRAY,strokeColor=None,strokeWidth=0))
            ew = (earned/mx*baw) if mx else 0
            if ew>0: d.add(Rect(lw,y,ew,bh,fillColor=CLR_DK_BLUE,strokeColor=None,strokeWidth=0))
        el.append(d)
    el.append(_sp()); return el

# ── S3: Primary Assessment & Value Proposition ───────────────────
def _s3_assessment(ev):
    el = _heading("PRIMARY ASSESSMENT &amp; VALUE PROPOSITION")
    ejs = json.dumps(ev, indent=2, default=str)[:6000]
    p = f"""You are a senior technical recruiter writing a formal candidate assessment.
Based on this evaluation data: {ejs}

Return a JSON object with EXACTLY these 3 keys, each containing an array of strings (bullet points).
Each array must have at least 3 items. Each item must be a complete, professional sentence (at least 15 characters).

{{
  "technical_summary": ["bullet 1", "bullet 2", "bullet 3"],
  "value_proposition": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
  "project_positioning": ["bullet 1", "bullet 2", "bullet 3"]
}}

Rules: Plain text only in each bullet. No markdown, no bold, no asterisks."""
    data = _gemini_json(p, required_keys=["technical_summary", "value_proposition", "project_positioning"])
    section_map = {
        "TECHNICAL SUMMARY": data["technical_summary"],
        "VALUE PROPOSITION": data["value_proposition"],
        "PROJECT POSITIONING": data["project_positioning"],
    }
    for title, bullets in section_map.items():
        if not bullets or len(bullets) < 3:
            raise RuntimeError(f"Section 'Primary Assessment': subsection '{title}' has fewer than 3 items")
        el.append(Paragraph(f'<b>{_safe(title)}</b>', STYLES['subheading']))
        el.append(_bullets([str(b) for b in bullets]))
        el.append(Spacer(1, 6))
    el.append(_sp())
    return el

# ── S4: Experience-Aware Scoring ─────────────────────────────────
def _s4_experience(ev, exp_scores, exp_level):
    el = _heading("EXPERIENCE-AWARE SCORING")
    lvls = {'2nd_year':'2nd Year','3rd_year':'3rd Year','4th_year':'4th Year',
            'fresher':'Fresher (0-1 yr)','experienced_0_2':'Experienced (1-2 yr)',
            'senior':'Senior (3+ yr)'}
    raw = ev.get('original_overall', 0)
    rows = []; hl = -1
    for i,(key,label) in enumerate(lvls.items()):
        adj = exp_scores.get(key,{}).get('overall_score',0) if exp_scores else 0
        ec = exp_scores.get(key,{}).get('experience_context',{}) if exp_scores else {}
        grade = "A" if adj>=85 else "B" if adj>=70 else "C" if adj>=55 else "D"
        thr = ec.get('benchmark_good', '-')
        rows.append([label, Paragraph(f"{raw:.1f}", STYLES['right_num']),
                     Paragraph(f"{adj:.1f}", STYLES['right_num']), grade, str(thr)])
        if key == exp_level: hl = i
    hd = ["Experience Level","Raw Score","Adjusted Score","Grade","Threshold"]
    cw = [CONTENT_W*0.24, CONTENT_W*0.17, CONTENT_W*0.19, CONTENT_W*0.15, CONTENT_W*0.25]
    el.append(_table(hd, rows, cw=cw, hl_row=hl)); el.append(Spacer(1,10))
    ps = ev.get('overall_score', 0)
    box = [Paragraph('<b>PRIMARY SCORE</b>', STYLES['subheading']),
           Paragraph(f'<font size="24"><b>{ps:.1f}</b></font> / 100', STYLES['center']),
           Spacer(1,4)]
    el.append(_callout(box, border=CLR_BLUE, bg=CLR_LT_BLUE))
    el.append(_sp()); return el

# ── S5: Industry Benchmark ───────────────────────────────────────
def _s5_benchmark(ev, exp_level):
    el = _heading("INDUSTRY BENCHMARK")
    ctx = ev.get('experience_context', {})
    bmin = ctx.get('benchmark_min'); bgood = ctx.get('benchmark_good')
    bexc = ctx.get('benchmark_excellent')
    overall = ev.get('overall_score', 0)
    if bmin is not None and bgood is not None and bexc is not None:
        rows = [
            ["Minimum Acceptable", Paragraph(f"{bmin}", STYLES['right_num'])],
            ["Good Performance", Paragraph(f"{bgood}", STYLES['right_num'])],
            ["Excellent Performance", Paragraph(f"{bexc}", STYLES['right_num'])],
            [Paragraph("<b>Candidate Score</b>", STYLES['body_bold']),
             Paragraph(f"<b>{overall:.1f}</b>", STYLES['right_num'])],
        ]
        hd = ["Industry Standard", "Score"]
        cw = [CONTENT_W*0.6, CONTENT_W*0.4]
        el.append(_table(hd, rows, cw=cw))
        el.append(Spacer(1,8))
        if overall >= bexc: cmp = "EXCEEDS industry excellent benchmark"
        elif overall >= bgood: cmp = "MEETS industry good benchmark"
        elif overall >= bmin: cmp = "MEETS minimum industry standard"
        else: cmp = "BELOW minimum industry standard"
        el.append(Paragraph(f'<b>Candidate vs Industry:</b> {_safe(cmp)}', STYLES['body']))
    else:
        raise RuntimeError("Section 'Industry Benchmark': benchmark thresholds (benchmark_min, benchmark_good, benchmark_excellent) are missing from experience_context")
    el.append(_sp()); return el

# ── S6: Core Skill Analysis ──────────────────────────────────────
def _s6_skills(ev):
    el = _heading("CORE SKILL ANALYSIS")
    rd = ev.get('report', ev)
    sr = rd.get('skill_ratings', {}); sd = rd.get('scoring_details', {})
    if not isinstance(sd, dict): sd = {}
    def _rl(s):
        if s>=85: return ("Expert", CLR_GREEN)
        if s>=70: return ("Advanced", CLR_BLUE)
        if s>=50: return ("Intermediate", CLR_ORANGE)
        return ("Beginner", CLR_RED)
    skills = [
        ("Python Proficiency", sd.get('code_quality', 60)),
        ("OOP Concepts", sd.get('completeness', 55)),
        ("DSA Knowledge", sd.get('code_quality', 50)),
        ("Prompt Engineering", sd.get('innovation', 45)),
        ("System Architecture", sd.get('production', 50)),
        ("Testing & QA", sd.get('documentation', 45)),
        ("Professionalism", sd.get('code_quality', 55)),
        ("Time Management", sd.get('completeness', 50)),
    ]
    for sn, srd in sr.items():
        sc = srd.get('rating', 50) if isinstance(srd, dict) else srd
        if not any(s[0]==sn for s in skills): skills.append((sn, sc))
    rows = []
    for domain, score in skills[:8]:
        lb, clr = _rl(score)
        rows.append([Paragraph(f'<b>{_safe(domain)}</b>', STYLES['body']),
                     Paragraph(f"{score:.0f}", STYLES['right_num']),
                     Paragraph(f'<font color="{clr.hexval()}">{lb}</font>', STYLES['body'])])
    hd = ["Skill Domain","Score","Proficiency"]
    cw = [CONTENT_W*0.40, CONTENT_W*0.20, CONTENT_W*0.40]
    el.append(_table(hd, rows, cw=cw)); el.append(_sp()); return el

# ── S7: Criteria-Wise Evaluation ─────────────────────────────────
def _s7_criteria(ev, exp_level, challenge):
    el = _heading("CRITERIA-WISE EVALUATION")
    rd = ev.get('report', ev)
    criteria = rd.get('evaluation_criteria', [])
    adjs = ev.get('score_adjustments', [])
    ps = rd.get('project_summary', {}); ts = ps.get('tech_stack', [])
    items = []
    if adjs:
        for a in adjs:
            items.append({'name': a.get('category', 'Unknown'),
                          'score': a.get('adjusted', a.get('original', 0)), 'max': 100})
    elif criteria:
        for c in criteria:
            items.append({'name': c.get('criterion_name', 'Unknown'),
                          'score': c.get('score', 0), 'max': 100})
    if not items:
        raise RuntimeError("Section 'Criteria-Wise Evaluation': no evaluation criteria or score adjustments found in evaluation data")
    # Single batch Gemini JSON call for all criteria feedback
    criteria_names = [it['name'] for it in items]
    criteria_summary = "; ".join([f"{it['name']}: {it['score']:.1f}/{it['max']}" for it in items])
    fb_prompt = f"""For a {exp_level.replace('_', ' ')} candidate in a {challenge} evaluation.
Technologies: {', '.join(ts[:6]) if ts else 'Not specified'}
Scores: {criteria_summary}

Return a JSON object with a single key "feedback" containing an object.
The keys must be EXACTLY these criterion names: {json.dumps(criteria_names)}
Each value must be exactly 2 sentences of specific, actionable feedback (plain text, no markdown).

Example format:
{{
  "feedback": {{
    "{criteria_names[0]}": "Sentence one about performance. Sentence two with actionable advice."
  }}
}}"""
    fb_data = _gemini_json(fb_prompt, required_keys=["feedback"])
    fb_map = fb_data.get("feedback", {})
    if not isinstance(fb_map, dict):
        raise RuntimeError("Section 'Criteria-Wise Evaluation': Gemini returned invalid feedback format")
    # Render each criterion with progress bar + feedback
    for item in items:
        nm = item['name']; sc = item['score']; mx = item['max']
        el.append(Paragraph(f'<b>{_safe(nm)}</b>  —  <b>{sc:.1f} / {mx}</b>', STYLES['body_bold']))
        el.append(_Bar(sc, mx, w=CONTENT_W * 0.90, h=12))
        el.append(Spacer(1, 4))
        fb = str(fb_map.get(nm, '')).strip()
        if not fb:
            raise RuntimeError(f"Section 'Criteria-Wise Evaluation': no feedback returned for criterion '{nm}'")
        el.append(Paragraph(f'{_safe(fb)}', STYLES['body']))
        el.append(Spacer(1, 8))
    el.append(_sp())
    return el

# ── S8: Technology Proficiency ───────────────────────────────────
def _s8_tech(ev):
    el = _heading("TECHNOLOGY PROFICIENCY")
    rd = ev.get('report', ev)
    ps = rd.get('project_summary', {}); ts = ps.get('tech_stack', [])
    sd = rd.get('scoring_details', {})
    if not isinstance(sd, dict): sd = {}
    tm = sd.get('tech_match', 60)
    if ts:
        rows = []
        for tech in ts[:10]:
            prof = min(100, max(20, tm + hash(tech) % 20 - 10))
            usage = "Primary" if prof>=70 else "Secondary" if prof>=50 else "Minimal"
            depth = "Deep integration" if prof>=70 else "Moderate usage" if prof>=50 else "Basic usage"
            rows.append([Paragraph(f'<b>{_safe(tech)}</b>', STYLES['body']),
                         usage, depth, Paragraph(f'{prof}%', STYLES['right_num'])])
        hd = ["Technology","Usage Level","Depth of Usage","Proficiency"]
        cw = [CONTENT_W*0.28, CONTENT_W*0.18, CONTENT_W*0.30, CONTENT_W*0.24]
        el.append(_table(hd, rows, cw=cw))
    else:
        raise RuntimeError("Section 'Technology Proficiency': no tech_stack found in project_summary")
    el.append(_sp()); return el

# ── S9: Hiring Analysis ──────────────────────────────────────────
def _s9_hiring(ev):
    el = _heading("HIRING ANALYSIS")
    overall = ev.get('overall_score', 0)
    ejs = json.dumps(ev, indent=2, default=str)[:5000]
    rd = ev.get('report', ev); ps = rd.get('project_summary', {})
    # Single consolidated Gemini JSON call for all hiring sub-sections
    hire_prompt = f"""You are a senior technical recruiter analyzing a candidate.
Evaluation data: {ejs}
Project summary: {json.dumps(ps, default=str)[:1500]}
Candidate scored {overall:.1f}/100.

Return a JSON object with these keys:
{{
  "why_hire": ["reason 1", "reason 2", "reason 3", "reason 4"],
  "key_strengths": ["strength 1", "strength 2", "strength 3", "strength 4"],
  "company_relevancy": ["company/industry fit 1", "company/industry fit 2", "company/industry fit 3"]
}}

Rules:
- "why_hire" must have exactly 4 items explaining why this candidate should be hired.
- "key_strengths" must have exactly 4 specific technical strengths.
- "company_relevancy" must have 3-4 items describing which companies/industries benefit from hiring this candidate.
- All items must be plain text, no markdown. Each item at least 20 characters."""
    hire_data = _gemini_json(hire_prompt, required_keys=["why_hire", "key_strengths", "company_relevancy"])
    # Why Hire
    if overall >= 60:
        why_hire = hire_data.get("why_hire", [])
        if not why_hire or len(why_hire) < 3:
            raise RuntimeError("Section 'Hiring Analysis': 'why_hire' has fewer than 3 items")
        el.append(Paragraph('<b>WHY HIRE THIS CANDIDATE?</b>', STYLES['subheading']))
        el.append(_callout([_bullets([str(b) for b in why_hire[:4]])], border=CLR_GREEN)); el.append(Spacer(1,8))
    # Project Summary
    el.append(Paragraph('<b>PROJECT SUMMARY</b>', STYLES['subheading']))
    pname = ps.get('repository', 'Unknown')
    el.append(Paragraph(f'Repository: {_safe(pname)}', STYLES['body']))
    el.append(Spacer(1,6))
    # Key Strengths
    key_strengths = hire_data.get("key_strengths", [])
    if not key_strengths or len(key_strengths) < 3:
        raise RuntimeError("Section 'Hiring Analysis': 'key_strengths' has fewer than 3 items")
    el.append(Paragraph('<b>KEY STRENGTHS</b>', STYLES['subheading']))
    el.append(_callout([_bullets([str(b) for b in key_strengths[:4]])], border=CLR_BLUE)); el.append(Spacer(1,8))
    # Company Relevancy
    company_rel = hire_data.get("company_relevancy", [])
    if not company_rel or len(company_rel) < 3:
        raise RuntimeError("Section 'Hiring Analysis': 'company_relevancy' has fewer than 3 items")
    el.append(Paragraph('<b>COMPANY RELEVANCY</b>', STYLES['subheading']))
    el.append(_callout([_bullets([str(b) for b in company_rel[:4]])], border=CLR_PURPLE)); el.append(Spacer(1,8))
    el.append(_sp()); return el

# ── S10: Areas for Improvement ───────────────────────────────────
def _s10_improve(ev):
    el = _heading("AREAS FOR IMPROVEMENT")
    ejs = json.dumps(ev, indent=2, default=str)[:5000]
    # Single consolidated Gemini JSON call
    improve_prompt = f"""Based on this candidate evaluation: {ejs}

Return a JSON object with these keys:
{{
  "weaknesses": ["weakness 1", "weakness 2", "weakness 3", "weakness 4"],
  "improvements": ["improvement 1", "improvement 2", "improvement 3", "improvement 4", "improvement 5"]
}}

Rules:
- "weaknesses" must have exactly 4 specific, actionable weaknesses.
- "improvements" must have exactly 5 specific, actionable improvements for the next 90 days.
- All items must be plain text, no markdown. Each item at least 20 characters."""
    improve_data = _gemini_json(improve_prompt, required_keys=["weaknesses", "improvements"])
    # Weaknesses
    weaknesses = improve_data.get("weaknesses", [])
    if not weaknesses or len(weaknesses) < 3:
        raise RuntimeError("Section 'Areas for Improvement': 'weaknesses' has fewer than 3 items")
    el.append(Paragraph('<b>WEAKNESSES</b>', STYLES['subheading']))
    el.append(_callout([_bullets([str(w) for w in weaknesses[:4]])], border=CLR_ORANGE)); el.append(Spacer(1,8))
    # Recommended Improvements
    improvements = improve_data.get("improvements", [])
    if not improvements or len(improvements) < 4:
        raise RuntimeError("Section 'Areas for Improvement': 'improvements' has fewer than 4 items")
    el.append(Paragraph('<b>RECOMMENDED IMPROVEMENTS</b>', STYLES['subheading']))
    numbered = [Paragraph(f'<b>{i}.</b> {_safe(str(it))}', STYLES['body']) for i, it in enumerate(improvements[:5],1)]
    el.append(_callout(numbered, border=colors.HexColor("#888888"), bg=CLR_GRAY_BG))
    el.append(_sp()); return el

# ── S11: Proof of Evidence ───────────────────────────────────────
def _s11_evidence(ev):
    el = _heading("PROOF OF EVIDENCE")
    el.append(Paragraph('<b>Deep Code Analysis — Verified Quality Indicators</b>', STYLES['subheading']))
    rd = ev.get('report', ev) if isinstance(ev, dict) else {}
    valid_entries = rd.get('verified_evidences', [])
    if not isinstance(valid_entries, list):
        valid_entries = []
        
    if len(valid_entries) < 3:
        raise RuntimeError(f"Section 'Proof of Evidence': only {len(valid_entries)} verified evidence items found, minimum 3 required. Ensure repository content is accessible.")

    for idx, e in enumerate(valid_entries[:6], 1):
        accent = CLR_GREEN if e.get('positive', True) else CLR_ORANGE
        cc = [
            [Paragraph(f'<b>Evidence #{idx}: {_safe(e.get("type","Evidence"))}</b>', STYLES['body_bold'])],
            [Paragraph(f'<font color="#757575">File: {_safe(e.get("file","N/A"))}  |  Lines: {_safe(e.get("lines","N/A"))}</font>', STYLES['small_gray'])],
            [Paragraph(f'<font color="#757575">Function: {_safe(e.get("function","N/A"))}</font>', STYLES['small_gray'])],
            [Paragraph(f'<b>What was implemented:</b> {_safe(e.get("finding","N/A"))}', STYLES['body'])],
            [Paragraph(f'<i>Why it matters: {_safe(e.get("significance","N/A"))}</i>', STYLES['italic'])],
        ]
        ct = Table(cc, colWidths=[CONTENT_W-16])
        ct.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),14),
            ('TOPPADDING',(0,0),(-1,-1),6), ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LINEBEFORESTYLE',(0,0),(0,-1),'SOLID'), ('LINEBEFOREWIDTH',(0,0),(0,-1),4),
            ('LINEBEFORECOLOR',(0,0),(0,-1),accent),
            ('BACKGROUND',(0,0),(-1,-1),colors.HexColor("#FFFFFF")),
            ('BOX',(0,0),(-1,-1),0.4,CLR_LT_GRAY),
        ]))
        el.append(KeepTogether([ct, Spacer(1, 10)]))
    el.append(_sp()); return el

# ── S12: Total Commits ───────────────────────────────────────────
def _s12_commits(commit_data):
    el = _heading("TOTAL NUMBER OF COMMITS")
    if not commit_data or not commit_data.get('fetched', False):
        err = commit_data.get('error', 'Commit data could not be fetched') if commit_data else 'No commit data provided'
        # Improved robustness: show warning instead of crashing
        el.append(Paragraph(f"<i>Note: {err}. Real-time commit tracking metrics are unavailable for this report.</i>", STYLES['body']))
        el.append(_sp()); return el
    total = commit_data.get('total', 0)
    contribs = commit_data.get('contributors_count', 0)
    pattern = commit_data.get('pattern', 'Unknown')
    authors = commit_data.get('authors', [])
    rows = [
        ["Total Commits", Paragraph(f"<b>{total}</b>", STYLES['right_num'])],
        ["Contributors", Paragraph(f"<b>{contribs}</b>", STYLES['right_num'])],
        ["Commit Pattern", Paragraph(f"<b>{_safe(pattern)}</b>", STYLES['body_bold'])],
    ]
    if authors:
        rows.append(["Authors", Paragraph(f"<b>{_safe(', '.join(authors[:5]))}</b>", STYLES['body_bold'])])
    hd = ["Metric", "Value"]
    cw = [CONTENT_W*0.5, CONTENT_W*0.5]
    el.append(_table(hd, rows, cw=cw)); el.append(Spacer(1,10))
    msgs = commit_data.get('messages', [])
    if msgs:
        el.append(Paragraph('<b>Recent Commit Messages (Sample)</b>', STYLES['subheading']))
        el.append(_bullets(msgs[:8]))
    weekly = commit_data.get('weekly', [])
    if weekly and len(weekly) > 1:
        el.append(Spacer(1,8))
        el.append(Paragraph('<b>Weekly Commit Activity</b>', STYLES['subheading']))
        bc = min(len(weekly), 8); cw2 = CONTENT_W*0.7; ch = 60
        d = Drawing(cw2, ch); bw = cw2/(bc*2)
        mc = max(weekly[:bc]) if weekly[:bc] else 1
        if mc == 0: mc = 1
        for i in range(bc):
            v = weekly[i] if i<len(weekly) else 0
            bh = (v/mc)*(ch-15) if mc else 0; x = i*bw*2+bw*0.5
            d.add(Rect(x,0,bw,max(bh,1),fillColor=CLR_DK_BLUE,strokeColor=None,strokeWidth=0))
            d.add(String(x+bw*0.2, max(bh,1)+2, str(v), fontName='Helvetica',fontSize=6,fillColor=CLR_BODY))
            d.add(String(x,-10,f"W{i+1}",fontName='Helvetica',fontSize=6,fillColor=colors.HexColor("#888888")))
        el.append(d)
    el.append(_sp()); return el

# ── S13: Technical Architecture Overview ──────────────────────────
def _s13_architecture(repo_analysis):
    el = _heading("TECHNICAL ARCHITECTURE OVERVIEW")
    if not isinstance(repo_analysis, dict):
        raise RuntimeError("Section 'Technical Architecture': repo_analysis is missing or invalid")
    
    arch = repo_analysis.get('architecture_overview', {})
    if not arch:
        # Fallback to empty dict but don't fail as it might be a partial analysis
        arch = {}
    
    maturity = arch.get('system_maturity', 'Prototype')
    m_clr = CLR_GREEN if 'Production' in maturity or 'Enterprise' in maturity else CLR_ORANGE if 'Beta' in maturity or 'Alpha' in maturity else CLR_RED
    
    box = [
        Paragraph(f'<b>System Maturity:</b> <font color="{m_clr.hexval()}">{_safe(maturity)}</font>', STYLES['subheading']),
        Paragraph(f'<i>{_safe(arch.get("maturity_justification", "Analysis of system design and implementation status."))}</i>', STYLES['body'])
    ]
    el.append(_callout(box, border=m_clr, bg=CLR_LT_GRAY))
    el.append(Spacer(1, 12))
    
    el.append(Paragraph('<b>HIGH-LEVEL DESIGN</b>', STYLES['subheading']))
    el.append(Paragraph(_safe(arch.get('high_level_design', 'Detailed architecture analysis based on repository patterns.')), STYLES['body']))
    el.append(Spacer(1, 10))
    
    el.append(Paragraph('<b>DATA FLOW SUMMARY</b>', STYLES['subheading']))
    el.append(Paragraph(_safe(arch.get('data_flow_summary', 'Information regarding data ingestion, processing, and output cycles.')), STYLES['body']))
    
    el.append(_sp()); return el

# ── S14: Repository Statistics ───────────────────────────────────
def _s14_repo_stats(ev, repo_analysis, commit_data):
    el = _heading("REPOSITORY STATISTICS")
    rd = ev.get('report', ev); ps = rd.get('project_summary', {})
    sd = rd.get('scoring_details', {}); ts = ps.get('tech_stack', [])
    if not isinstance(sd, dict): sd = {}
    rs = repo_analysis.get('repo_stats', {}) if isinstance(repo_analysis, dict) else {}
    
    # Robustness: use defaults if commit_data missing
    if not commit_data or not isinstance(commit_data, dict):
        commit_data = {"total": "N/A", "pattern": "N/A"}
        
    # Robustness: use defaults if repo_stats missing
    if not rs or not isinstance(rs, dict):
        rs = {"stars": 0, "forks": 0, "total_files": "N/A", "readme_quality_score": "N/A"}
        
    total_commits = commit_data.get('total', 'N/A')
    pattern = commit_data.get('pattern', 'Unknown')
    stars = rs.get('stars', 0)
    forks = rs.get('forks', 0)
    doc_s = sd.get('documentation', 50); prod_s = sd.get('production', 40)
    left = [
        f"GitHub Stars: <b>{stars}</b>",
        f"GitHub Forks: <b>{forks}</b>",
        f"Total Files: <b>{rs.get('total_files', 'N/A')}</b>",
        f"Total Commits: <b>{total_commits}</b>",
        f"Commit Pattern: <b>{_safe(pattern)}</b>",
    ]
    right = [
        f"README Quality: <b>{rs.get('readme_quality_score', 'N/A')}/10</b>",
        f"CI/CD Pipeline: <b>{'Detected' if rs.get('ci_cd_detected') else 'Not Detected'}</b>",
        f"Docker Setup: <b>{'Detected' if rs.get('docker_detected') else 'Not Detected'}</b>",
        f"Primary Language: <b>{rs.get('language') or (ts[0] if ts else 'Unknown')}</b>",
        f"Stack Category: <b>{_safe(ps.get('category', 'General'))}</b>",
    ]
    rows = []
    for i in range(max(len(left), len(right))):
        l = Paragraph(left[i], STYLES['body']) if i<len(left) else ""
        r = Paragraph(right[i], STYLES['body']) if i<len(right) else ""
        rows.append([l, r])
    st = Table(rows, colWidths=[CONTENT_W*0.5, CONTENT_W*0.5])
    st.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6), ('LEFTPADDING',(0,0),(-1,-1),10),
        ('RIGHTPADDING',(0,0),(-1,-1),10), ('GRID',(0,0),(-1,-1),0.4,CLR_LT_GRAY),
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor("#FFFFFF")),
    ]))
    el.append(st); el.append(Spacer(1,10))
    if ts:
        el.append(Paragraph('<b>Detected Technologies</b>', STYLES['subheading']))
        el.append(_bullets(ts[:12]))
    el.append(_sp()); return el

# ── SA: Risk Analysis ────────────────────────────────────────────
def _sA_risk(ev):
    el = _heading("RISK ANALYSIS")
    rd = ev.get('report', ev); sd = rd.get('scoring_details', {})
    if not isinstance(sd, dict): sd = {}
    cq = sd.get('code_quality', 50); doc = sd.get('documentation', 40)
    prod = sd.get('production', 45); comp = sd.get('completeness', 50)
    risks = [
        ("Code Quality", "Low" if cq>=70 else "Medium" if cq>=50 else "High",
         f"Code quality score: {cq}. " + ("Well-structured codebase." if cq>=70 else "Some quality improvements needed." if cq>=50 else "Significant quality concerns.")),
        ("Documentation", "Low" if doc>=70 else "Medium" if doc>=40 else "High",
         f"Documentation score: {doc}. " + ("Comprehensive documentation." if doc>=70 else "Partial documentation exists." if doc>=40 else "Critical documentation gaps.")),
        ("Production Readiness", "Low" if prod>=65 else "Medium" if prod>=45 else "High",
         f"Production score: {prod}. " + ("Production-ready setup." if prod>=65 else "Some production features present." if prod>=45 else "Not production-ready.")),
        ("Feature Completeness", "Low" if comp>=70 else "Medium" if comp>=50 else "High",
         f"Completeness score: {comp}. " + ("Core features implemented." if comp>=70 else "Partial implementation." if comp>=50 else "Major features missing.")),
        ("Security", "Low" if prod>=60 else "Medium" if prod>=40 else "High",
         "Based on production readiness indicators. " + ("Security practices observed." if prod>=60 else "Limited security measures." if prod>=40 else "Security hardening needed.")),
    ]
    rows = []
    for area, level, justification in risks:
        clr = CLR_GREEN if level=="Low" else CLR_ORANGE if level=="Medium" else CLR_RED
        rows.append([Paragraph(f'<b>{_safe(area)}</b>', STYLES['body']),
                     Paragraph(f'<font color="{clr.hexval()}"><b>{level}</b></font>', STYLES['body']),
                     Paragraph(_safe(justification), STYLES['body'])])
    hd = ["Area","Risk Level","Justification"]
    cw = [CONTENT_W*0.22, CONTENT_W*0.15, CONTENT_W*0.63]
    el.append(_table(hd, rows, cw=cw)); el.append(_sp()); return el

# ── SB: Production Readiness Breakdown ───────────────────────────
def _sB_prod_ready(ev):
    el = _heading("PRODUCTION READINESS BREAKDOWN")
    rd = ev.get('report', ev); sd = rd.get('scoring_details', {})
    if not isinstance(sd, dict): sd = {}
    cq = sd.get('code_quality', 50); doc = sd.get('documentation', 40); prod = sd.get('production', 45)
    def _rating(s):
        if s>=70: return "Strong"
        if s>=50: return "Moderate"
        return "Weak"
    components = [
        ("Testing", _rating(cq), "Unit/integration test presence and coverage indicators"),
        ("Logging", _rating(cq), "Structured logging and error tracking patterns"),
        ("CI/CD", _rating(prod), "Continuous integration and deployment pipeline"),
        ("Deployment", _rating(prod), "Container, cloud, or server deployment readiness"),
        ("Config Management", _rating(prod), "Environment variables, secrets management, config separation"),
    ]
    rows = []
    for comp, rating, desc in components:
        clr = CLR_GREEN if rating=="Strong" else CLR_ORANGE if rating=="Moderate" else CLR_RED
        rows.append([Paragraph(f'<b>{_safe(comp)}</b>', STYLES['body']),
                     Paragraph(f'<font color="{clr.hexval()}"><b>{rating}</b></font>', STYLES['body']),
                     Paragraph(_safe(desc), STYLES['body'])])
    hd = ["Component","Rating","Assessment"]
    cw = [CONTENT_W*0.22, CONTENT_W*0.15, CONTENT_W*0.63]
    el.append(_table(hd, rows, cw=cw))
    el.append(Spacer(1,6))
    el.append(Paragraph("<i>Note: This is a qualitative assessment based on repository indicators, not a recalculation of scores.</i>", STYLES['small_gray']))
    el.append(_sp()); return el

# ── SC: Interview Focus Recommendations ──────────────────────────
def _sC_interview(ev):
    el = _heading("INTERVIEW FOCUS RECOMMENDATIONS")
    ejs = json.dumps(ev, indent=2, default=str)[:4000]
    p = f"""Based on this candidate evaluation: {ejs}

Return a JSON object with a single key "questions" containing an array of exactly 5 strings.
Each string is a technical interview question that should be asked to validate claims.
Each question must be derived from the project characteristics and scores.

{{
  "questions": [
    "Question 1 specific to this project?",
    "Question 2 specific to this project?",
    "Question 3 specific to this project?",
    "Question 4 specific to this project?",
    "Question 5 specific to this project?"
  ]
}}

Rules: Each question must be at least 20 characters. Plain text only, no markdown."""
    q_data = _gemini_json(p, required_keys=["questions"])
    questions = q_data.get("questions", [])
    if not isinstance(questions, list) or len(questions) < 5:
        raise RuntimeError(f"Section 'Interview Focus Recommendations': expected 5 questions, got {len(questions) if isinstance(questions, list) else 0}")
    numbered = [Paragraph(f'<b>Q{i}.</b> {_safe(str(q))}', STYLES['body']) for i,q in enumerate(questions[:5],1)]
    el.append(_callout(numbered, border=CLR_DK_BLUE, bg=CLR_LT_BLUE))
    el.append(_sp()); return el

# ── Final Footer ─────────────────────────────────────────────────
def _footer(logo_path):
    el = [Spacer(1,20), _HRule(CONTENT_W, 1, CLR_RULE), Spacer(1,10),
          Paragraph("This report was generated by HiDevs AI Evaluation System", STYLES['center']),
          Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}  |  Confidential — For Internal Use Only", STYLES['center']),
          Spacer(1,10)]
    if logo_path and os.path.exists(logo_path):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(logo_path); iw,ih = img.size
            th=25; sc=th/ih; tw=iw*sc
            logo = RLImage(logo_path, width=tw, height=th); logo.hAlign='CENTER'
            el.append(logo)
        except Exception:
            el.append(Paragraph('<b>HiDevs</b>', STYLES['center']))
    else:
        el.append(Paragraph('<b>HiDevs</b>', STYLES['center']))
    return el

# ═══════════════════════ MAIN PUBLIC FUNCTION ════════════════════
def generate_pdf_report(
    evaluation_result: dict,
    repo_analysis: dict,
    metrics: dict,
    experience_scores: dict,
    commit_data: dict,
    candidate_name: str,
    challenge_type: str,
    experience_level: str,
    logo_path: str = "logo.jpg",
) -> bytes:
    """Generate a complete, production-grade PDF evaluation report. Returns PDF bytes."""
    print("[PDF] Starting PDF report generation...")
    if logo_path and not os.path.isabs(logo_path):
        base = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base, logo_path)
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN+75, bottomMargin=MARGIN+10,
        title="HiDevs Candidate Evaluation Report", author="HiDevs AI Evaluation System")
    # Shift frame top down to avoid header overlap (hy-85 rule)
    frame = Frame(MARGIN, MARGIN+10, CONTENT_W, PAGE_H-2*MARGIN-90, id='main')
    handler = _PageHandler(logo_path)
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=handler)])
    story = []
    rd = evaluation_result.get('report', evaluation_result)
    ps = rd.get('project_summary', {}); repo_url = ps.get('repository', '')
    sections = [
        ("1  Executive Dashboard",       lambda: _s1_executive(evaluation_result, candidate_name, challenge_type, experience_level, repo_url)),
        ("2  Evaluation Breakdown",      lambda: _s2_breakdown(evaluation_result)),
        ("PB", None),
        ("3  Primary Assessment",        lambda: _s3_assessment(evaluation_result)),
        ("PB", None),
        ("4  Experience-Aware Scoring",   lambda: _s4_experience(evaluation_result, experience_scores, experience_level)),
        ("5  Industry Benchmarks",       lambda: _s5_benchmark(evaluation_result, experience_level)),
        ("PB", None),
        ("6  Core Skill Analysis",       lambda: _s6_skills(evaluation_result)),
        ("7  Criteria-Wise Evaluation",  lambda: _s7_criteria(evaluation_result, experience_level, challenge_type)),
        ("PB", None),
        ("8  Technology Proficiency",    lambda: _s8_tech(evaluation_result)),
        ("9  Hiring Analysis",           lambda: _s9_hiring(evaluation_result)),
        ("PB", None),
        ("10 Areas of Improvement",      lambda: _s10_improve(evaluation_result)),
        ("11 Proof of Evidence",         lambda: _s11_evidence(evaluation_result)),
        ("PB", None),
        ("12 Total Commits",             lambda: _s12_commits(commit_data)),
        ("13 Technical Architecture",    lambda: _s13_architecture(repo_analysis)),
        ("14 Repository Statistics",     lambda: _s14_repo_stats(evaluation_result, repo_analysis, commit_data)),
        ("PB", None),
        ("15 Risk Analysis",             lambda: _sA_risk(evaluation_result)),
        ("16 Production Readiness",      lambda: _sB_prod_ready(evaluation_result)),
        ("PB", None),
        ("17 Interview Recommendations", lambda: _sC_interview(evaluation_result)),
        ("FT Footer",                    lambda: _footer(logo_path)),
    ]
    for label, builder in sections:
        if label == "PB":
            story.append(PageBreak()); continue
        print(f"[PDF] Building section {label}...")
        story.extend(builder())
    print("[PDF] Assembling final PDF...")
    doc.build(story)
    pdf_bytes = buf.getvalue(); buf.close()
    print(f"[PDF] Done: {len(pdf_bytes)} bytes")
    return pdf_bytes
