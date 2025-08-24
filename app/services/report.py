"""Utilities for generating PDF reports.

This module uses ReportLab to produce PDFs summarizing session data and
related document references.
"""

from collections.abc import Iterable, Mapping
from io import BytesIO


def build_pdf_report(session_data: Mapping[str, str], document_refs: Iterable[str]) -> bytes:
    """Create a PDF report for a chat session.

    Parameters
    ----------
    session_data:
        Key/value pairs describing the session (e.g. user, timestamp).
    document_refs:
        Iterable of document identifiers associated with the session.

    Returns
    -------
    bytes
        Binary PDF content suitable for download or emailing.

    Raises
    ------
    RuntimeError
        If the ReportLab library is not installed.
    """

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:  # pragma: no cover - dependency not available in tests
        raise RuntimeError("ReportLab is required to generate PDF reports") from exc

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 72  # 1 inch margin
    y = height - margin

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, y, "Session Report")
    y -= 24

    pdf.setFont("Helvetica", 12)
    for key, value in session_data.items():
        pdf.drawString(margin, y, f"{key}: {value}")
        y -= 14
        if y < margin:
            pdf.showPage()
            y = height - margin
            pdf.setFont("Helvetica", 12)

    y -= 10
    if y < margin:
        pdf.showPage()
        y = height - margin
        pdf.setFont("Helvetica", 12)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin, y, "Document References")
    y -= 20
    pdf.setFont("Helvetica", 12)

    for ref in document_refs:
        pdf.drawString(margin, y, f"- {ref}")
        y -= 14
        if y < margin:
            pdf.showPage()
            y = height - margin
            pdf.setFont("Helvetica", 12)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
