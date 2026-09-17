import io
from datetime import datetime
from fpdf import FPDF
import pandas as pd


def clean_ascii(text: str) -> str:
    """Removes or replaces non-ASCII characters that crash standard PDF fonts."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.replace("—", "-")
        .replace("–", "-")
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


class HSEExecutivePDF(FPDF):
    def header(self):
        # Company / Project Banner
        self.set_fill_color(24, 43, 73)  # Dark industrial blue
        self.rect(0, 0, 210, 20, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 14)
        self.set_xy(10, 5)
        self.cell(0, 10, clean_ascii("OIL INDIA - SIF PRECURSOR EXECUTIVE REPORT"), ln=True)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Confidential - For HSE Management Use Only", align="C")


def generate_hse_pdf(df: pd.DataFrame) -> bytes:
    """
    Generates an Executive HSE Summary PDF from the processed dataframe.
    """
    pdf = HSEExecutivePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Metadata Row
    pdf.ln(15)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    timestamp = datetime.now().strftime("%d-%b-%Y %H:%M")
    pdf.cell(0, 6, clean_ascii(f"Generated On: {timestamp} | Scope: Current Operational Reports"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # 1. Executive Summary & KPIs
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 8, "1. Executive Risk Overview", ln=True)

    total_reports = len(df)
    high_sif = int((df["sif"] == "HIGH").sum()) if "sif" in df.columns else 0
    ratio = (high_sif / total_reports * 100) if total_reports > 0 else 0

    # KPI Summary Cards
    kpi_y = pdf.get_y()
    pdf.set_draw_color(210, 215, 225)
    pdf.set_fill_color(245, 247, 250)

    # Card 1: Total Reports
    pdf.rect(10, kpi_y, 60, 18, "FD")
    pdf.set_xy(12, kpi_y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(56, 5, "Total Reports Audited", ln=True)
    pdf.set_x(12)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(56, 7, str(total_reports), ln=True)

    # Card 2: HIGH SIF
    pdf.rect(75, kpi_y, 60, 18, "FD")
    pdf.set_xy(77, kpi_y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(56, 5, "HIGH SIF Precursors", ln=True)
    pdf.set_x(77)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(200, 30, 30)
    pdf.cell(56, 7, str(high_sif), ln=True)

    # Card 3: Density
    pdf.rect(140, kpi_y, 60, 18, "FD")
    pdf.set_xy(142, kpi_y + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(56, 5, "High SIF Density", ln=True)
    pdf.set_x(142)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(200, 30, 30 if ratio > 25 else 24)
    pdf.cell(56, 7, f"{ratio:.1f}%", ln=True)

    pdf.set_xy(10, kpi_y + 22)

    # 2. Site Hotspots (if site column present)
    if "site" in df.columns:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(24, 43, 73)
        pdf.cell(0, 8, "2. High-Risk Site Hotspots", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 5, "Sites ranked by concentration of potential fatal/serious precursors:", ln=True)
        pdf.ln(2)

        hotspot = (
            df.groupby("site")
            .agg(total=("sif", "count"), high=("sif", lambda x: (x == "HIGH").sum()))
            .reset_index()
        )
        hotspot["density"] = (hotspot["high"] / hotspot["total"] * 100).round(1)
        hotspot = hotspot.sort_values("density", ascending=False)

        pdf.set_fill_color(230, 235, 245)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(70, 7, "Operating Site", border=1, fill=True)
        pdf.cell(40, 7, "Total Reports", border=1, align="C", fill=True)
        pdf.cell(40, 7, "High SIF Count", border=1, align="C", fill=True)
        pdf.cell(40, 7, "Risk Density (%)", border=1, align="C", fill=True, ln=True)

        pdf.set_font("Helvetica", "", 9)
        for _, row in hotspot.head(5).iterrows():
            pdf.cell(70, 6, clean_ascii(row["site"]), border=1)
            pdf.cell(40, 6, str(row["total"]), border=1, align="C")
            pdf.cell(40, 6, str(row["high"]), border=1, align="C")
            pdf.cell(40, 6, f"{row['density']}%", border=1, align="C", ln=True)
        pdf.ln(4)

    # 3. Top Triggered Rules
    if "rules" in df.columns:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(24, 43, 73)
        pdf.cell(0, 8, "3. Top Breached / Triggered Life-Saving Rules", ln=True)
        pdf.ln(1)

        rule_counts = df.explode("rules")["rules"].value_counts()
        rule_counts = rule_counts[rule_counts.index != "None"]

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        if not rule_counts.empty:
            for rule, count in rule_counts.head(4).items():
                pdf.cell(8, 5, "-", align="R")
                pdf.cell(0, 5, clean_ascii(f" {rule}: {count} incident(s) flagged"), ln=True)
        else:
            pdf.cell(0, 5, "No specific rules breached in current batch.", ln=True)
        pdf.ln(4)

    # 4. Critical Flagged Reports
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(24, 43, 73)
    pdf.cell(0, 8, "4. Critical Precursor Excerpts (Immediate Action Required)", ln=True)
    pdf.ln(1)

    high_reports = df[df["sif"] == "HIGH"]
    if not high_reports.empty:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 30, 30)
        for _, row in high_reports.head(4).iterrows():
            report_text = row["report"][:160] + ("..." if len(row["report"]) > 160 else "")
            site_info = f"[{row['site']}] " if "site" in row and pd.notna(row["site"]) else ""
            rule_info = f" (Rule: {row.get('rules_str', 'N/A')})"
            
            entry = clean_ascii(f"- {site_info}{report_text}{rule_info}")
            pdf.set_fill_color(255, 243, 243)
            pdf.set_draw_color(230, 180, 180)
            pdf.multi_cell(190, 5, entry, border=1, fill=True)
            pdf.ln(1)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 5, "No HIGH SIF-potential precursors identified in this dataset.", ln=True)

    return bytes(pdf.output(), 'latin-1')