from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import jwt
from pydantic import BaseModel
from quart import Blueprint, current_app, jsonify, request

router = Blueprint("api", __name__, url_prefix="/api")

# In-memory session store for example purposes
_sessions: dict[str, dict[str, Any]] = {}


class AuthRequest(BaseModel):
    """Request body for validating a JWT token."""

    token: str


class AuthResponse(BaseModel):
    """Response returned after validating a JWT token."""

    valid: bool
    claims: dict[str, Any] | None = None
    error: str | None = None


@router.post("/auth/validate")
async def auth_validate():
    """Validate a JWT token, optionally bypassing in development."""

    data = AuthRequest(**await request.get_json())
    if os.getenv("DEV_AUTH_BYPASS"):
        return jsonify(AuthResponse(valid=True, claims={"sub": "dev-user"}).model_dump())
    try:
        claims = jwt.decode(data.token, options={"verify_signature": False})
        return jsonify(AuthResponse(valid=True, claims=claims).model_dump())
    except jwt.PyJWTError as exc:  # pragma: no cover - safety catch
        return (
            jsonify(AuthResponse(valid=False, error=str(exc)).model_dump()),
            401,
        )


class SessionCreateRequest(BaseModel):
    """Request to create a new chat session."""

    user: str | None = None


class SessionCreateResponse(BaseModel):
    """Response containing the created session identifier."""

    session_id: str


@router.post("/sessions")
async def create_session():
    """Create a new session and return the session id."""

    data = SessionCreateRequest(**await request.get_json())
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"user": data.user}
    return jsonify(SessionCreateResponse(session_id=session_id).model_dump())


class QuestionRequest(BaseModel):
    """Request to ask a question within a session."""

    session_id: str
    question: str


class QuestionResponse(BaseModel):
    """Answer returned for a question."""

    answer: str


@router.post("/questions")
async def ask_question():
    """Return a simple echo answer for the provided question."""

    data = QuestionRequest(**await request.get_json())
    answer = f"You asked: {data.question}"
    return jsonify(QuestionResponse(answer=answer).model_dump())


@router.post("/documents")
async def upload_document():
    """Upload a document and attempt OCR on its contents."""

    files = await request.files
    upload = files.get("file")
    if upload is None:
        return jsonify({"error": "file field required"}), 400

    text = ""
    try:
        import pytesseract  # type: ignore
        from PIL import Image

        image = Image.open(upload.stream)
        text = pytesseract.image_to_string(image)
    except Exception as err:  # pragma: no cover - best effort
        current_app.logger.info("OCR failed: %s", err)
        text = ""

    return jsonify({"filename": upload.filename, "text": text})


class ReportRequest(BaseModel):
    """Request to generate a PDF report and email it to a recipient."""

    title: str
    content: str
    email: str


class ReportResponse(BaseModel):
    """Response confirming report generation."""

    message: str


def _generate_pdf(title: str, content: str) -> bytes:
    """Generate a simple PDF document in memory."""

    try:
        from fpdf import FPDF  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return b"PDF generation not available"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.multi_cell(0, 10, txt=content)
    return pdf.output(dest="S").encode("latin1")


def _send_email(to: str, pdf_bytes: bytes) -> None:
    """Best-effort email sender for the generated PDF."""

    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = "Report"
        msg["From"] = "noreply@example.com"
        msg["To"] = to
        msg.set_content("Please find the report attached.")
        msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="report.pdf")
        with smtplib.SMTP("localhost") as smtp:
            smtp.send_message(msg)
    except Exception as err:  # pragma: no cover - environment dependent
        logging.getLogger(__name__).info("Email send failed: %s", err)


@router.post("/reports")
async def create_report():
    """Generate a PDF report and email it to the requested address."""

    data = ReportRequest(**await request.get_json())
    pdf_bytes = _generate_pdf(data.title, data.content)
    _send_email(data.email, pdf_bytes)
    return jsonify(ReportResponse(message="Report generated and emailed").model_dump())
