#!/usr/bin/env python3
"""Generate realistic medical documents for 20 test cases.
Produces properly structured PDFs and PNGs that closely match
real Indian medical documents — prescriptions, hospital bills,
lab reports, and pharmacy bills with proper tables and formatting.

Usage:
    uv run python documents/generate_documents.py
"""

from __future__ import annotations

import json
import math
import random
from datetime import date
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent

# Colors
PRIMARY = (25, 25, 112)      # Dark blue for headers
SECONDARY = (60, 60, 60)     # Dark gray for body
ACCENT = (0, 102, 204)       # Blue accent
LIGHT_BG = (250, 250, 255)   # Very light blue bg
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (180, 30, 30)
GRAY = (150, 150, 150)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (80, 80, 80)

# ── Font Setup ────────────────────────────────────────────────────

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REGULAR = f"{FONT_DIR}/DejaVuSans.ttf"
FONT_BOLD = f"{FONT_DIR}/DejaVuSans-Bold.ttf"
FONT_MONO = f"{FONT_DIR}/DejaVuSansMono.ttf"

def _load_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        path = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REGULAR)
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


# ── PDF Helpers ───────────────────────────────────────────────────

class DocPDF(FPDF):
    """Base PDF with Unicode support."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=12)
        self.set_left_margin(15)
        self.set_right_margin(15)
        # Register DejaVu fonts for Unicode
        for style, path in [("", FONT_REGULAR), ("B", FONT_BOLD)]:
            self.add_font("DejaVu", style, path)
        self._row_h = 6.5
        self._col = 0  # current column for grid layout

    def hdr(self, text: str, size: int = 16):
        """Large bold header."""
        self.set_font("DejaVu", "B", size)
        self.set_text_color(*PRIMARY)
        self.cell(w=0, h=self._row_h + 2, text=text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*SECONDARY)

    def sub(self, text: str, size: int = 10):
        """Sub-header or detail line."""
        self.set_font("DejaVu", "", size)
        self.set_text_color(*SECONDARY)
        self.cell(w=0, h=self._row_h, text=text, new_x="LMARGIN", new_y="NEXT")

    def rule(self, char: str = "-"):
        """Horizontal separator line."""
        self.sub(char * 75, size=8)
        self.set_text_color(*SECONDARY)

    def label(self, left: str, right: str = "", size: int = 10):
        """Left label + right value on same line."""
        self.set_font("DejaVu", "B", size)
        self.set_text_color(*DARK_GRAY)
        w = self.w - self.l_margin - self.r_margin
        self.cell(w=w * 0.4, h=self._row_h, text=left)
        self.set_font("DejaVu", "", size)
        self.set_text_color(*SECONDARY)
        self.cell(w=w * 0.6, h=self._row_h, text=str(right), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*SECONDARY)

    def section(self, title: str):
        """Section header with underline."""
        self.ln(2)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*PRIMARY)
        self.cell(w=0, h=self._row_h + 2, text=title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*ACCENT)
        y = self.get_y()
        self.line(15, y, self.w - 15, y)
        self.ln(1)
        self.set_text_color(*SECONDARY)

    def table_header(self, cols: list[tuple[str, float]]):
        """Draw a table header row. cols = [(label, width_ratio), ...]."""
        self.set_font("DejaVu", "B", 9)
        self.set_fill_color(230, 235, 245)
        self.set_draw_color(*LIGHT_GRAY)
        w = self.w - self.l_margin - self.r_margin
        for label, ratio in cols:
            self.cell(w=w * ratio, h=self._row_h + 2, text=label, border=1, fill=True)
        self.ln()

    def table_row(self, cols: list[tuple[str, float]], bold: bool = False):
        """Draw a data row."""
        self.set_font("DejaVu", "B" if bold else "", 9)
        self.set_draw_color(*LIGHT_GRAY)
        w = self.w - self.l_margin - self.r_margin
        for text, ratio in cols:
            self.cell(w=w * ratio, h=self._row_h + 2, text=str(text), border=1)
        self.ln()

    def body_text(self, text: str, size: int = 10):
        """Regular paragraph text with line wrapping."""
        self.set_font("DejaVu", "", size)
        w = self.w - self.l_margin - self.r_margin
        self.multi_cell(w=w, h=self._row_h, text=text)

    def rx_item(self, num: int, text: str):
        """Numbered prescription item with Rx symbol."""
        self.set_font("DejaVu", "", 10)
        w = self.w - self.l_margin - self.r_margin
        self.cell(w=8, h=self._row_h + 1, text=f"{num}.")
        self.cell(w=w - 8, h=self._row_h + 1, text=text, new_x="LMARGIN", new_y="NEXT")


class PNGCanvas(DocPDF):
    """PDF subclass that also renders to PNG using Pillow."""

    def __init__(self):
        super().__init__()
        self._img = Image.new("RGB", (800, 1200), "white")
        self._draw = ImageDraw.Draw(self._img)
        self._y = 25
        self._x = 30
        self._img_w = 800

    # Override row_h to be larger for PNG
    @property
    def _row_h(self):
        return getattr(self, '_png_row_h', 7.5)

    @_row_h.setter
    def _row_h(self, val):
        self._png_row_h = val

    def finish_page(self):
        """Complete current page rendering."""
        pass

    def _img_line(self, x1, y1, x2, y2, color=BLACK, width=1):
        self._draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def _img_rect(self, x, y, w, h, fill=None, outline=None):
        if fill:
            self._draw.rectangle([x, y, x + w, y + h], fill=fill, outline=outline)
        else:
            self._draw.rectangle([x, y, x + w, y + h], outline=outline)

    def _img_text(self, x, y, text, size=12, bold=False, color=SECONDARY, mono=False):
        font = _load_font(size, bold=bold, mono=mono)
        self._draw.text((x, y), text, fill=color, font=font)

    def _img_text_right(self, x_end, y, text, size=12, bold=False, color=SECONDARY):
        font = _load_font(size, bold=bold)
        bbox = self._draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        self._draw.text((x_end - w, y), text, fill=color, font=font)

    def _img_multi_text(self, x, y, text, size=10, bold=False, color=SECONDARY, max_w=740):
        font = _load_font(size, bold=bold)
        words = text.split()
        lines = []
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            bbox = self._draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_w:
                lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)
        for ln in lines:
            self._draw.text((x, self._y), ln, fill=color, font=font)
            self._y += size * 1.3
        return len(lines)

    def _img_table(self, x, y, rows: list[list[str]], col_widths: list[int],
                   header: bool = True, font_size: int = 10):
        """Draw a proper table with borders and header."""
        bold_font = _load_font(font_size, bold=True)
        font = _load_font(font_size)
        row_h = int(font_size * 2.2)
        cy = y

        for row_idx, row_data in enumerate(rows):
            cx = x
            is_header = header and row_idx == 0

            if is_header:
                # Draw header background
                self._img_rect(x, cy, sum(col_widths), row_h, fill=(230, 235, 245))

            for col_idx, cell_text in enumerate(row_data):
                cw = col_widths[col_idx]
                # Draw cell border
                self._img_rect(cx, cy, cw, row_h, outline=LIGHT_GRAY)
                # Draw text
                f = bold_font if is_header else font
                self._draw.text((cx + 4, cy + 2), str(cell_text), fill=PRIMARY if is_header else SECONDARY, font=f)
                cx += cw

            cy += row_h

        return cy

    def save_png(self, path: Path):
        """Crop and save the rendered image."""
        h = min(self._y + 30, 2000)
        self._img = self._img.crop((0, 0, 800, h))
        self._img.save(str(path), "PNG")


# ── PDF Generation ────────────────────────────────────────────────

def _new_doc() -> DocPDF:
    return DocPDF()


def _new_png() -> PNGCanvas:
    return PNGCanvas()


def _save_pdf(doc: DocPDF, path: Path):
    doc.output(str(path))


# ── Document Builders ─────────────────────────────────────────────

def build_prescription_pdf(
    doctor_name: str,
    doctor_reg: str,
    doctor_qual: str,
    clinic_name: str,
    clinic_addr: str,
    clinic_phone: str,
    patient_name: str,
    patient_age: int,
    patient_gender: str,
    visit_date: str,
    chief_complaint: str,
    vitals: str,
    diagnosis: str,
    medicines: list[dict],
    tests_ordered: list[str],
    follow_up: str,
    additional_notes: str = "",
) -> DocPDF:
    """Build a realistic Indian prescription."""

    doc = _new_doc()
    doc.add_page()
    w = doc.w - doc.l_margin - doc.r_margin

    # ── Clinic Header ──
    doc.hdr(clinic_name.upper(), size=14)
    doc.sub(f"{doctor_name}, {doctor_qual}")
    doc.sub(f"Reg. No: {doctor_reg}")
    doc.sub(clinic_addr)
    doc.sub(f"Ph: {clinic_phone}")
    doc.rule("=")

    # ── Patient Info ──
    doc.sub(f"Patient: {patient_name}          Age: {patient_age} years   Gender: {patient_gender}")
    doc.sub(f"Date: {visit_date}                                    Patient ID: {_gen_id(patient_name)}")
    doc.sub(f"Chief Complaint: {chief_complaint}")

    if vitals:
        doc.sub(f"Vitals: {vitals}")
    doc.rule()

    # ── Diagnosis ──
    doc.section("DIAGNOSIS")
    doc.sub(f"  Primary: {diagnosis}", size=11)

    # ── Prescription ──
    doc.section("Rx")
    for i, med in enumerate(medicines, 1):
        name = med.get("name", "")
        dosage = med.get("dosage", "")
        duration = med.get("duration", "")
        instructions = med.get("instructions", "")
        line = f"{name} — {dosage}"
        if duration:
            line += f" x {duration}"
        if instructions:
            line += f"   [{instructions}]"
        doc.rx_item(i, line)

    # ── Investigations ──
    if tests_ordered:
        doc.section("INVESTIGATIONS")
        for test in tests_ordered:
            doc.sub(f"  - {test}")

    # ── Follow-up ──
    doc.ln(3)
    doc.sub(f"Follow-up: {follow_up}")

    if additional_notes:
        doc.sub(additional_notes)

    # ── Signature block ──
    doc.ln(8)
    doc.sub("_" * 40)
    doc.sub(f"{doctor_name}")
    doc.sub(f"{doctor_qual}, Reg. {doctor_reg}")
    doc.sub("[Signature & Round Stamp]")

    return doc


def build_hospital_bill_pdf(
    hospital_name: str,
    hospital_addr: str,
    hospital_phone: str,
    gstin: str,
    bill_no: str,
    bill_date: str,
    patient_name: str,
    patient_age: int,
    patient_gender: str,
    ref_doctor: str,
    line_items: list[dict],
    payment_mode: str = "Cash / UPI / Card",
) -> DocPDF:
    """Build a realistic hospital bill with itemized line items."""

    doc = _new_doc()
    doc.add_page()

    # ── Hospital Header ──
    doc.hdr(hospital_name.upper(), size=14)
    doc.sub(hospital_addr)
    if gstin:
        doc.sub(f"GSTIN: {gstin}")
    doc.sub(f"Ph: {hospital_phone}")
    doc.rule("=")

    # ── Bill Info ──
    doc.section("BILL / INVOICE")
    doc.label("Bill No:", bill_no)
    doc.label("Date:", bill_date)
    doc.rule()

    # ── Patient Info ──
    doc.label("Patient Name:", patient_name)
    doc.label("Age / Gender:", f"{patient_age} / {patient_gender}")
    doc.label("Referring Doctor:", ref_doctor)
    doc.rule()

    # ── Line Items Table ──
    doc.ln(2)
    col_def = [
        ("Sr.", 0.06),
        ("Description", 0.40),
        ("Qty", 0.08),
        ("Rate (Rs.)", 0.15),
        ("Amount (Rs.)", 0.15),
        ("GST %", 0.08),
        ("Total (Rs.)", 0.08),
    ]
    doc.table_header(col_def)

    subtotal = 0.0
    for i, item in enumerate(line_items, 1):
        desc = item.get("description", "")
        qty = item.get("quantity", 1)
        rate = item.get("rate", 0)
        amount = qty * rate
        gst_pct = item.get("gst_pct", 0)
        total = amount * (1 + gst_pct / 100)
        subtotal += total
        doc.table_row([
            (str(i), 0.06),
            (desc, 0.40),
            (str(qty), 0.08),
            (f"{rate:,.2f}", 0.15),
            (f"{amount:,.2f}", 0.15),
            (f"{gst_pct}%", 0.08),
            (f"{total:,.2f}", 0.08),
        ])

    # ── Totals ──
    gst_total = sum(
        item.get("rate", 0) * item.get("quantity", 1) * item.get("gst_pct", 0) / 100
        for item in line_items
    )
    doc.ln(1)
    doc.table_header([("", 0.60), ("Amount (Rs.)", 0.40)])
    doc.table_row([("Subtotal", 0.60), (f"Rs. {subtotal:,.2f}", 0.40)])
    doc.table_row([(f"Total GST", 0.60), (f"Rs. {gst_total:,.2f}", 0.40)])
    doc.table_row([("GRAND TOTAL", 0.60), (f"Rs. {subtotal:,.2f}", 0.40)], bold=True)

    # ── Amount in words ──
    doc.ln(2)
    doc.sub(f"Amount in words: {_num_to_words(int(subtotal))} only")

    doc.rule("-")
    doc.sub(f"Payment Mode: {payment_mode}")
    doc.sub(f"Received by: [Cashier]    [Authorized Stamp]")

    return doc


def build_lab_report_pdf(
    lab_name: str,
    lab_address: str,
    lab_accreditation: str,
    lab_id: str,
    patient_name: str,
    patient_age: int,
    patient_gender: str,
    ref_doctor: str,
    sample_date: str,
    report_date: str,
    sample_id: str,
    test_groups: list[dict],
    remarks: str,
    pathologist_name: str = "",
    pathologist_reg: str = "",
) -> DocPDF:
    """Build a realistic diagnostic lab report with test result tables."""

    doc = _new_doc()
    doc.add_page()

    # ── Lab Header ──
    doc.hdr(lab_name.upper(), size=14)
    if lab_accreditation:
        doc.sub(f"{lab_accreditation}   |   Lab ID: {lab_id}")
    doc.sub(lab_address)
    doc.rule("=")

    # ── Patient & Sample Info ──
    doc.section("PATIENT DETAILS")
    doc.label("Patient Name:", patient_name)
    doc.label("Age / Gender:", f"{patient_age} / {patient_gender}")
    doc.label("Referring Doctor:", ref_doctor)
    doc.label("Sample Date:", sample_date)
    doc.label("Report Date:", report_date)
    doc.label("Sample ID:", sample_id)
    doc.rule()

    # ── Test Results Tables ──
    for group in test_groups:
        group_name = group.get("group_name", "")
        tests = group.get("tests", [])

        if group_name:
            doc.section(group_name.upper())

        col_def = [
            ("Test Name", 0.25),
            ("Result", 0.15),
            ("Unit", 0.12),
            ("Normal Range", 0.28),
            ("Flag", 0.10),
            ("Method", 0.10),
        ]
        doc.table_header(col_def)

        for test in tests:
            flag = test.get("flag", "")
            flag_color = ""
            col_data = [
                (test.get("name", ""), 0.25),
                (str(test.get("result", "")), 0.15),
                (test.get("unit", ""), 0.12),
                (test.get("normal_range", ""), 0.28),
                (flag, 0.10),
                (test.get("method", ""), 0.10),
            ]
            doc.table_row(col_data)

        doc.ln(2)

    # ── Remarks ──
    doc.section("REMARKS")
    doc.body_text(remarks)
    doc.ln(2)

    if pathologist_name:
        doc.sub("_" * 40)
        doc.sub(f"{pathologist_name}")
        if pathologist_reg:
            doc.sub(f"Reg. No: {pathologist_reg}")
        doc.sub("[Signature & Stamp]")

    return doc


def build_pharmacy_bill_pdf(
    pharmacy_name: str,
    pharmacy_addr: str,
    drug_lic_no: str,
    bill_no: str,
    bill_date: str,
    patient_name: str,
    prescribing_doctor: str,
    medicines: list[dict],
    discount_pct: float = 0,
    pharmacist_name: str = "",
) -> DocPDF:
    """Build a realistic pharmacy bill with batch numbers and expiry."""

    doc = _new_doc()
    doc.add_page()

    # ── Pharmacy Header ──
    doc.hdr(pharmacy_name.upper(), size=14)
    doc.sub(f"Drug Lic. No: {drug_lic_no}")
    doc.sub(pharmacy_addr)
    doc.rule("=")

    # ── Bill Info ──
    doc.label("Bill No:", bill_no)
    doc.label("Date:", bill_date)
    doc.label("Patient:", patient_name)
    doc.label("Prescribing Doctor:", prescribing_doctor)
    doc.rule()

    # ── Medicines Table ──
    doc.ln(2)
    col_def = [
        ("Sr.", 0.05),
        ("Medicine / Description", 0.28),
        ("Batch No.", 0.12),
        ("Expiry", 0.10),
        ("Qty", 0.07),
        ("MRP (Rs.)", 0.10),
        ("Rate (Rs.)", 0.10),
        ("Amount (Rs.)", 0.10),
        ("GST %", 0.08),
    ]
    doc.table_header(col_def)

    total = 0.0
    for i, med in enumerate(medicines, 1):
        qty = med.get("quantity", 1)
        mrp = med.get("mrp", 0)
        rate = med.get("rate", mrp)
        amount = qty * rate
        gst_pct = med.get("gst_pct", 12)
        total_before_discount = amount * (1 + gst_pct / 100)
        total += total_before_discount
        doc.table_row([
            (str(i), 0.05),
            (med.get("name", ""), 0.28),
            (med.get("batch", ""), 0.12),
            (med.get("expiry", ""), 0.10),
            (str(qty), 0.07),
            (f"{mrp:,.2f}", 0.10),
            (f"{rate:,.2f}", 0.10),
            (f"{amount:,.2f}", 0.10),
            (f"{gst_pct}%", 0.08),
        ])

    # ── Totals ──
    discount_amt = total * discount_pct / 100
    net = total - discount_amt

    doc.ln(1)
    doc.table_header([("", 0.60), ("Amount (Rs.)", 0.40)])
    doc.table_row([("Subtotal", 0.60), (f"Rs. {total:,.2f}", 0.40)])
    if discount_pct > 0:
        doc.table_row([(f"Discount ({discount_pct}%)", 0.60), (f"Rs. -{discount_amt:,.2f}", 0.40)])
    doc.table_row([("NET AMOUNT", 0.60), (f"Rs. {net:,.2f}", 0.40)], bold=True)

    doc.ln(3)
    doc.sub(f"Amount in words: {_num_to_words(int(net))} only")
    doc.rule("-")

    if pharmacist_name:
        doc.sub(f"Dispensed by: {pharmacist_name}    [Stamp]")

    return doc


# ── PNG Builders ──────────────────────────────────────────────────

def build_prescription_png(
    doctor_name, doctor_reg, doctor_qual, clinic_name, clinic_addr,
    clinic_phone, patient_name, patient_age, patient_gender,
    visit_date, chief_complaint, vitals, diagnosis, medicines,
    tests_ordered, follow_up, additional_notes="",
) -> PNGCanvas:
    """Build a realistic prescription as PNG image."""

    img = _new_png()
    img._y = 20
    mx = 30
    mw = 740
    row_h = 22

    # ── Top Header Box ──
    y0 = img._y
    img._img_rect(mx, y0, mw, 85, fill=(245, 248, 255), outline=ACCENT)
    img._img_text(mx + 15, y0 + 8, clinic_name.upper(), size=16, bold=True, color=PRIMARY)
    img._img_text(mx + 15, y0 + 28, f"{doctor_name}, {doctor_qual}", size=11, color=DARK_GRAY)
    img._img_text(mx + 15, y0 + 42, f"Reg. No: {doctor_reg}", size=10, color=DARK_GRAY)
    img._img_text(mx + 15, y0 + 56, clinic_addr, size=9, color=GRAY)
    img._img_text(mx + 15, y0 + 70, f"Ph: {clinic_phone}", size=9, color=GRAY)

    # ── Separator ──
    img._y = y0 + 95
    img._img_line(mx, img._y, mx + mw, img._y, color=ACCENT, width=2)
    img._y += 5

    # ── Patient Info Box ──
    y1 = img._y
    img._img_rect(mx, y1, mw, 52, fill=None, outline=LIGHT_GRAY)
    img._img_text(mx + 10, y1 + 6, f"Patient: {patient_name}", size=11, bold=True, color=DARK_GRAY)
    img._img_text(mx + 10, y1 + 22, f"Age: {patient_age} yrs   Gender: {patient_gender}   Date: {visit_date}", size=10, color=SECONDARY)
    img._img_text(mx + 10, y1 + 36, f"Chief Complaint: {chief_complaint}", size=10, color=SECONDARY)
    if vitals:
        img._img_text(mx + 10, y1 + 50, f"Vitals: {vitals}", size=9, color=GRAY)
    img._y = y1 + 60

    # ── Diagnosis ──
    img._img_line(mx, img._y, mx + mw, img._y, color=ACCENT, width=1)
    img._y += 8
    img._img_text(mx, img._y, "DIAGNOSIS:", size=12, bold=True, color=PRIMARY)
    img._y += row_h
    img._img_text(mx + 10, img._y, diagnosis, size=11, bold=True, color=BLACK)
    img._y += row_h + 4

    # ── Rx ──
    img._img_line(mx, img._y, mx + mw, img._y, color=ACCENT, width=1)
    img._y += 8
    img._img_text(mx, img._y, "Rx", size=14, bold=True, color=RED)
    img._y += row_h + 4

    for i, med in enumerate(medicines, 1):
        name = med.get("name", "")
        dosage = med.get("dosage", "")
        duration = med.get("duration", "")
        instructions = med.get("instructions", "")
        line = f"{i}.  {name}  -  {dosage}"
        if duration:
            line += f"  x  {duration}"
        img._img_text(mx + 15, img._y, line, size=10, color=SECONDARY)
        img._y += 18
        if instructions:
            img._img_text(mx + 25, img._y, f"({instructions})", size=9, color=GRAY)
            img._y += 16

    # ── Investigations ──
    if tests_ordered:
        img._y += 4
        img._img_line(mx, img._y, mx + mw, img._y, color=LIGHT_GRAY, width=1)
        img._y += 6
        img._img_text(mx, img._y, "INVESTIGATIONS:", size=11, bold=True, color=PRIMARY)
        img._y += row_h
        for test in tests_ordered:
            img._img_text(mx + 15, img._y, f"- {test}", size=10, color=SECONDARY)
            img._y += 18

    # ── Follow-up ──
    img._y += 8
    img._img_line(mx, img._y, mx + mw, img._y, color=LIGHT_GRAY, width=1)
    img._y += 6
    img._img_text(mx, img._y, f"Follow-up: {follow_up}", size=10, color=SECONDARY)
    if additional_notes:
        img._y += 18
        img._img_text(mx, img._y, additional_notes, size=9, color=GRAY)

    # ── Signature Block ──
    img._y += 30
    img._img_text_right(mx + mw, img._y, f"{doctor_name}", size=10, bold=True, color=DARK_GRAY)
    img._y += 16
    img._img_text_right(mx + mw, img._y, f"{doctor_qual}", size=9, color=GRAY)
    img._y += 14
    img._img_text_right(mx + mw, img._y, f"Reg. {doctor_reg}", size=9, color=GRAY)
    img._y += 18
    img._img_text_right(mx + mw, img._y, "[Signature & Round Seal]", size=9, color=GRAY)

    return img


def build_hospital_bill_png(
    hospital_name, hospital_addr, hospital_phone, gstin, bill_no,
    bill_date, patient_name, patient_age, patient_gender,
    ref_doctor, line_items, payment_mode="Cash / UPI / Card",
) -> PNGCanvas:
    """Build hospital bill as PNG with proper table."""

    img = _new_png()
    img._y = 20
    mx = 30
    mw = 740

    # ── Hospital Header ──
    y0 = img._y
    img._img_rect(mx, y0, mw, 70, fill=(245, 248, 255), outline=ACCENT)
    img._img_text(mx + 15, y0 + 8, hospital_name.upper(), size=16, bold=True, color=PRIMARY)
    img._img_text(mx + 15, y0 + 28, hospital_addr, size=10, color=DARK_GRAY)
    if gstin:
        img._img_text(mx + 15, y0 + 42, f"GSTIN: {gstin}", size=10, color=DARK_GRAY)
    img._img_text(mx + 15, y0 + 56, f"Ph: {hospital_phone}", size=9, color=GRAY)

    img._y = y0 + 80

    # ── Bill Header Box ──
    y1 = img._y
    img._img_rect(mx, y1, mw, 55, fill=None, outline=LIGHT_GRAY)
    img._img_text(mx + 10, y1 + 6, "BILL / RECEIPT", size=13, bold=True, color=PRIMARY)
    img._img_text(mx + 10, y1 + 24, f"Bill No: {bill_no}", size=10, bold=True, color=DARK_GRAY)
    img._img_text(mx + 360, y1 + 24, f"Date: {bill_date}", size=10, bold=True, color=DARK_GRAY)
    img._y = y1 + 60

    # ── Patient Info ──
    img._img_text(mx, img._y, f"Patient Name: {patient_name}", size=11, bold=True, color=DARK_GRAY)
    img._y += 18
    img._img_text(mx, img._y, f"Age/Gender: {patient_age} / {patient_gender}       Referring Doctor: {ref_doctor}", size=10, color=SECONDARY)
    img._y += 25

    # ── Line Items Table ──
    col_widths = [30, 280, 45, 85, 100, 55, 85]
    headers = ["Sr.", "Description", "Qty", "Rate", "Amount", "GST%", "Total"]
    rows = [headers]
    subtotal = 0.0
    for i, item in enumerate(line_items, 1):
        qty = item.get("quantity", 1)
        rate = item.get("rate", 0)
        amt = qty * rate
        gst = item.get("gst_pct", 0)
        tot = amt * (1 + gst / 100)
        subtotal += tot
        rows.append([
            str(i),
            item.get("description", ""),
            str(qty),
            f"{rate:,.2f}",
            f"{amt:,.2f}",
            f"{gst}%",
            f"{tot:,.2f}",
        ])

    img._y = img._img_table(mx, img._y, rows, col_widths, header=True)

    # ── Totals ──
    img._y += 5
    total_cols = [500, 85]
    img._img_table(mx + 30, img._y, [
        ["Subtotal", f"Rs. {subtotal:,.2f}"],
        ["GRAND TOTAL", f"Rs. {subtotal:,.2f}"],
    ], total_cols, header=False)
    img._y += 55

    # ── Amount in words ──
    img._img_text(mx, img._y, f"Amount in words: {_num_to_words(int(subtotal))} only", size=9, color=GRAY)
    img._y += 25

    # ── Footer ──
    img._img_line(mx, img._y, mx + mw, img._y, color=LIGHT_GRAY, width=1)
    img._y += 8
    img._img_text(mx, img._y, f"Payment Mode: {payment_mode}                              Received by: [Cashier Signature & Stamp]",
                  size=9, color=GRAY)

    return img


def build_lab_report_png(
    lab_name, lab_address, lab_accreditation, lab_id,
    patient_name, patient_age, patient_gender, ref_doctor,
    sample_date, report_date, sample_id, test_groups,
    remarks, pathologist_name="", pathologist_reg="",
) -> PNGCanvas:
    """Build lab report as PNG with proper test result tables."""

    img = _new_png()
    img._y = 20
    mx = 30
    mw = 740

    # ── Lab Header ──
    y0 = img._y
    img._img_rect(mx, y0, mw, 60, fill=(245, 248, 255), outline=ACCENT)
    img._img_text(mx + 15, y0 + 8, lab_name.upper(), size=16, bold=True, color=PRIMARY)
    if lab_accreditation:
        img._img_text(mx + 15, y0 + 28, f"{lab_accreditation}   |   Lab ID: {lab_id}", size=10, color=DARK_GRAY)
    img._img_text(mx + 15, y0 + 44, lab_address, size=9, color=GRAY)
    img._y = y0 + 70

    # ── Patient Info ──
    img._img_text(mx, img._y, "PATIENT DETAILS", size=12, bold=True, color=PRIMARY)
    img._y += 20
    img._img_rect(mx, img._y, mw, 55, fill=None, outline=LIGHT_GRAY)
    pi_x = mx + 10
    pi_y = img._y + 6
    img._img_text(pi_x, pi_y, f"Patient: {patient_name}     Age/Gender: {patient_age} / {patient_gender}",
                  size=10, color=DARK_GRAY)
    img._img_text(pi_x, pi_y + 18, f"Ref Doctor: {ref_doctor}", size=10, color=DARK_GRAY)
    img._img_text(pi_x, pi_y + 32, f"Sample Date: {sample_date}     Report Date: {report_date}     Sample ID: {sample_id}",
                  size=10, color=SECONDARY)
    img._y += 65

    # ── Test Result Tables ──
    for group in test_groups:
        group_name = group.get("group_name", "")
        tests = group.get("tests", [])

        if group_name:
            img._y += 5
            img._img_line(mx, img._y, mx + mw, img._y, color=ACCENT, width=1)
            img._y += 6
            img._img_text(mx, img._y, group_name.upper(), size=12, bold=True, color=PRIMARY)
            img._y += 22

        col_widths = [180, 90, 70, 160, 55, 110]
        headers = ["Test Name", "Result", "Unit", "Normal Range", "Flag", "Method"]
        rows = [headers]
        for t in tests:
            rows.append([
                t.get("name", ""),
                str(t.get("result", "")),
                t.get("unit", ""),
                t.get("normal_range", ""),
                t.get("flag", ""),
                t.get("method", ""),
            ])

        img._y = img._img_table(mx, img._y, rows, col_widths, header=True)
        img._y += 8

    # ── Remarks ──
    img._y += 5
    img._img_line(mx, img._y, mx + mw, img._y, color=LIGHT_GRAY, width=1)
    img._y += 8
    img._img_text(mx, img._y, "REMARKS:", size=11, bold=True, color=DARK_GRAY)
    img._y += 20
    img._img_text(mx + 5, img._y, remarks, size=10, color=SECONDARY)
    img._y += 25

    # ── Signature ──
    if pathologist_name:
        img._y += 20
        img._img_text_right(mx + mw, img._y, f"{pathologist_name}", size=10, bold=True, color=DARK_GRAY)
        img._y += 16
        if pathologist_reg:
            img._img_text_right(mx + mw, img._y, f"Reg. No: {pathologist_reg}", size=9, color=GRAY)
        img._y += 14
        img._img_text_right(mx + mw, img._y, "[Signature & Stamp]", size=9, color=GRAY)

    return img


def build_pharmacy_bill_png(
    pharmacy_name, pharmacy_addr, drug_lic_no, bill_no, bill_date,
    patient_name, prescribing_doctor, medicines, discount_pct=0,
    pharmacist_name="",
) -> PNGCanvas:
    """Build pharmacy bill as PNG."""

    img = _new_png()
    img._y = 20
    mx = 30
    mw = 740

    # ── Header ──
    y0 = img._y
    img._img_rect(mx, y0, mw, 60, fill=(245, 248, 255), outline=ACCENT)
    img._img_text(mx + 15, y0 + 8, pharmacy_name.upper(), size=16, bold=True, color=PRIMARY)
    img._img_text(mx + 15, y0 + 28, f"Drug Lic. No: {drug_lic_no}", size=10, color=DARK_GRAY)
    img._img_text(mx + 15, y0 + 44, pharmacy_addr, size=9, color=GRAY)
    img._y = y0 + 70

    # ── Bill Info ──
    img._img_text(mx, img._y, f"Bill No: {bill_no}                               Date: {bill_date}", size=11, bold=True, color=DARK_GRAY)
    img._y += 20
    img._img_text(mx, img._y, f"Patient: {patient_name}                           Dr: {prescribing_doctor}", size=10, color=SECONDARY)
    img._y += 28

    # ── Medicines Table ──
    col_widths = [25, 170, 70, 60, 40, 70, 70, 75, 50]
    headers = ["Sr.", "Medicine", "Batch No.", "Expiry", "Qty", "MRP", "Rate", "Amount", "GST%"]
    rows = [headers]

    total = 0.0
    for i, med in enumerate(medicines, 1):
        qty = med.get("quantity", 1)
        mrp = med.get("mrp", 0)
        rate = med.get("rate", mrp)
        amt = qty * rate
        gst = med.get("gst_pct", 12)
        tot = amt * (1 + gst / 100)
        total += tot
        rows.append([
            str(i),
            med.get("name", ""),
            med.get("batch", ""),
            med.get("expiry", ""),
            str(qty),
            f"{mrp:,.2f}",
            f"{rate:,.2f}",
            f"{amt:,.2f}",
            f"{gst}%",
        ])

    img._y = img._img_table(mx, img._y, rows, col_widths, header=True)

    # ── Totals ──
    discount_amt = total * discount_pct / 100
    net = total - discount_amt
    img._y += 5
    tot_cols = [500, 85]
    tot_rows = [["Subtotal", f"Rs. {total:,.2f}"]]
    if discount_pct > 0:
        tot_rows.append([f"Discount ({discount_pct}%)", f"Rs. -{discount_amt:,.2f}"])
    tot_rows.append(["NET AMOUNT", f"Rs. {net:,.2f}"])
    img._img_table(mx + 30, img._y, tot_rows, tot_cols, header=False)
    img._y += 60

    img._img_text(mx, img._y, f"Amount in words: {_num_to_words(int(net))} only", size=9, color=GRAY)
    img._y += 25

    img._img_line(mx, img._y, mx + mw, img._y, color=LIGHT_GRAY, width=1)
    img._y += 8
    if pharmacist_name:
        img._img_text(mx, img._y, f"Dispensed by: {pharmacist_name}    [Stamp]", size=9, color=GRAY)

    return img


# ── Test Case Data ────────────────────────────────────────────────

def _gen_id(name: str) -> str:
    return f"{name[:3].upper()}-{random.randint(10000,99999)}"

def _rand_batch() -> str:
    return f"{chr(65+random.randint(0,25))}{random.randint(1000,9999)}"

def _rand_expiry() -> str:
    m = random.randint(1, 12)
    y = random.randint(26, 29)
    return f"{m:02d}/20{y}"

def _num_to_words(n: int) -> str:
    """Convert number to Indian number words."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    if n == 0:
        return "Zero"
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
    if n < 1000:
        return ones[n // 100] + " Hundred" + (" " + _num_to_words(n % 100) if n % 100 else "")
    if n < 100000:
        return _num_to_words(n // 1000) + " Thousand" + (" " + _num_to_words(n % 1000) if n % 1000 else "")
    return _num_to_words(n // 100000) + " Lakh" + (" " + _num_to_words(n % 100000) if n % 100000 else "")


# ── Case Definitions ──────────────────────────────────────────────

PASSING_CASES = [
    {
        "id": "case1",
        "name": "Clean Consultation — Viral Fever",
        "member": "EMP001", "category": "CONSULTATION", "amount": 1500,
        "treatment_date": "2024-11-01",
        "hospital": "City Medical Centre", "gstin": "29AABCT1234A1ZX",
        "doctor": "Dr. Arun Sharma", "reg": "KA/45678/2015",
        "doctor_qual": "MBBS, MD (Internal Medicine)",
        "clinic_addr": "12 MG Road, Bengaluru - 560001",
        "clinic_phone": "+91-80-2345-6789",
        "patient": "Rajesh Kumar", "patient_age": 39, "patient_gender": "Male",
        "chief_complaint": "Fever since 3 days, body ache, mild headache",
        "vitals": "BP: 120/80 mmHg, Temp: 101.2 F, Pulse: 88/min",
        "diagnosis": "Viral Fever (Acute Febrile Illness)",
        "medicines": [
            {"name": "Tab. Paracetamol (Dolo 650) 650mg", "dosage": "1-1-1", "duration": "5 days", "instructions": "After food"},
            {"name": "Tab. Vitamin C (Limcee) 500mg", "dosage": "0-0-1", "duration": "7 days", "instructions": "After food"},
            {"name": "Tab. Cetirizine 10mg", "dosage": "0-1-0", "duration": "5 days", "instructions": "At bedtime, for nasal congestion"},
        ],
        "tests_ordered": ["CBC (Complete Blood Count)", "Dengue NS1 Antigen", "CRP (C-Reactive Protein)"],
        "follow_up": "After 5 days if fever persists, or earlier if symptoms worsen",
        "line_items": [
            {"description": "Consultation Fee (OPD)", "quantity": 1, "rate": 1000, "gst_pct": 0},
            {"description": "CBC (Complete Blood Count)", "quantity": 1, "rate": 300, "gst_pct": 0},
            {"description": "Dengue NS1 Antigen Test", "quantity": 1, "rate": 200, "gst_pct": 0},
        ],
    },
    {
        "id": "case2",
        "name": "Diagnostic Lab Tests — Annual Health Checkup",
        "member": "EMP002", "category": "DIAGNOSTIC", "amount": 2000,
        "treatment_date": "2024-11-05",
        "hospital": "Precision Diagnostics Pvt Ltd", "gstin": "29AABCP5678B1ZX",
        "doctor": "Dr. Meena Pillai", "reg": "KA/89012/2018",
        "doctor_qual": "MBBS, MD (Pathology)",
        "clinic_addr": "45 Jayanagar, Bengaluru - 560041",
        "clinic_phone": "+91-80-2678-1234",
        "patient": "Priya Singh", "patient_age": 32, "patient_gender": "Female",
        "chief_complaint": "Routine annual health screening — no acute complaints",
        "vitals": "BP: 118/76 mmHg, Pulse: 72/min, Weight: 58 kg",
        "diagnosis": "Routine Health Screening — NAD (No Abnormality Detected)",
        "medicines": [],
        "tests_ordered": ["CBC", "Lipid Profile", "Thyroid Panel (TSH, T3, T4)", "Liver Function Test", "Kidney Function Test", "HbA1c"],
        "follow_up": "Review reports with physician in 1 week",
        "line_items": [
            {"description": "Complete Blood Count (CBC)", "quantity": 1, "rate": 400, "gst_pct": 0},
            {"description": "Lipid Profile", "quantity": 1, "rate": 500, "gst_pct": 0},
            {"description": "Thyroid Panel (TSH, T3, T4)", "quantity": 1, "rate": 600, "gst_pct": 0},
            {"description": "Liver Function Test (LFT)", "quantity": 1, "rate": 500, "gst_pct": 0},
        ],
    },
    {
        "id": "case3",
        "name": "Pharmacy — Generic Drug Purchase",
        "member": "EMP003", "category": "PHARMACY", "amount": 800,
        "treatment_date": "2024-11-02",
        "hospital": "Health First Pharmacy",
        "doctor": "Dr. R. Gupta", "reg": "DL/34567/2016",
        "doctor_qual": "MBBS, MD (General Medicine)",
        "clinic_addr": "15 Connaught Place, New Delhi - 110001",
        "clinic_phone": "+91-11-2345-6789",
        "patient": "Amit Verma", "patient_age": 45, "patient_gender": "Male",
        "chief_complaint": "Loose stools since 2 days, nausea, mild abdominal cramps",
        "vitals": "BP: 126/84 mmHg, Pulse: 80/min",
        "diagnosis": "Acute Gastroenteritis",
        "medicines": [
            {"name": "Tab. Paracetamol 500mg", "dosage": "1-0-1", "duration": "3 days", "instructions": "If fever"},
            {"name": "ORS Powder Sachet (WHO Formula)", "dosage": "1 sachet in 1L water", "duration": "3 days", "instructions": "After each loose stool"},
            {"name": "Cap. Probiotic (Lactobacillus 2B CFU)", "dosage": "1-1-1", "duration": "5 days", "instructions": "After food"},
            {"name": "Tab. Ondansetron 4mg", "dosage": "0-1-0", "duration": "3 days", "instructions": "30 min before food, for nausea"},
        ],
        "tests_ordered": [],
        "follow_up": "If stools not normal in 3 days or blood appears",
        "line_items": [
            {"description": "Tab. Paracetamol 500mg (15 tabs)", "quantity": 1, "rate": 150, "gst_pct": 12},
            {"description": "ORS Sachets (5 pcs)", "quantity": 1, "rate": 100, "gst_pct": 5},
            {"description": "Cap. Probiotic (15 caps)", "quantity": 1, "rate": 350, "gst_pct": 12},
            {"description": "Tab. Ondansetron 4mg (9 tabs)", "quantity": 1, "rate": 200, "gst_pct": 12},
        ],
    },
    {
        "id": "case4",
        "name": "Network Hospital — Apollo (Discount Applied)",
        "member": "EMP010", "category": "CONSULTATION", "amount": 4500,
        "treatment_date": "2024-11-03",
        "hospital": "Apollo Hospitals", "gstin": "33AAACA8895Q1ZK",
        "doctor": "Dr. S. Iyer", "reg": "TN/56789/2013",
        "doctor_qual": "MBBS, MD (Pulmonology), DNB",
        "clinic_addr": "21 Greams Lane, Chennai - 600006",
        "clinic_phone": "+91-44-2829-0200",
        "patient": "Deepak Shah", "patient_age": 52, "patient_gender": "Male",
        "chief_complaint": "Persistent cough with green sputum x 1 week, fever x 3 days, shortness of breath",
        "vitals": "BP: 132/86 mmHg, Temp: 101.8 F, Pulse: 94/min, SpO2: 94%",
        "diagnosis": "Acute Bronchitis with Reactive Airway Disease",
        "medicines": [
            {"name": "Cap. Amoxicillin 500mg", "dosage": "1-1-1", "duration": "7 days", "instructions": "After food"},
            {"name": "Salbutamol Inhaler (Asthalin) 100mcg", "dosage": "2 puffs SOS", "duration": "as needed", "instructions": "For wheezing / breathlessness"},
            {"name": "Tab. Acetylcysteine 600mg", "dosage": "1-0-1", "duration": "7 days", "instructions": "After food, mucolytic"},
        ],
        "tests_ordered": ["Chest X-Ray (PA View)", "Sputum Culture & Sensitivity", "CBC with ESR"],
        "follow_up": "After 7 days or earlier if breathing difficulty worsens",
        "line_items": [
            {"description": "Consultation Fee (Specialist)", "quantity": 1, "rate": 1500, "gst_pct": 0},
            {"description": "Chest X-Ray (PA View)", "quantity": 1, "rate": 800, "gst_pct": 0},
            {"description": "Nebulization (2 sessions)", "quantity": 2, "rate": 560, "gst_pct": 0},
            {"description": "Amoxicillin 500mg (21 caps)", "quantity": 1, "rate": 630, "gst_pct": 5},
            {"description": "Salbutamol Inhaler", "quantity": 1, "rate": 450, "gst_pct": 12},
        ],
    },
    {
        "id": "case5",
        "name": "Dental — Composite Filling (Covered Procedure)",
        "member": "EMP002", "category": "DENTAL", "amount": 3000,
        "treatment_date": "2024-11-04",
        "hospital": "Smile Dental Clinic & Implant Centre",
        "doctor": "Dr. Kavita Rao", "reg": "KA/67890/2019",
        "doctor_qual": "BDS, MDS (Conservative Dentistry)",
        "clinic_addr": "78 Indiranagar, Bengaluru - 560038",
        "clinic_phone": "+91-80-4123-4567",
        "patient": "Priya Singh", "patient_age": 32, "patient_gender": "Female",
        "chief_complaint": "Pain in lower right molar while eating sweets and cold food x 2 weeks",
        "vitals": "BP: 120/78 mmHg, Pulse: 74/min",
        "diagnosis": "Dental Caries — Class I (Mandibular Right First Molar #46)",
        "medicines": [
            {"name": "Tab. Amoxicillin 500mg", "dosage": "1-1-1", "duration": "5 days", "instructions": "After food, antibiotic prophylaxis"},
            {"name": "Tab. Ibuprofen 400mg", "dosage": "1-0-1", "duration": "3 days", "instructions": "After food, for post-procedure pain"},
            {"name": "Chlorhexidine Mouthwash 0.2%", "dosage": "15ml rinse twice daily", "duration": "7 days", "instructions": "After brushing"},
        ],
        "tests_ordered": [],
        "follow_up": "After 2 weeks for polishing, or earlier if sensitivity persists",
        "additional_notes": "Rubber dam isolation used. High-strength composite restoration (3M Filtek Z350 XT).",
        "line_items": [
            {"description": "Dental Examination & Consultation", "quantity": 1, "rate": 500, "gst_pct": 0},
            {"description": "Intraoral Periapical Radiograph (IOPA)", "quantity": 1, "rate": 300, "gst_pct": 0},
            {"description": "Composite Restoration (Class I, Tooth #46)", "quantity": 1, "rate": 1700, "gst_pct": 0},
            {"description": "Amoxicillin 500mg (15 tabs)", "quantity": 1, "rate": 200, "gst_pct": 5},
            {"description": "Ibuprofen 400mg (10 tabs)", "quantity": 1, "rate": 150, "gst_pct": 5},
            {"description": "Chlorhexidine Mouthwash (150ml)", "quantity": 1, "rate": 150, "gst_pct": 12},
        ],
    },
    {
        "id": "case6",
        "name": "Vision — Eye Exam & Prescription Glasses",
        "member": "EMP004", "category": "VISION", "amount": 2500,
        "treatment_date": "2024-11-06",
        "hospital": "Vasan Eye Care Hospital",
        "doctor": "Dr. Arvind Menon", "reg": "KA/12345/2017",
        "doctor_qual": "MBBS, MS (Ophthalmology), FRCS (Edin)",
        "clinic_addr": "25 Brigade Road, Bengaluru - 560025",
        "clinic_phone": "+91-80-2558-1234",
        "patient": "Sneha Reddy", "patient_age": 28, "patient_gender": "Female",
        "chief_complaint": "Difficulty reading road signs while driving, eye strain after screen work",
        "vitals": "BP: 112/74 mmHg, Pulse: 68/min",
        "diagnosis": "Simple Myopia (OD: -2.25D, OS: -2.00D) with Astigmatism",
        "medicines": [
            {"name": "Refresh Tears Eye Drops (CMC 0.5%)", "dosage": "1 drop TID", "duration": "as needed", "instructions": "For dryness"},
        ],
        "tests_ordered": [],
        "follow_up": "Eye checkup after 1 year or earlier if vision changes",
        "additional_notes": "Pupillary distance (PD): 62mm. Anti-reflective coating recommended.",
        "line_items": [
            {"description": "Comprehensive Eye Examination", "quantity": 1, "rate": 800, "gst_pct": 0},
            {"description": "Prescription Glasses — Single Vision (Frame + Lens)", "quantity": 1, "rate": 1700, "gst_pct": 18},
        ],
    },
    {
        "id": "case7",
        "name": "Alternative Medicine — Panchakarma (Ayurveda)",
        "member": "EMP006", "category": "ALTERNATIVE_MEDICINE", "amount": 4000,
        "treatment_date": "2024-11-07",
        "hospital": "Ayur Wellness & Panchakarma Centre",
        "doctor": "Vaidya T. Krishnan", "reg": "AYUR/KL/2345/2019",
        "doctor_qual": "BAMS, MD (Panchakarma), PhD (Ayurveda)",
        "clinic_addr": "34 Ayurveda Marg, Bengaluru - 560002",
        "clinic_phone": "+91-80-2654-3210",
        "patient": "Kavita Nair", "patient_age": 47, "patient_gender": "Female",
        "chief_complaint": "Chronic bilateral knee pain, stiffness in morning >30 min, aggravated in winter x 2 years",
        "vitals": "BP: 124/80 mmHg, Pulse: 76/min, Weight: 72 kg",
        "diagnosis": "Sandhivata (Osteoarthritis of Knees) — Vata-Kapha predominance",
        "medicines": [
            {"name": "Shallaki (Boswellia serrata) 500mg Capsules", "dosage": "1-0-1", "duration": "30 days", "instructions": "After food with warm water"},
            {"name": "Yogaraj Guggulu 500mg Tablets", "dosage": "0-1-0", "duration": "30 days", "instructions": "After lunch, for joint inflammation"},
            {"name": "Mahanarayana Taila (Oil) — External", "dosage": "Gentle massage on knees", "duration": "30 days", "instructions": "Twice daily, warm before application"},
        ],
        "tests_ordered": [],
        "follow_up": "After 1 month for assessment, continue medicines for 3 months",
        "additional_notes": "Diet advised: avoid cold, dry, and fermented foods. Include ginger, turmeric, and ghee in diet.",
        "line_items": [
            {"description": "Ayurvedic Consultation (Vaidya)", "quantity": 1, "rate": 500, "gst_pct": 0},
            {"description": "Abhyanga (Full Body Oil Massage)", "quantity": 1, "rate": 1000, "gst_pct": 0},
            {"description": "Swedana (Herbal Steam Therapy)", "quantity": 3, "rate": 500, "gst_pct": 0},
            {"description": "Shallaki Capsules (60 caps)", "quantity": 1, "rate": 600, "gst_pct": 5},
            {"description": "Yogaraj Guggulu (60 tabs)", "quantity": 1, "rate": 400, "gst_pct": 5},
        ],
    },
    {
        "id": "case8",
        "name": "Consultation — Upper Respiratory Infection",
        "member": "EMP001", "category": "CONSULTATION", "amount": 3500,
        "treatment_date": "2024-11-08",
        "hospital": "Manipal Hospital", "gstin": "29AABCM1234H1ZX",
        "doctor": "Dr. N. Subramanian", "reg": "KA/34567/2016",
        "doctor_qual": "MBBS, MD (Internal Medicine), FICP",
        "clinic_addr": "98 HAL Airport Road, Bengaluru - 560017",
        "clinic_phone": "+91-80-2502-3456",
        "patient": "Rajesh Kumar", "patient_age": 39, "patient_gender": "Male",
        "chief_complaint": "Severe sore throat x 4 days, fever, nasal congestion, productive cough",
        "vitals": "BP: 122/82 mmHg, Temp: 100.8 F, Pulse: 86/min, SpO2: 96%",
        "diagnosis": "Upper Respiratory Tract Infection (URTI) with Pharyngitis",
        "medicines": [
            {"name": "Tab. Azithromycin 500mg", "dosage": "1-0-0", "duration": "5 days", "instructions": "1 hour before food"},
            {"name": "Tab. Cetirizine 10mg + Pseudoephedrine 120mg (Zukamin Cold)", "dosage": "0-1-0", "duration": "5 days", "instructions": "After food"},
            {"name": "Tab. Paracetamol 650mg (Dolo 650)", "dosage": "1-1-1", "duration": "5 days", "instructions": "After food"},
            {"name": "Cofsils Lozenges", "dosage": "1 lozenge every 4 hours", "duration": "3 days", "instructions": "For sore throat relief"},
        ],
        "tests_ordered": ["CBC with Differential", "Throat Swab Culture", "CRP"],
        "follow_up": "After 5 days if symptoms not improving",
        "additional_notes": "Steam inhalation twice daily. Increase fluid intake. Avoid cold beverages and oily food.",
        "line_items": [
            {"description": "Consultation Fee (OPD Specialist)", "quantity": 1, "rate": 1500, "gst_pct": 0},
            {"description": "CBC with Differential", "quantity": 1, "rate": 400, "gst_pct": 0},
            {"description": "Throat Swab Culture", "quantity": 1, "rate": 400, "gst_pct": 0},
            {"description": "Nebulization (1 session)", "quantity": 1, "rate": 400, "gst_pct": 0},
            {"description": "Azithromycin 500mg (5 tabs)", "quantity": 1, "rate": 450, "gst_pct": 5},
            {"description": "Cetirizine+Pseudoephedrine (5 tabs)", "quantity": 1, "rate": 180, "gst_pct": 12},
            {"description": "Paracetamol 650mg (15 tabs)", "quantity": 1, "rate": 170, "gst_pct": 5},
        ],
    },
    {
        "id": "case9",
        "name": "Diagnostic — Comprehensive Health Package",
        "member": "EMP007", "category": "DIAGNOSTIC", "amount": 1800,
        "treatment_date": "2024-11-09",
        "hospital": "Thyrocare Technologies Ltd (Mumbai Central Lab)",
        "doctor": "Dr. Venkat Rao", "reg": "AP/67890/2017",
        "doctor_qual": "MBBS, MD (Biochemistry)",
        "clinic_addr": "D-37/1, MIDC, Turbhe, Navi Mumbai - 400705",
        "clinic_phone": "+91-22-4123-4567",
        "patient": "Suresh Patil", "patient_age": 41, "patient_gender": "Male",
        "chief_complaint": "Preventive health checkup — no specific complaints. Family history of diabetes.",
        "vitals": "BP: 130/86 mmHg, Pulse: 78/min, Weight: 78 kg, Height: 172 cm, BMI: 26.4",
        "diagnosis": "Routine Health Screening — Borderline dyslipidemia noted",
        "medicines": [],
        "tests_ordered": ["CBC", "Lipid Profile", "Fasting & PP Blood Glucose", "HbA1c", "Thyroid Profile", "LFT", "KFT", "Urine Routine"],
        "follow_up": "Review with physician. Lifestyle modification for elevated LDL.",
        "additional_notes": "Patient advised to reduce saturated fat intake and increase physical activity (30 min walk daily).",
        "line_items": [
            {"description": "Complete Health Package (includes CBC, Lipid, Glucose, LFT, KFT, Thyroid, Urine)", "quantity": 1, "rate": 1800, "gst_pct": 0},
        ],
    },
    {
        "id": "case10",
        "name": "Pharmacy + Hypertension Follow-up",
        "member": "EMP003", "category": "PHARMACY", "amount": 1200,
        "treatment_date": "2024-11-10",
        "hospital": "Apollo Pharmacy (Delhi)",
        "doctor": "Dr. R. Gupta", "reg": "DL/34567/2016",
        "doctor_qual": "MBBS, MD (General Medicine)",
        "clinic_addr": "15 Connaught Place, New Delhi - 110001",
        "clinic_phone": "+91-11-2345-6789",
        "patient": "Amit Verma", "patient_age": 46, "patient_gender": "Male",
        "chief_complaint": "Routine BP checkup and medication refill. No new complaints.",
        "vitals": "BP: 134/88 mmHg (controlled on medication), Pulse: 76/min",
        "diagnosis": "Essential Hypertension (HTN) — Well controlled on current medication",
        "medicines": [
            {"name": "Tab. Amlodipine 5mg (Amlong)", "dosage": "1-0-0", "duration": "30 days", "instructions": "Morning, after breakfast"},
            {"name": "Tab. Telmisartan 40mg (Telma)", "dosage": "0-0-1", "duration": "30 days", "instructions": "At bedtime"},
        ],
        "tests_ordered": [],
        "follow_up": "BP monitoring at home weekly. Next review in 3 months.",
        "additional_notes": "Continue low-sodium diet. Avoid added salt in food. Reduce caffeine intake.",
        "line_items": [
            {"description": "Follow-up Consultation", "quantity": 1, "rate": 400, "gst_pct": 0},
            {"description": "Amlodipine 5mg (Amlong) — 30 tabs", "quantity": 1, "rate": 300, "gst_pct": 12},
            {"description": "Telmisartan 40mg (Telma) — 30 tabs", "quantity": 1, "rate": 350, "gst_pct": 12},
            {"description": "BP Monitoring", "quantity": 1, "rate": 150, "gst_pct": 0},
        ],
    },
]

REJECTION_CASES = [
    {
        "id": "case1",
        "name": "Wrong Documents — Two Prescriptions, No Bill",
        "member": "EMP001", "category": "CONSULTATION", "amount": 1500,
        "treatment_date": "2024-11-01",
        "doctor": "Dr. Arun Sharma", "reg": "KA/45678/2015",
        "doctor_qual": "MBBS, MD (Internal Medicine)",
        "clinic_addr": "12 MG Road, Bengaluru - 560001",
        "clinic_phone": "+91-80-2345-6789",
        "patient": "Rajesh Kumar", "patient_age": 39, "patient_gender": "Male",
        "diagnosis": "Viral Fever",
        "medicines": [
            {"name": "Tab. Paracetamol 650mg", "dosage": "1-1-1", "duration": "5 days", "instructions": ""},
        ],
        "error_type": "MISSING_REQUIRED",
        "scenario": "Two prescriptions uploaded, hospital bill missing",
    },
    {
        "id": "case2",
        "name": "Unreadable Pharmacy Bill",
        "member": "EMP004", "category": "PHARMACY", "amount": 800,
        "treatment_date": "2024-10-25",
        "doctor": "Dr. Sunita Reddy", "reg": "KA/23456/2018",
        "doctor_qual": "MBBS, MD (General Medicine)",
        "clinic_addr": "45 Indiranagar, Bengaluru - 560038",
        "clinic_phone": "+91-80-4156-7890",
        "patient": "Sneha Reddy", "patient_age": 28, "patient_gender": "Female",
        "diagnosis": "Acute Pharyngitis",
        "medicines": [
            {"name": "Tab. Azithromycin 500mg", "dosage": "1-0-0", "duration": "5 days", "instructions": ""},
        ],
        "error_type": "UNREADABLE",
        "scenario": "Pharmacy bill is blurry/unreadable",
    },
    {
        "id": "case3",
        "name": "Patient Name Mismatch",
        "member": "EMP001", "category": "CONSULTATION", "amount": 1500,
        "treatment_date": "2024-11-01",
        "doctor": "Dr. Arun Sharma", "reg": "KA/45678/2015",
        "doctor_qual": "MBBS, MD (Internal Medicine)",
        "clinic_addr": "12 MG Road, Bengaluru - 560001",
        "clinic_phone": "+91-80-2345-6789",
        "patient": "Rajesh Kumar", "patient_age": 39, "patient_gender": "Male",
        "diagnosis": "Viral Fever",
        "medicines": [{"name": "Tab. Paracetamol 650mg", "dosage": "1-1-1", "duration": "5 days", "instructions": ""}],
        "error_type": "PATIENT_MISMATCH",
        "scenario": "Prescription for Rajesh Kumar, bill for Arjun Mehta",
    },
    {
        "id": "case4",
        "name": "Waiting Period — Diabetes (EMP005 joined Sep 2024)",
        "member": "EMP005", "category": "CONSULTATION", "amount": 3000,
        "treatment_date": "2024-10-15",
        "hospital": "City Medical Centre, Bengaluru",
        "doctor": "Dr. Sunil Mehta", "reg": "GJ/56789/2014",
        "doctor_qual": "MBBS, MD (Endocrinology), DM",
        "clinic_addr": "32 Satellite Road, Ahmedabad - 380015",
        "clinic_phone": "+91-79-2678-1234",
        "patient": "Vikram Joshi", "patient_age": 55, "patient_gender": "Male",
        "chief_complaint": "Increased thirst, frequent urination, fatigue x 1 month",
        "vitals": "BP: 138/90 mmHg, Weight: 82 kg, Height: 168 cm",
        "diagnosis": "Type 2 Diabetes Mellitus (T2DM) — Newly Diagnosed",
        "medicines": [
            {"name": "Tab. Metformin 500mg (Glyciphage)", "dosage": "1-0-1", "duration": "30 days", "instructions": "After food"},
            {"name": "Tab. Glimepiride 1mg (Amaryl)", "dosage": "1-0-0", "duration": "30 days", "instructions": "Before breakfast"},
        ],
        "tests_ordered": ["HbA1c", "Fasting & PP Glucose", "Lipid Profile", "Kidney Function Test", "Urine Microalbumin"],
        "follow_up": "After 1 month with blood sugar log",
        "line_items": [
            {"description": "Specialist Consultation (Endocrinology)", "quantity": 1, "rate": 1000, "gst_pct": 0},
            {"description": "HbA1c Test", "quantity": 1, "rate": 500, "gst_pct": 0},
            {"description": "Fasting & PP Blood Glucose", "quantity": 1, "rate": 200, "gst_pct": 0},
            {"description": "Metformin 500mg (60 tabs)", "quantity": 1, "rate": 480, "gst_pct": 5},
            {"description": "Glimepiride 1mg (30 tabs)", "quantity": 1, "rate": 420, "gst_pct": 5},
            {"description": "Glucometer + 50 Strips", "quantity": 1, "rate": 400, "gst_pct": 12},
        ],
        "rejection_reason": "WAITING_PERIOD",
        "scenario": "EMP005 joined 2024-09-01. Claims for diabetes on 2024-10-15 — within 90-day waiting period.",
    },
    {
        "id": "case5",
        "name": "Excluded Condition — Obesity Bariatric",
        "member": "EMP009", "category": "CONSULTATION", "amount": 8000,
        "treatment_date": "2024-10-18",
        "hospital": "Wellness & Metabolic Clinic, Mumbai",
        "doctor": "Dr. P. Banerjee", "reg": "WB/34567/2015",
        "doctor_qual": "MBBS, MD (Internal Medicine), Fellowship in Obesity Medicine",
        "clinic_addr": "56 Park Street, Kolkata - 700016",
        "clinic_phone": "+91-33-2244-5678",
        "patient": "Anita Desai", "patient_age": 42, "patient_gender": "Female",
        "chief_complaint": "Weight gain x 5 years, BMI 37, difficulty walking, joint pain, snoring",
        "vitals": "BP: 144/92 mmHg, Weight: 96 kg, Height: 161 cm, BMI: 37.0",
        "diagnosis": "Morbid Obesity (BMI 37.0) with Metabolic Syndrome",
        "medicines": [
            {"name": "Tab. Orlistat 120mg", "dosage": "1-1-1", "duration": "30 days", "instructions": "With meals containing fat"},
        ],
        "tests_ordered": ["Lipid Profile", "HbA1c", "Thyroid Profile", "Vitamin D & B12", "Sleep Study"],
        "follow_up": "After 1 month with food diary. Bariatric surgery evaluation if no improvement.",
        "line_items": [
            {"description": "Bariatric Consultation", "quantity": 1, "rate": 3000, "gst_pct": 0},
            {"description": "Personalised Diet & Nutrition Program (3 months)", "quantity": 1, "rate": 5000, "gst_pct": 0},
        ],
        "rejection_reason": "EXCLUDED_CONDITION",
        "scenario": "Obesity/bariatric treatment explicitly excluded.",
    },
    {
        "id": "case6",
        "name": "Per-Claim Limit Exceeded — ₹7,500 > ₹5,000",
        "member": "EMP003", "category": "CONSULTATION", "amount": 7500,
        "treatment_date": "2024-10-20",
        "hospital": "Max Super Specialty Hospital", "gstin": "07AAACM4321A1ZX",
        "doctor": "Dr. R. Gupta", "reg": "DL/34567/2016",
        "doctor_qual": "MBBS, MD (General Medicine)",
        "clinic_addr": "15 Connaught Place, New Delhi - 110001",
        "clinic_phone": "+91-11-2345-6789",
        "patient": "Amit Verma", "patient_age": 46, "patient_gender": "Male",
        "chief_complaint": "Severe abdominal pain, vomiting, diarrhea x 2 days, unable to keep food down",
        "vitals": "BP: 110/70 mmHg, Pulse: 100/min, Temp: 100.4 F, Signs of dehydration",
        "diagnosis": "Acute Gastroenteritis with Moderate Dehydration",
        "medicines": [
            {"name": "Inj. Ondansetron 4mg IV", "dosage": "Stat dose given", "duration": "Single dose", "instructions": ""},
            {"name": "Tab. Ofloxacin 200mg + Ornidazole 500mg", "dosage": "1-0-1", "duration": "5 days", "instructions": "After food"},
            {"name": "Cap. Probiotic (VSL#3)", "dosage": "1-1-1", "duration": "7 days", "instructions": "After food"},
            {"name": "ORS — continue at home", "dosage": "200ml after each loose stool", "duration": "as needed", "instructions": ""},
        ],
        "tests_ordered": ["CBC", "Serum Electrolytes", "Stool Routine & Culture"],
        "follow_up": "After 3 days or earlier if unable to tolerate oral fluids",
        "line_items": [
            {"description": "Emergency Consultation", "quantity": 1, "rate": 2000, "gst_pct": 0},
            {"description": "IV Fluids (Ringer's Lactate 1L x 2)", "quantity": 2, "rate": 750, "gst_pct": 0},
            {"description": "CBC + Electrolytes", "quantity": 1, "rate": 1000, "gst_pct": 0},
            {"description": "Ofloxacin+Ornidazole (10 tabs)", "quantity": 1, "rate": 400, "gst_pct": 5},
            {"description": "VSL#3 Probiotic (21 caps)", "quantity": 1, "rate": 600, "gst_pct": 12},
            {"description": "Inj. Ondansetron + Administration", "quantity": 1, "rate": 300, "gst_pct": 5},
            {"description": "Disposable IV Set + Cannula", "quantity": 1, "rate": 200, "gst_pct": 12},
        ],
        "rejection_reason": "PER_CLAIM_EXCEEDED",
        "scenario": "Total ₹7,500 exceeds per-claim limit of ₹5,000.",
    },
    {
        "id": "case7",
        "name": "Pre-Authorization Missing — MRI Lumbar Spine",
        "member": "EMP007", "category": "DIAGNOSTIC", "amount": 15000,
        "treatment_date": "2024-11-02",
        "hospital": "AIIMS Diagnostic Centre, Delhi",
        "doctor": "Dr. Venkat Rao", "reg": "AP/67890/2017",
        "doctor_qual": "MBBS, DNB (Orthopaedics), MCh (Neuro-Spine)",
        "clinic_addr": "AIIMS Campus, Ansari Nagar, New Delhi - 110029",
        "clinic_phone": "+91-11-2658-8500",
        "patient": "Suresh Patil", "patient_age": 42, "patient_gender": "Male",
        "chief_complaint": "Lower back pain radiating to right leg x 3 months, numbness in right foot, difficulty walking",
        "vitals": "BP: 128/84 mmHg, Pulse: 74/min",
        "diagnosis": "Suspected Lumbar Disc Herniation (L4-L5) with Right S1 Radiculopathy",
        "medicines": [
            {"name": "Tab. Pregabalin 75mg (Pregabid)", "dosage": "0-1-0", "duration": "15 days", "instructions": "At bedtime"},
            {"name": "Tab. Etoricoxib 90mg", "dosage": "1-0-0", "duration": "10 days", "instructions": "After breakfast"},
        ],
        "tests_ordered": ["MRI Lumbar Spine (with contrast)", "Nerve Conduction Study", "X-Ray Lumbar Spine (AP + Lateral)"],
        "follow_up": "After MRI report. Physiotherapy referral planned.",
        "additional_notes": "Patient advised strict bed rest for 3 days. Avoid bending forward and lifting weights. Use lumbar support belt.",
        "line_items": [
            {"description": "MRI Lumbar Spine (with IV Contrast)", "quantity": 1, "rate": 15000, "gst_pct": 0},
        ],
        "rejection_reason": "PRE_AUTH_MISSING",
        "scenario": "MRI >₹10,000 requires pre-authorization. Not obtained.",
    },
    {
        "id": "case8",
        "name": "Dental — Teeth Whitening (Cosmetic, Excluded)",
        "member": "EMP002", "category": "DENTAL", "amount": 6000,
        "treatment_date": "2024-10-25",
        "hospital": "Smile Dental Clinic & Implant Centre",
        "doctor": "Dr. Kavita Rao", "reg": "KA/67890/2019",
        "doctor_qual": "BDS, MDS (Conservative Dentistry)",
        "clinic_addr": "78 Indiranagar, Bengaluru - 560038",
        "clinic_phone": "+91-80-4123-4567",
        "patient": "Priya Singh", "patient_age": 32, "patient_gender": "Female",
        "chief_complaint": "Desires brighter smile for upcoming wedding. Teeth appear yellowish.",
        "vitals": "BP: 118/74 mmHg, Pulse: 70/min",
        "diagnosis": "Extrinsic Dental Stains — Aesthetic Concern",
        "medicines": [],
        "tests_ordered": [],
        "follow_up": "None required",
        "additional_notes": "Patient counseled about sensitivity after whitening and advised to avoid staining foods for 48 hours.",
        "line_items": [
            {"description": "In-Office Teeth Whitening (Zoom Advanced Power)", "quantity": 1, "rate": 4000, "gst_pct": 0},
            {"description": "Ultrasonic Scaling & Polishing", "quantity": 1, "rate": 2000, "gst_pct": 0},
        ],
        "rejection_reason": "EXCLUDED_CONDITION",
        "scenario": "Teeth whitening is cosmetic, excluded under dental policy. Scaling may be covered.",
    },
    {
        "id": "case9",
        "name": "Submission Deadline Exceeded — 153 Days Late",
        "member": "EMP001", "category": "CONSULTATION", "amount": 2000,
        "treatment_date": "2024-06-15",
        "hospital": "City Medical Centre",
        "doctor": "Dr. Arun Sharma", "reg": "KA/45678/2015",
        "doctor_qual": "MBBS, MD (Internal Medicine)",
        "clinic_addr": "12 MG Road, Bengaluru - 560001",
        "clinic_phone": "+91-80-2345-6789",
        "patient": "Rajesh Kumar", "patient_age": 39, "patient_gender": "Male",
        "chief_complaint": "Severe one-sided headache with aura, nausea, photophobia — recurring episodes",
        "vitals": "BP: 128/82 mmHg, Pulse: 78/min",
        "diagnosis": "Migraine with Aura (Classic Migraine) — Acute Episode",
        "medicines": [
            {"name": "Tab. Sumatriptan 50mg", "dosage": "1 tab at onset", "duration": "as needed", "instructions": "Take at first sign of migraine, repeat after 2h if needed (max 2/day)"},
            {"name": "Tab. Naproxen 500mg", "dosage": "1-0-1", "duration": "3 days", "instructions": "After food"},
            {"name": "Tab. Propranolol 40mg (Migraine Prophylaxis)", "dosage": "1-0-1", "duration": "30 days", "instructions": "Continue daily"},
        ],
        "tests_ordered": ["CT Scan Brain (Plain)", "Fundoscopy (Eye Exam)"],
        "follow_up": "After 1 month. Maintain headache diary. Avoid triggers: cheese, chocolate, red wine.",
        "line_items": [
            {"description": "Consultation Fee (OPD)", "quantity": 1, "rate": 1000, "gst_pct": 0},
            {"description": "CT Scan Brain (Plain)", "quantity": 1, "rate": 500, "gst_pct": 0},
            {"description": "Sumatriptan 50mg (6 tabs)", "quantity": 1, "rate": 350, "gst_pct": 12},
            {"description": "Propranolol 40mg (60 tabs)", "quantity": 1, "rate": 150, "gst_pct": 5},
        ],
        "rejection_reason": "SUBMISSION_DEADLINE_EXCEEDED",
        "scenario": "Treatment on Jun 15, submitted in November — exceeds 30-day deadline by 153 days.",
    },
    {
        "id": "case10",
        "name": "Fraud Signal — 4th Same-Day Claim (MANUAL_REVIEW)",
        "member": "EMP008", "category": "CONSULTATION", "amount": 4800,
        "treatment_date": "2024-10-30",
        "hospital": "City Clinic A, Bengaluru",
        "doctor": "Dr. S. Khan", "reg": "KA/11111/2020",
        "doctor_qual": "MBBS, DNB (Neurology)",
        "clinic_addr": "12 Koramangala, Bengaluru - 560034",
        "clinic_phone": "+91-80-4110-2345",
        "patient": "Ravi Menon", "patient_age": 35, "patient_gender": "Male",
        "chief_complaint": "Recurrent headache with dizziness x 1 week, blurred vision occasionally",
        "vitals": "BP: 134/86 mmHg, Pulse: 82/min",
        "diagnosis": "Migraine with Vertiginous Component — Rule Out Vestibular Migraine",
        "medicines": [
            {"name": "Tab. Sumatriptan 50mg", "dosage": "1 tab at migraine onset", "duration": "as needed", "instructions": "Max 2 per day"},
            {"name": "Tab. Cinnarizine 25mg + Dimenhydrinate 40mg", "dosage": "1-0-1", "duration": "10 days", "instructions": "After food, for vertigo"},
        ],
        "tests_ordered": ["CT Brain (Plain + Contrast)", "Videonystagmography (VNG)", "Audiometry"],
        "follow_up": "After 10 days with investigation reports",
        "line_items": [
            {"description": "Specialist Neurology Consultation", "quantity": 1, "rate": 1500, "gst_pct": 0},
            {"description": "CT Scan Brain (with Contrast)", "quantity": 1, "rate": 2500, "gst_pct": 0},
            {"description": "Sumatriptan 50mg (6 tabs)", "quantity": 1, "rate": 400, "gst_pct": 12},
            {"description": "Cinnarizine+Dimenhydrinate (20 tabs)", "quantity": 1, "rate": 400, "gst_pct": 12},
        ],
        "rejection_reason": "MANUAL_REVIEW",
        "claims_history": [
            {"claim_id": "CLM_0081", "date": "2024-10-30", "amount": 1200, "provider": "City Clinic A"},
            {"claim_id": "CLM_0082", "date": "2024-10-30", "amount": 1800, "provider": "City Clinic B"},
            {"claim_id": "CLM_0083", "date": "2024-10-30", "amount": 2100, "provider": "Wellness Center"},
        ],
        "scenario": "4th claim on same day from EMP008 — triggers fraud flag.",
    },
]

# ── Lab Report Data ───────────────────────────────────────────────

def _build_lab_data(case: dict) -> tuple:
    """Build lab report specific data based on the case."""
    patient = case["patient"]
    age = case["patient_age"]
    gender = case["patient_gender"]

    if case["id"] == "case2":
        test_groups = [
            {
                "group_name": "HAEMATOLOGY (CBC)",
                "tests": [
                    {"name": "Hemoglobin (Hb)", "result": "13.2", "unit": "g/dL", "normal_range": "12.0 - 15.0", "flag": "", "method": "Cyanmethemoglobin"},
                    {"name": "RBC Count", "result": "4.6", "unit": "mill/uL", "normal_range": "4.0 - 5.2", "flag": "", "method": "Automated"},
                    {"name": "WBC Count", "result": "7,200", "unit": "/uL", "normal_range": "4,500 - 11,000", "flag": "", "method": "Automated"},
                    {"name": "Platelet Count", "result": "245,000", "unit": "/uL", "normal_range": "150,000 - 450,000", "flag": "", "method": "Automated"},
                    {"name": "MCV", "result": "88", "unit": "fL", "normal_range": "80 - 100", "flag": "", "method": "Automated"},
                ],
            },
            {
                "group_name": "LIPID PROFILE",
                "tests": [
                    {"name": "Total Cholesterol", "result": "188", "unit": "mg/dL", "normal_range": "<200", "flag": "", "method": "Enzymatic"},
                    {"name": "HDL Cholesterol", "result": "52", "unit": "mg/dL", "normal_range": ">40 (F)", "flag": "", "method": "Direct"},
                    {"name": "LDL Cholesterol", "result": "112", "unit": "mg/dL", "normal_range": "<130", "flag": "", "method": "Calculated"},
                    {"name": "Triglycerides", "result": "120", "unit": "mg/dL", "normal_range": "<150", "flag": "", "method": "Enzymatic"},
                ],
            },
            {
                "group_name": "THYROID PROFILE",
                "tests": [
                    {"name": "TSH (3rd Gen)", "result": "2.4", "unit": "uIU/mL", "normal_range": "0.4 - 4.0", "flag": "", "method": "ECLIA"},
                    {"name": "Free T3", "result": "3.1", "unit": "pg/mL", "normal_range": "2.3 - 4.2", "flag": "", "method": "ECLIA"},
                    {"name": "Free T4", "result": "1.2", "unit": "ng/dL", "normal_range": "0.8 - 1.8", "flag": "", "method": "ECLIA"},
                ],
            },
        ]
        remarks = "All parameters within normal limits. Lipid profile shows borderline normal LDL. No active intervention required. Clinical correlation advised."
        pathologist = "Dr. Meena Pillai, MD (Pathology)"
        pathologist_reg = "KA/89012/2018"

    elif case["id"] == "case9":
        test_groups = [
            {
                "group_name": "HAEMATOLOGY",
                "tests": [
                    {"name": "Hemoglobin (Hb)", "result": "14.1", "unit": "g/dL", "normal_range": "13.0 - 17.0", "flag": "", "method": "Cyanmethemoglobin"},
                    {"name": "WBC Count", "result": "8,100", "unit": "/uL", "normal_range": "4,500 - 11,000", "flag": "", "method": "Automated"},
                    {"name": "Platelet Count", "result": "260,000", "unit": "/uL", "normal_range": "150,000 - 450,000", "flag": "", "method": "Automated"},
                ],
            },
            {
                "group_name": "BIOCHEMISTRY",
                "tests": [
                    {"name": "Fasting Blood Glucose", "result": "102", "unit": "mg/dL", "normal_range": "70 - 100", "flag": "HIGH", "method": "Hexokinase"},
                    {"name": "Post Prandial Glucose", "result": "138", "unit": "mg/dL", "normal_range": "<140", "flag": "", "method": "Hexokinase"},
                    {"name": "HbA1c", "result": "5.8", "unit": "%", "normal_range": "<5.7", "flag": "HIGH", "method": "HPLC"},
                    {"name": "Total Cholesterol", "result": "210", "unit": "mg/dL", "normal_range": "<200", "flag": "HIGH", "method": "Enzymatic"},
                    {"name": "HDL Cholesterol", "result": "38", "unit": "mg/dL", "normal_range": ">40 (M)", "flag": "LOW", "method": "Direct"},
                    {"name": "LDL Cholesterol", "result": "142", "unit": "mg/dL", "normal_range": "<130", "flag": "HIGH", "method": "Calculated"},
                    {"name": "Triglycerides", "result": "180", "unit": "mg/dL", "normal_range": "<150", "flag": "HIGH", "method": "Enzymatic"},
                    {"name": "Total Bilirubin", "result": "0.8", "unit": "mg/dL", "normal_range": "0.2 - 1.2", "flag": "", "method": "Jendrassik-Grof"},
                    {"name": "SGOT (AST)", "result": "28", "unit": "U/L", "normal_range": "<40", "flag": "", "method": "IFCC"},
                    {"name": "SGPT (ALT)", "result": "32", "unit": "U/L", "normal_range": "<40", "flag": "", "method": "IFCC"},
                    {"name": "Serum Creatinine", "result": "0.9", "unit": "mg/dL", "normal_range": "0.7 - 1.3", "flag": "", "method": "Jaffe"},
                    {"name": "Uric Acid", "result": "5.8", "unit": "mg/dL", "normal_range": "3.5 - 7.2", "flag": "", "method": "Uricase"},
                ],
            },
            {
                "group_name": "URINALYSIS",
                "tests": [
                    {"name": "Color", "result": "Straw", "unit": "", "normal_range": "Pale Yellow", "flag": "", "method": "Visual"},
                    {"name": "pH", "result": "6.0", "unit": "", "normal_range": "5.0 - 8.0", "flag": "", "method": "Dipstick"},
                    {"name": "Protein", "result": "Nil", "unit": "", "normal_range": "Nil", "flag": "", "method": "Dipstick"},
                    {"name": "Glucose", "result": "Trace", "unit": "", "normal_range": "Nil", "flag": "*", "method": "Dipstick"},
                    {"name": "Ketones", "result": "Nil", "unit": "", "normal_range": "Nil", "flag": "", "method": "Dipstick"},
                ],
            },
        ]
        remarks = "1. Fasting glucose is borderline elevated (impaired fasting glucose). 2. HbA1c 5.8% indicates prediabetes — lifestyle modification strongly advised. 3. Dyslipidemia noted — elevated LDL (142) and TG (180), low HDL (38). Suggest dietary changes and increased physical activity. 4. Trace glucose in urine correlates with elevated blood glucose. 5. All other parameters within normal limits. Clinical correlation advised — follow up with treating physician for prediabetes management."
        pathologist = "Dr. Venkat Rao, MD (Biochemistry)"
        pathologist_reg = "AP/67890/2017"

    else:
        # Default lab data
        test_groups = [
            {
                "group_name": "HAEMATOLOGY",
                "tests": [
                    {"name": "Hemoglobin", "result": "13.5", "unit": "g/dL", "normal_range": "13.0 - 17.0", "flag": "", "method": "Automated"},
                    {"name": "WBC Count", "result": "8,500", "unit": "/uL", "normal_range": "4,500 - 11,000", "flag": "", "method": "Automated"},
                    {"name": "Platelet Count", "result": "220,000", "unit": "/uL", "normal_range": "150,000 - 450,000", "flag": "", "method": "Automated"},
                ],
            },
        ]
        remarks = "All parameters within normal limits."
        pathologist = "Dr. Meena Pillai, MD (Pathology)"
        pathologist_reg = "KA/89012/2018"

    return case["hospital"], case.get("clinic_addr", ""), lab_accreditation(case["id"]), lab_id(case["id"]), patient, age, gender, case["doctor"], case["treatment_date"], case["treatment_date"], f"SP-{case['treatment_date'].replace('-','')}-{_gen_id(patient)}", test_groups, remarks, pathologist, pathologist_reg


def lab_accreditation(case_id: str) -> str:
    if case_id in ("case2", "case9"):
        return "NABL Accredited Lab (ISO 15189:2012)"
    return "NABL Accredited"


def lab_id(case_id: str) -> str:
    return f"KA-NABL-{1000 + int(''.join(filter(str.isdigit, case_id)))}"


def _pharmacy_data(case: dict):
    """Build pharmacy-specific data."""
    patient = case["patient"]
    meds = case.get("medicines", [])
    line_items = case.get("line_items", [])
    # Build medicine entries for the pharmacy bill table
    pharmacy_meds = []
    for item in line_items:
        pharmacy_meds.append({
            "name": item["description"],
            "batch": _rand_batch(),
            "expiry": _rand_expiry(),
            "quantity": item.get("quantity", 1),
            "mrp": item["rate"],
            "rate": item["rate"],
            "gst_pct": item.get("gst_pct", 12),
        })
    return (
        case["hospital"], "Bengaluru - 560001", "KA-BLR-DL-2024-001234",
        f"HFP-{case['treatment_date'].replace('-','')[-4:]}-{random.randint(1000,9999)}",
        case["treatment_date"], patient, case["doctor"],
        pharmacy_meds, 5, "R. Sharma"
    )


# ── Rejection Document Generators ─────────────────────────────────

def _generate_rejection_case1(case: dict, case_dir: Path):
    """TC001 — Two prescriptions, no hospital bill."""
    # Build prescription 1
    pdf = build_prescription_pdf(
        case["doctor"], case["reg"], case["doctor_qual"], case.get("hospital", "City Clinic"),
        case["clinic_addr"], case["clinic_phone"], case["patient"], case["patient_age"],
        case["patient_gender"], case["treatment_date"], f"Fever since 3 days", "",
        case["diagnosis"], case["medicines"], [], "After 5 days",
    )
    _save_pdf(pdf, case_dir / "prescription_1.pdf")

    # Build prescription 2 (different doctor)
    pdf2 = build_prescription_pdf(
        "Dr. K. Narayan", "KA/56789/2020", "MBBS, MD (General Medicine)",
        "Health Plus Clinic", case["clinic_addr"], case["clinic_phone"],
        case["patient"], case["patient_age"], case["patient_gender"],
        case["treatment_date"], f"Fever since 3 days", "",
        case["diagnosis"], case["medicines"], [], "After 5 days",
    )
    _save_pdf(pdf2, case_dir / "prescription_2.pdf")

    # Build PNG versions
    png1 = build_prescription_png(
        case["doctor"], case["reg"], case["doctor_qual"], case.get("hospital", "City Clinic"),
        case["clinic_addr"], case["clinic_phone"], case["patient"], case["patient_age"],
        case["patient_gender"], case["treatment_date"], "Fever since 3 days", "",
        case["diagnosis"], case["medicines"], [], "After 5 days",
    )
    png1.save_png(case_dir / "prescription_1.png")
    png2 = build_prescription_png(
        "Dr. K. Narayan", "KA/56789/2020", "MBBS, MD (General Medicine)",
        "Health Plus Clinic", case["clinic_addr"], case["clinic_phone"],
        case["patient"], case["patient_age"], case["patient_gender"],
        case["treatment_date"], "Fever since 3 days", "",
        case["diagnosis"], case["medicines"], [], "After 5 days",
    )
    png2.save_png(case_dir / "prescription_2.png")


def _generate_rejection_case2(case: dict, case_dir: Path):
    """TC002 — Good prescription + unreadable pharmacy bill."""
    # Good prescription
    pdf = build_prescription_pdf(
        case["doctor"], case["reg"], case["doctor_qual"], "Health Plus Clinic",
        case["clinic_addr"], case["clinic_phone"], case["patient"], case["patient_age"],
        case["patient_gender"], case["treatment_date"], "Sore throat x 4 days", "",
        case["diagnosis"], case["medicines"], [],
        "After 5 days if not better",
    )
    _save_pdf(pdf, case_dir / "prescription.pdf")
    png1 = build_prescription_png(
        case["doctor"], case["reg"], case["doctor_qual"], "Health Plus Clinic",
        case["clinic_addr"], case["clinic_phone"], case["patient"], case["patient_age"],
        case["patient_gender"], case["treatment_date"], "Sore throat x 4 days", "",
        case["diagnosis"], case["medicines"], [], "After 5 days if not better",
    )
    png1.save_png(case_dir / "prescription.png")

    # Unreadable bill — heavy blur and noise
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new("RGB", (800, 900), (245, 245, 240))
    draw = ImageDraw.Draw(img)
    font = _load_font(10)
    text = [
        "HEALTH FIRST PHARMACY", "Drug Lic: KA-BLR-2024-001234",
        "Bill No: HFP-1025-0987    Date: 25-Oct-2024",
        "Patient: Sneha Reddy", "Dr: Sunita Reddy",
        "------------------------------------",
        "Azithromycin 500mg  5 tabs  Rs. 450",
        "Paracetamol 650mg  10 tabs  Rs. 150",
        "Total: Rs. 600",
    ]
    y = 40
    for t in text:
        draw.text((40, y), t, fill=DARK_GRAY, font=font)
        y += 22
    # Apply heavy blur
    blurred = img.filter(ImageFilter.GaussianBlur(radius=12))
    # Add noise
    import random
    pixels = blurred.load()
    for _ in range(15000):
        x = random.randint(0, 799)
        y = random.randint(0, 799)
        r, g, b = pixels[x, y][:3] if len(pixels[x, y]) >= 3 else (200, 200, 200)
        pixels[x, y] = (min(r + random.randint(-40, 40), 255),
                        min(g + random.randint(-40, 40), 255),
                        min(b + random.randint(-40, 40), 255))
    blurred.save(str(case_dir / "pharmacy_bill.png"), "PNG")

    # Unreadable PDF — garbled text
    from fpdf import FPDF
    pdf2 = DocPDF()
    pdf2.add_page()
    pdf2.set_font("DejaVu", "", 10)
    garble = "X" * 30 + "  XXXX  " + "X" * 30 + "\n" + "XX  XXXXXXXX  XX\n" + "    XX  XXXX  XX  XXXX  XXXX\n" + "XXXXXXXX  XX  XXXXXXXX  XX  XXXX\n"
    pdf2.multi_cell(w=170, h=8, text=garble * 10)
    pdf2.output(str(case_dir / "pharmacy_bill.pdf"))


def _generate_rejection_case3(case: dict, case_dir: Path):
    """TC003 — Patient name mismatch."""
    # Prescription for Rajesh Kumar
    pdf = build_prescription_pdf(
        case["doctor"], case["reg"], case["doctor_qual"], case.get("hospital", "City Clinic"),
        case["clinic_addr"], case["clinic_phone"],
        "Rajesh Kumar", 39, "Male", case["treatment_date"],
        "Fever since 3 days", "",
        case["diagnosis"], case["medicines"], [],
        "After 5 days",
    )
    _save_pdf(pdf, case_dir / "prescription.pdf")
    png1 = build_prescription_png(
        case["doctor"], case["reg"], case["doctor_qual"], case.get("hospital", "City Clinic"),
        case["clinic_addr"], case["clinic_phone"],
        "Rajesh Kumar", 39, "Male", case["treatment_date"],
        "Fever since 3 days", "",
        case["diagnosis"], case["medicines"], [], "After 5 days",
    )
    png1.save_png(case_dir / "prescription.png")

    # Hospital bill for Arjun Mehta
    bill = build_hospital_bill_pdf(
        case.get("hospital", "City Medical Centre"), case["clinic_addr"],
        case["clinic_phone"], "29AABCT1234A1ZX",
        f"CMC/{case['treatment_date'].replace('-','')}/001", case["treatment_date"],
        "Arjun Mehta", 25, "Male", case["doctor"],
        [{"description": "Consultation Fee", "quantity": 1, "rate": 1000, "gst_pct": 0},
         {"description": "CBC Test", "quantity": 1, "rate": 300, "gst_pct": 0},
         {"description": "Dengue NS1", "quantity": 1, "rate": 200, "gst_pct": 0}],
    )
    _save_pdf(bill, case_dir / "hospital_bill.pdf")
    bill_png = build_hospital_bill_png(
        case.get("hospital", "City Medical Centre"), case["clinic_addr"],
        case["clinic_phone"], "29AABCT1234A1ZX",
        f"CMC/{case['treatment_date'].replace('-','')}/001", case["treatment_date"],
        "Arjun Mehta", 25, "Male", case["doctor"],
        [{"description": "Consultation Fee", "quantity": 1, "rate": 1000, "gst_pct": 0},
         {"description": "CBC Test", "quantity": 1, "rate": 300, "gst_pct": 0},
         {"description": "Dengue NS1", "quantity": 1, "rate": 200, "gst_pct": 0}],
    )
    bill_png.save_png(case_dir / "hospital_bill.png")


def _generate_full_rejection_docs(case: dict, case_dir: Path):
    """Generate full valid documents for rejection cases that need policy evaluation."""
    # Prescription
    pdf = build_prescription_pdf(
        case["doctor"], case["reg"], case["doctor_qual"],
        case.get("hospital", "City Medical Centre"), case["clinic_addr"],
        case["clinic_phone"], case["patient"], case["patient_age"],
        case["patient_gender"], case["treatment_date"],
        case.get("chief_complaint", ""), case.get("vitals", ""),
        case["diagnosis"], case.get("medicines", []),
        case.get("tests_ordered", []), case.get("follow_up", ""),
        case.get("additional_notes", ""),
    )
    _save_pdf(pdf, case_dir / "prescription.pdf")
    png = build_prescription_png(
        case["doctor"], case["reg"], case["doctor_qual"],
        case.get("hospital", "City Medical Centre"), case["clinic_addr"],
        case["clinic_phone"], case["patient"], case["patient_age"],
        case["patient_gender"], case["treatment_date"],
        case.get("chief_complaint", ""), case.get("vitals", ""),
        case["diagnosis"], case.get("medicines", []),
        case.get("tests_ordered", []), case.get("follow_up", ""),
        case.get("additional_notes", ""),
    )
    png.save_png(case_dir / "prescription.png")

    # Hospital Bill
    line_items = case.get("line_items", [])
    if line_items:
        bill = build_hospital_bill_pdf(
            case.get("hospital", "City Medical Centre"), case["clinic_addr"],
            case["clinic_phone"], case.get("gstin", "29AABCT1234A1ZX"),
            f"BILL/{case['treatment_date'].replace('-','')}/{random.randint(100,999)}",
            case["treatment_date"], case["patient"], case["patient_age"],
            case["patient_gender"], case["doctor"], line_items,
        )
        _save_pdf(bill, case_dir / "hospital_bill.pdf")
        bill_png = build_hospital_bill_png(
            case.get("hospital", "City Medical Centre"), case["clinic_addr"],
            case["clinic_phone"], case.get("gstin", "29AABCT1234A1ZX"),
            f"BILL/{case['treatment_date'].replace('-','')}/{random.randint(100,999)}",
            case["treatment_date"], case["patient"], case["patient_age"],
            case["patient_gender"], case["doctor"], line_items,
        )
        bill_png.save_png(case_dir / "hospital_bill.png")


# ── Main Generator ────────────────────────────────────────────────

def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def generate_all():
    print("Generating properly structured medical documents...\n")

    total_files = 0

    # ── PASSING CASES ──────────────────────────────────────────
    print("=== PASSING CASES ===")
    for case in PASSING_CASES:
        case_dir = BASE_DIR / "passing" / case["id"]
        _ensure_dir(case_dir)
        print(f"  {case['id']}: {case['name']}...", end=" ", flush=True)
        count = 0

        # Prescription
        pdf = build_prescription_pdf(
            case["doctor"], case["reg"], case["doctor_qual"],
            case["hospital"], case["clinic_addr"], case["clinic_phone"],
            case["patient"], case["patient_age"], case["patient_gender"],
            case["treatment_date"], case.get("chief_complaint", ""),
            case.get("vitals", ""), case["diagnosis"],
            case.get("medicines", []), case.get("tests_ordered", []),
            case.get("follow_up", ""), case.get("additional_notes", ""),
        )
        _save_pdf(pdf, case_dir / "prescription.pdf")
        png = build_prescription_png(
            case["doctor"], case["reg"], case["doctor_qual"],
            case["hospital"], case["clinic_addr"], case["clinic_phone"],
            case["patient"], case["patient_age"], case["patient_gender"],
            case["treatment_date"], case.get("chief_complaint", ""),
            case.get("vitals", ""), case["diagnosis"],
            case.get("medicines", []), case.get("tests_ordered", []),
            case.get("follow_up", ""), case.get("additional_notes", ""),
        )
        png.save_png(case_dir / "prescription.png")
        count += 2

        # Hospital Bill (or Pharmacy Bill for PHARMACY category)
        line_items = case.get("line_items", [])
        if case["category"] == "PHARMACY":
            pname, paddr, lic, bno, bdate, pn, doc, pmeds, disc, pharm = _pharmacy_data(case)
            bill_pdf = build_pharmacy_bill_pdf(pname, paddr, lic, bno, bdate, pn, doc, pmeds, disc, pharm)
            _save_pdf(bill_pdf, case_dir / "pharmacy_bill.pdf")
            bill_png = build_pharmacy_bill_png(pname, paddr, lic, bno, bdate, pn, doc, pmeds, disc, pharm)
            bill_png.save_png(case_dir / "pharmacy_bill.png")
            count += 2
        elif line_items:
            bill = build_hospital_bill_pdf(
                case["hospital"], case["clinic_addr"], case["clinic_phone"],
                case.get("gstin", ""),
                f"BILL/{case['treatment_date'].replace('-','')}/{random.randint(100,999)}",
                case["treatment_date"], case["patient"], case["patient_age"],
                case["patient_gender"], case["doctor"], line_items,
            )
            _save_pdf(bill, case_dir / "hospital_bill.pdf")
            bill_png = build_hospital_bill_png(
                case["hospital"], case["clinic_addr"], case["clinic_phone"],
                case.get("gstin", ""),
                f"BILL/{case['treatment_date'].replace('-','')}/{random.randint(100,999)}",
                case["treatment_date"], case["patient"], case["patient_age"],
                case["patient_gender"], case["doctor"], line_items,
            )
            bill_png.save_png(case_dir / "hospital_bill.png")
            count += 2

        # Lab Report for DIAGNOSTIC cases
        if case["category"] == "DIAGNOSTIC":
            lab_args = _build_lab_data(case)
            lab_pdf = build_lab_report_pdf(*lab_args)
            _save_pdf(lab_pdf, case_dir / "lab_report.pdf")
            lab_png = build_lab_report_png(*lab_args)
            lab_png.save_png(case_dir / "lab_report.png")
            count += 2

        # Save case metadata
        meta = {
            "case_id": case["id"], "name": case["name"],
            "member_id": case["member"], "claim_category": case["category"],
            "treatment_date": case["treatment_date"], "claimed_amount": case["amount"],
            "hospital_name": case.get("hospital", ""),
            "patient_name": case["patient"], "diagnosis": case["diagnosis"],
            "expected_decision": "APPROVED",
        }
        with open(case_dir / "case_meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        count += 1
        total_files += count
        print(f"({count} files)")

    # ── REJECTION CASES ────────────────────────────────────────
    print("\n=== REJECTION CASES ===")
    for case in REJECTION_CASES:
        case_dir = BASE_DIR / "rejection" / case["id"]
        _ensure_dir(case_dir)
        print(f"  {case['id']}: {case['name']}...", end=" ", flush=True)

        error_type = case.get("error_type", "")

        if error_type == "MISSING_REQUIRED":
            _generate_rejection_case1(case, case_dir)
            count = 4 + 1  # 2 PDFs + 2 PNGs + meta
        elif error_type == "UNREADABLE":
            _generate_rejection_case2(case, case_dir)
            count = 4 + 1
        elif error_type == "PATIENT_MISMATCH":
            _generate_rejection_case3(case, case_dir)
            count = 4 + 1
        else:
            _generate_full_rejection_docs(case, case_dir)
            count = 4 + 1

        # Save case metadata
        rejection_reason = case.get("rejection_reason", error_type)
        meta = {
            "case_id": case["id"], "name": case["name"],
            "member_id": case["member"], "claim_category": case["category"],
            "treatment_date": case["treatment_date"], "claimed_amount": case["amount"],
            "hospital_name": case.get("hospital", ""),
            "patient_name": case.get("patient", ""),
            "diagnosis": case.get("diagnosis", ""),
            "expected_rejection_reason": rejection_reason,
            "scenario": case["scenario"],
        }
        if case.get("claims_history"):
            meta["claims_history"] = case["claims_history"]
        with open(case_dir / "case_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        total_files += count
        print(f"({count} files)")

    print(f"\n{'='*60}")
    print(f"  Total files generated: {total_files}")
    print(f"  Passing cases: {len(PASSING_CASES)} | Rejection cases: {len(REJECTION_CASES)}")
    print(f"  Output directory: {BASE_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    generate_all()
