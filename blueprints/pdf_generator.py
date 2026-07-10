import re
import os
import io
from datetime import datetime
from fpdf import FPDF
from flask import current_app


class ResearchPDF(FPDF):
    def __init__(self, topic: str):
        super().__init__()
        self.topic = topic
        self.set_margins(20, 22, 20)
        self.set_auto_page_break(auto=True, margin=22)

    def header(self):
        # Dynamically search and embed the GlobalTechVibers Logo if inside application context
        try:
            logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logo.png')
            if os.path.exists(logo_path):
                # Draw logo at top right of the page header
                self.image(logo_path, x=150, y=7, w=40)
        except Exception:
            pass

        # Reset cursor coordinates to avoid self.image() affecting current self.x margin positioning
        self.set_xy(20, 10)

        self.set_font("Helvetica", "B", 8)
        self.set_text_color(214, 40, 40)  # Brand Primary color (Red #d62828)
        self.cell(170, 5, "GLOBALTECHVIBERS  \u00b7  AI RESEARCH DIVISION", align="L")
        self.ln(4)
        self.set_draw_color(210, 210, 210)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        date_str = datetime.now().strftime("%B %d, %Y")
        self.cell(
            170, 8,
            f"Generated {date_str}  \u00b7  Page {self.page_no()}  \u00b7  globaltechvibers.com",
            align="C",
        )


def _safe(text: str) -> str:
    """Encode text safely for FPDF core fonts (latin-1)."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(topic: str, report_text: str, sources: list = None) -> bytes:
    """Convert a report string into a branded PDF. Returns raw bytes."""
    pdf = ResearchPDF(topic)
    pdf.add_page()

    # Title block
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(170, 11, _safe(topic.title()), align="L")
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(170, 6, f"Research Report  \u00b7  {datetime.now().strftime('%B %d, %Y')}", align="L")
    pdf.ln(8)

    pdf.set_draw_color(210, 210, 210)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)

    # Report body parser
    for line in report_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            pdf.ln(2)
            continue

        if stripped.startswith("## "):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(214, 40, 40)  # Section Headings in Brand Primary Color
            pdf.multi_cell(170, 7, _safe(stripped[3:]), align="L")
            pdf.ln(1)

        elif stripped.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(170, 6, _safe(stripped[4:]), align="L")

        elif stripped.startswith(("- ", "\u2022 ")):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(170, 6, _safe("\u2022  " + stripped[2:]), align="L")

        else:
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", stripped)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(170, 6, _safe(clean), align="L")

    # Sources Bibliography
    if sources:
        pdf.ln(8)
        pdf.set_draw_color(210, 210, 210)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(6)

        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(214, 40, 40)
        pdf.cell(170, 7, "Sources", align="L")
        pdf.ln(9)

        for i, src in enumerate(sources[:8], 1):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(170, 5, _safe(f"{i}. {src['title']}"), align="L")

            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(60, 100, 180)
            pdf.multi_cell(170, 5, _safe(src["url"]), align="L")
            pdf.ln(3)

    return bytes(pdf.output())
