"""
email_service.py
────────────────
Sends transactional booking confirmation emails via SMTP (Gmail or any TLS provider).

Credentials are loaded from environment variables:
  SMTP_HOST  (default: smtp.gmail.com)
  SMTP_PORT  (default: 587)
  SMTP_USER  — sender address / login
  SMTP_PASS  — app password or SMTP auth password

Returns a structured dict: { "success": bool, "error": str|None }

Rules:
  • Uses STARTTLS (port 587 by default).
  • Timeout: 10 seconds per SMTP operation.
  • Retries: up to 2 retries on transient SMTP failures (not on auth errors).
  • Thread-safe: stateless function, no module-level SMTP connection held open.
  • Never raises — all exceptions are caught and returned in the response dict.
"""

import io
import logging
import os
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

logger = logging.getLogger("seeroo_email")

# ── Configuration ─────────────────────────────────────────────────────────────
_SMTP_HOST   = os.getenv("SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER   = os.getenv("SMTP_USER", "")
_SMTP_PASS   = os.getenv("SMTP_PASS", "")

# Non-retryable SMTP error codes (permanent failures)
_FATAL_CODES = {535, 534, 530, 550, 551, 553}

# Path to HTML template
_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "booking_confirmation.html"


def _load_template() -> str:
    """Load the HTML email template from disk."""
    if not _TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Email template not found at: {_TEMPLATE_PATH}")
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def _render_template(
    booking_id: str,
    customer_name: str,
    tour_name: str,
    tour_date: str,
    pickup_city: str,
    seats: int,
    price_per_head: int,
    total_paid: int,
    contact_number: str,
) -> str:
    """
    Substitute named {placeholder} tokens in the HTML template.

    Uses regex instead of str.format() to avoid conflicts with CSS
    curly braces (e.g., `{box-sizing}`, `{display}`) that would cause
    KeyError or ValueError when processed by Python's str.format().

    Only tokens matching our explicit field names are replaced.
    """
    import re

    html = _load_template()

    replacements = {
        "booking_id":      booking_id,
        "customer_name":   customer_name,
        "tour_name":       tour_name,
        "tour_date":       tour_date,
        "pickup_city":     pickup_city,
        "seats":           str(seats),
        "price_per_head":  f"{price_per_head:,}",
        "total_paid":      f"{total_paid:,}",
        "contact_number":  contact_number,
    }

    # Match only exact placeholder tokens we know about
    pattern = re.compile(r"\{(" + "|".join(re.escape(k) for k in replacements) + r")\}")
    return pattern.sub(lambda m: replacements[m.group(1)], html)


def _build_message(
    recipient_email: str,
    booking_id: str,
    customer_name: str,
    tour_name: str,
    tour_date: str,
    pickup_city: str,
    seats: int,
    price_per_head: int,
    total_paid: int,
    contact_number: str,
    pdf_buffer: Optional[io.BytesIO],
) -> MIMEMultipart:
    """Assemble a MIME multipart email with HTML body and optional PDF attachment."""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"✅ Booking Confirmed – {tour_name} | Seeroo Travels Attock"
    msg["From"]    = f"Seeroo Travels Attock <{_SMTP_USER}>"
    msg["To"]      = recipient_email
    msg["Reply-To"] = _SMTP_USER

    # ── HTML body ──────────────────────────────────────────────────────────────
    html_body = _render_template(
        booking_id=booking_id,
        customer_name=customer_name,
        tour_name=tour_name,
        tour_date=tour_date,
        pickup_city=pickup_city,
        seats=seats,
        price_per_head=price_per_head,
        total_paid=total_paid,
        contact_number=contact_number,
    )

    # Wrap in alternative part (plain text fallback → HTML)
    alt_part = MIMEMultipart("alternative")
    plain_text = (
        f"Booking Confirmed – Seeroo Travels Attock\n\n"
        f"Booking ID   : {booking_id}\n"
        f"Customer     : {customer_name}\n"
        f"Tour         : {tour_name}\n"
        f"Date         : {tour_date}\n"
        f"Pickup City  : {pickup_city}\n"
        f"Seats        : {seats}\n"
        f"Price/Head   : Rs. {price_per_head:,}\n"
        f"Total Paid   : Rs. {total_paid:,}\n"
        f"Contact      : {contact_number}\n\n"
        "Please present this email at the pickup point. "
        "The invoice PDF is attached."
    )
    alt_part.attach(MIMEText(plain_text, "plain", "utf-8"))
    alt_part.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt_part)

    # ── PDF attachment ─────────────────────────────────────────────────────────
    if pdf_buffer is not None:
        pdf_buffer.seek(0)
        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        safe_id = booking_id[:8].upper()
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"Seeroo_Invoice_{safe_id}.pdf",
        )
        msg.attach(attachment)

    return msg


def _smtp_send(msg: MIMEMultipart, recipient_email: str) -> None:
    """Open SMTP connection, authenticate, and send. Raises on failure."""
    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(_SMTP_USER, _SMTP_PASS)
        server.sendmail(_SMTP_USER, [recipient_email], msg.as_string())


def send_booking_confirmation(
    recipient_email: str,
    booking_id: str,
    customer_name: str,
    tour_name: str,
    tour_date: str,
    pickup_city: str,
    seats: int,
    price_per_head: int,
    total_paid: int,
    contact_number: str,
    pdf_buffer: Optional[io.BytesIO] = None,
) -> dict:
    """
    Send a booking confirmation email with an optional PDF invoice attachment.

    Returns:
        { "success": True, "error": None }          on success
        { "success": False, "error": "<reason>" }   on failure
    """
    # ── Pre-flight guard: no credentials configured ────────────────────────────
    if not _SMTP_USER or not _SMTP_PASS:
        msg = "SMTP credentials not configured (SMTP_USER / SMTP_PASS missing in .env)."
        logger.warning(msg)
        return {"success": False, "error": msg}

    if not recipient_email or "@" not in recipient_email:
        msg = f"Invalid recipient email address: '{recipient_email}'."
        logger.warning(msg)
        return {"success": False, "error": msg}

    # ── Build MIME message once ────────────────────────────────────────────────
    try:
        mime_msg = _build_message(
            recipient_email=recipient_email,
            booking_id=booking_id,
            customer_name=customer_name,
            tour_name=tour_name,
            tour_date=tour_date,
            pickup_city=pickup_city,
            seats=seats,
            price_per_head=price_per_head,
            total_paid=total_paid,
            contact_number=contact_number,
            pdf_buffer=pdf_buffer,
        )
    except Exception as build_err:
        logger.error(f"[email] Failed to build MIME message: {build_err}")
        return {"success": False, "error": f"Message build error: {str(build_err)}"}

    # ── Retry loop (max 2 retries = 3 total attempts) ─────────────────────────
    max_retries = 2
    last_error  = ""

    for attempt in range(max_retries + 1):
        try:
            _smtp_send(mime_msg, recipient_email)
            logger.info(
                f"[email] Confirmation sent to '{recipient_email}' "
                f"(booking={booking_id[:8]}) on attempt {attempt + 1}."
            )
            return {"success": True, "error": None}

        except smtplib.SMTPAuthenticationError as auth_err:
            # Authentication errors are permanent — do NOT retry
            last_error = f"SMTP authentication failed: {auth_err}"
            logger.error(f"[email] {last_error}")
            return {"success": False, "error": last_error}

        except smtplib.SMTPRecipientsRefused as refused_err:
            last_error = f"Recipient refused: {refused_err}"
            logger.error(f"[email] {last_error}")
            return {"success": False, "error": last_error}

        except smtplib.SMTPException as smtp_err:
            last_error = f"SMTP error: {smtp_err}"
            logger.warning(
                f"[email] Attempt {attempt + 1}/{max_retries + 1} failed – {last_error}"
            )

        except OSError as net_err:
            last_error = f"Network error: {net_err}"
            logger.warning(
                f"[email] Attempt {attempt + 1}/{max_retries + 1} failed – {last_error}"
            )

        except Exception as generic_err:
            last_error = f"Unexpected error: {generic_err}"
            logger.error(f"[email] {last_error}")
            return {"success": False, "error": last_error}

        # Back-off before retry (1s, 2s)
        if attempt < max_retries:
            time.sleep(attempt + 1)

    logger.error(
        f"[email] All {max_retries + 1} attempts exhausted for '{recipient_email}'. "
        f"Last error: {last_error}"
    )
    return {"success": False, "error": last_error}
