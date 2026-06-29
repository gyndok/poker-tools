#!/usr/bin/env python3
"""
Render a poker session-review PDF from a JSON spec.

Usage:
  python3 make_pdf.py <spec.json>            # outfile taken from JSON
  python3 make_pdf.py <spec.json> <out.pdf>  # override outfile

JSON spec:
{
  "title":    "Session Review — <tournament>",
  "subtitle": "2026-06-25 · 14 non-folded hands · GTO-principle analysis (not a solver run)",
  "summary":  "Prose session summary. Use ♠♥♦♣ glyphs for suits.",
  "stats":    [["Stat","You","Typical TAG"], ["VPIP","16%","20-24%"], ...],
  "stats_note": "Optional small-print under the table (sample caveats, style read).",
  "hands": [
     {"n":1, "title":"A♥3♦  —  Big Blind, Level 10", "tag":"CORRECT",
      "setup":"...", "verdict":"..."},
     ...
  ],
  "outfile": "/abs/path/Session_review.pdf"
}

tag ∈ {CORRECT, MINOR NOTE, LEAK, COOLER}.  Write card suits as unicode pips
(♠♥♦♣) directly in the strings; this script colors ♥/♦ red automatically and
uses a font that renders the glyphs.  Requires: reportlab.
"""
import sys, os, json
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---- fonts: find a TTF with the ♠♥♦♣ glyphs ----
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/freefont",
             "/Library/Fonts", "/System/Library/Fonts/Supplemental", "/usr/share/fonts"]
def find_font(names):
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None
reg = find_font(["DejaVuSans.ttf", "FreeSans.ttf", "Arial Unicode.ttf"])
regb = find_font(["DejaVuSans-Bold.ttf", "FreeSansBold.ttf"])
BASE, BOLD = "Helvetica", "Helvetica-Bold"
if reg:
    pdfmetrics.registerFont(TTFont("Deja", reg)); BASE = "Deja"
    if regb:
        pdfmetrics.registerFont(TTFont("Deja-Bold", regb)); BOLD = "Deja-Bold"
    else:
        BOLD = "Deja"

GREEN = colors.HexColor("#1f7a4d"); RED = colors.HexColor("#c0392b")
DARK = colors.HexColor("#1a2330"); MUT = colors.HexColor("#5b6670")
TAGCOL = {"CORRECT": GREEN, "STANDARD": GREEN, "LEAK": RED,
          "COOLER": colors.HexColor("#b8860b"), "MINOR NOTE": colors.HexColor("#b8860b"),
          "NOTE": colors.HexColor("#b8860b")}

styles = getSampleStyleSheet()
def S(name, **kw):
    base = kw.pop("parent", styles["Normal"]); kw.setdefault("fontName", BASE)
    return ParagraphStyle(name, parent=base, **kw)
h_title = S("t", fontName=BOLD, fontSize=21, textColor=DARK, spaceAfter=2, leading=25)
h_sub   = S("s", fontSize=10.5, textColor=MUT, spaceAfter=10, leading=14)
h_hand  = S("h", fontName=BOLD, fontSize=13, textColor=DARK, spaceBefore=13, spaceAfter=2, leading=16)
lbl     = S("l", fontName=BOLD, fontSize=8.5, textColor=MUT, spaceAfter=1, leading=11)
body    = S("b", fontSize=10.5, textColor=colors.HexColor("#20242b"), spaceAfter=6, leading=15)
sec     = S("sec", fontName=BOLD, fontSize=15, textColor=DARK, spaceBefore=6, spaceAfter=8, leading=18)
small   = S("sm", fontSize=8.5, textColor=MUT, spaceBefore=4, leading=12)

def color_pips(t):
    for s in "♥♦":
        t = t.replace(s, f'<font color="#c0392b">{s}</font>')
    return t

def main():
    if len(sys.argv) < 2:
        print("usage: make_pdf.py <spec.json> [out.pdf]"); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2] if len(sys.argv) > 2 else spec.get("outfile", "session_review.pdf")

    doc = SimpleDocTemplate(out, pagesize=letter, topMargin=0.7*inch, bottomMargin=0.7*inch,
                            leftMargin=0.85*inch, rightMargin=0.85*inch,
                            title=spec.get("title", "Session Review"))
    st = []
    st.append(Paragraph(color_pips(spec.get("title", "Session Review")), h_title))
    if spec.get("subtitle"):
        st.append(Paragraph(color_pips(spec["subtitle"]), h_sub))
    st.append(HRFlowable(width="100%", thickness=1.2, color=GREEN, spaceAfter=10))

    if spec.get("summary"):
        st.append(Paragraph("Session Summary", sec))
        st.append(Paragraph(color_pips(spec["summary"]), body))

    if spec.get("stats"):
        t = Table(spec["stats"], colWidths=[1.9*inch, 1.6*inch, 1.7*inch], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,0),BOLD),("FONTNAME",(0,1),(-1,-1),BASE),
            ("FONTSIZE",(0,0),(-1,-1),9.5),
            ("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f1f5f3")]),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#d6dce2")),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),8)]))
        st.append(t)
    if spec.get("stats_note"):
        st.append(Paragraph(color_pips(spec["stats_note"]), small))

    if spec.get("hands"):
        st.append(PageBreak())
        st.append(Paragraph("Hand-by-Hand", sec))
        total = len(spec["hands"])
        for hd in spec["hands"]:
            tg = hd.get("tag", "CORRECT").upper()
            col = TAGCOL.get(tg, GREEN)
            label = {"STANDARD":"CORRECT","NOTE":"MINOR NOTE"}.get(tg, tg)
            n = hd.get("n", "")
            head = f'Hand {n}/{total} — {hd.get("title","")}' if n else hd.get("title","")
            chip = f'  <font face="{BOLD}" color="#{col.hexval()[2:]}">[{label}]</font>'
            st.append(Paragraph(color_pips(head) + chip, h_hand))
            if hd.get("setup"):
                st.append(Paragraph("SETUP &amp; ACTION", lbl))
                st.append(Paragraph(color_pips(hd["setup"]), body))
            if hd.get("verdict"):
                st.append(Paragraph("VERDICT", lbl))
                st.append(Paragraph(color_pips(hd["verdict"]), body))
            st.append(HRFlowable(width="100%", thickness=0.4,
                      color=colors.HexColor("#dde3e8"), spaceBefore=2, spaceAfter=2))

    if spec.get("footer"):
        st.append(Spacer(1, 10)); st.append(Paragraph(color_pips(spec["footer"]), small))
    doc.build(st)
    print("PDF written:", out)

if __name__ == "__main__":
    main()
