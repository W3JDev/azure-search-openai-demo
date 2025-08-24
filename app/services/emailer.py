import os
import smtplib
from email.message import EmailMessage

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)


def send_email_with_pdf(
    to_email: str, subject: str, body: str, pdf_content: bytes, pdf_filename: str = "report.pdf"
) -> None:
    """Send an email with a PDF attachment using TLS.

    Args:
        to_email: Recipient email address.
        subject: Email subject line.
        body: Plain text body of the email.
        pdf_content: PDF file content as bytes.
        pdf_filename: Filename for the attached PDF.
    """
    if not SMTP_SERVER:
        raise ValueError("SMTP_SERVER environment variable is required")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message.set_content(body)

    message.add_attachment(
        pdf_content,
        maintype="application",
        subtype="pdf",
        filename=pdf_filename,
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)
