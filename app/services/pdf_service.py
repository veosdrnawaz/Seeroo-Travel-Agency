"""
pdf_service.py
──────────────
Generates an A4-formatted invoice PDF entirely in-memory using ReportLab.
Returns a BytesIO object ready to be attached to an email.

NO filesystem writes occur here.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Brand colour palette ─────────────────────────────────────────────────────
FOREST_GREEN   = colors.HexColor("#1a4a1a")
EMERALD        = colors.HexColor("#2d7a2d")
LIGHT_GREEN    = colors.HexColor("#f0fdf0")
BORDER_GREEN   = colors.HexColor("#c8e6c8")
SUNSET_ORANGE  = colors.HexColor("#f97316")
TEXT_DARK      = colors.HexColor("#1a2e1a")
TEXT_MUTED     = colors.HexColor("#5a7a5a")
WHITE          = colors.white


def _styles() -> dict:
    """Return a dict of pre-configured ParagraphStyles."""
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "brand",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "tagline": ParagraphStyle(
            "tagline",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#c8e6c8"),
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "section_label": ParagraphStyle(
            "section_label",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),
        "field_label": ParagraphStyle(
            "field_label",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=TEXT_MUTED,
            alignment=TA_LEFT,
        ),
        "field_value": ParagraphStyle(
            "field_value",
            fontName="Helvetica",
            fontSize=9,
            textColor=TEXT_DARK,
            alignment=TA_LEFT,
        ),
        "total_label": ParagraphStyle(
            "total_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#a3d9a3"),
            alignment=TA_LEFT,
        ),
        "total_value": ParagraphStyle(
            "total_value",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=WHITE,
            alignment=TA_RIGHT,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
        ),
        "note": ParagraphStyle(
            "note",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor("#7c3a1a"),
            alignment=TA_LEFT,
        ),
        "booking_id": ParagraphStyle(
            "booking_id",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#166534"),
            alignment=TA_LEFT,
        ),
    }


def generate_invoice_pdf(
    booking_id: str,
    customer_name: str,
    tour_name: str,
    tour_date: str,
    pickup_city: str,
    seats: int,
    price_per_head: int,
    total_paid: int,
    contact_number: str,
) -> io.BytesIO:
    """
    Render a full A4 invoice and return it as an in-memory BytesIO buffer.

    Parameters match the fields in booking_confirmation.html template.
    """
    buffer = io.BytesIO()
    st = _styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=f"Seeroo Travels – Invoice #{booking_id[:8].upper()}",
        author="Seeroo Travels Attock",
    )

    story = []

    # ── Header banner ─────────────────────────────────────────────────────────
    header_data = [
        [Paragraph("SEEROO TRAVELS ATTOCK", st["brand"])],
        [Paragraph("ESCAPE  ·  EXPLORE  ·  EXPERIENCE", st["tagline"])],
    ]
    header_table = Table(header_data, colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FOREST_GREEN),
        ("TOPPADDING",    (0, 0), (-1, 0), 16),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, -1), (-1, -1), 3, SUNSET_ORANGE),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Invoice title row ─────────────────────────────────────────────────────
    title_data = [[
        Paragraph("BOOKING INVOICE", ParagraphStyle(
            "invoice_title",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=FOREST_GREEN,
            alignment=TA_LEFT,
        )),
        Paragraph(
            f"Booking ID: #{booking_id[:8].upper()}<br/>"
            f"Issued: {datetime.now().strftime('%d %b %Y, %H:%M')}",
            ParagraphStyle(
                "meta",
                fontName="Helvetica",
                fontSize=8,
                textColor=TEXT_MUTED,
                alignment=TA_RIGHT,
            ),
        ),
    ]]
    title_table = Table(title_data, colWidths=[doc.width * 0.55, doc.width * 0.45])
    title_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
    ]))
    story.append(title_table)
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_GREEN, spaceAfter=10))

    # ── Customer & Tour details grid ──────────────────────────────────────────
    def _row(label: str, value: str):
        return [
            Paragraph(label, st["field_label"]),
            Paragraph(str(value), st["field_value"]),
        ]

    rows = [
        [Paragraph("BOOKING DETAILS", st["section_label"]), Paragraph("", st["section_label"])],
        _row("Customer Name", customer_name),
        _row("Contact Number", contact_number),
        _row("Tour Name", tour_name),
        _row("Tour Date", tour_date),
        _row("Pickup City", pickup_city),
        _row("Seats Booked", f"{seats} seat(s)"),
        _row("Price per Head", f"Rs. {price_per_head:,}"),
    ]

    detail_table = Table(rows, colWidths=[doc.width * 0.40, doc.width * 0.60])
    detail_table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND", (0, 0), (-1, 0), FOREST_GREEN),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING",  (0, 0), (-1, 0), 8),
        ("SPAN", (0, 0), (-1, 0)),
        # Data rows
        ("BACKGROUND", (0, 1), (-1, -1), LIGHT_GREEN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREEN, WHITE]),
        ("TOPPADDING",    (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 1), (-1, -1), 0.5, BORDER_GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Total row ─────────────────────────────────────────────────────────────
    total_data = [[
        Paragraph("TOTAL AMOUNT DUE", st["total_label"]),
        Paragraph(f"Rs. {total_paid:,}", st["total_value"]),
    ]]
    total_table = Table(total_data, colWidths=[doc.width * 0.55, doc.width * 0.45])
    total_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), FOREST_GREEN),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (0, 0), (-1, 0), 3, SUNSET_ORANGE),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Payment reminder ──────────────────────────────────────────────────────
    note_data = [[
        Paragraph(
            "⚠  PAYMENT REMINDER: Full payment must be completed at the pickup point "
            "before departure. Please arrive 15 minutes early. This invoice is your "
            "proof of reservation.",
            st["note"],
        )
    ]]
    note_table = Table(note_data, colWidths=[doc.width])
    note_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
        ("LINEALL", (0, 0), (-1, -1), 0.5, SUNSET_ORANGE),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(note_table)
    story.append(Spacer(1, 1 * cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GREEN))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Seeroo Travels Attock  ·  Domestic Day Tours & Family Getaways<br/>"
        "Serving Attock · Wah · Kamra · Taxila",
        st["footer"],
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer
