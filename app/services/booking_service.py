"""
booking_service.py
──────────────────
Handles booking creation with:
  - Phone validation + normalisation
  - Atomic seat deduction (prevents overbooking)
  - Group discount calculation (5-9 seats: 5%, 10+: 10%)
  - Server-side PDF invoice generation (ReportLab)
  - Transactional email dispatch (SMTP)
  - Email attempt logging to email_logs table

CRITICAL RULES:
  • Email failure NEVER rolls back or blocks the booking.
  • booking_service NEVER raises on email/PDF errors.
  • email_logs always stores an entry (sent or failed).
"""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.security import clean_phone_number, validate_phone_format
from app.models.booking import Booking
from app.models.email_log import EmailLog
from app.models.tour import Tour
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.services.email_service import send_booking_confirmation
from app.services.pdf_service import generate_invoice_pdf

logger = logging.getLogger("seeroo_booking")


def get_booking_by_id(db: Session, booking_id: uuid.UUID) -> Booking:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def _log_email_attempt(
    db: Session,
    booking_id: uuid.UUID,
    recipient_email: str,
    result: dict,
) -> None:
    """
    Persist one row in email_logs for each dispatch attempt.
    This function never raises — any DB error is swallowed and logged.
    """
    try:
        log_entry = EmailLog(
            booking_id=booking_id,
            recipient_email=recipient_email,
            status="sent" if result.get("success") else "failed",
            error_message=result.get("error"),
        )
        db.add(log_entry)
        db.commit()
        logger.info(
            f"[email_log] booking={str(booking_id)[:8]} "
            f"recipient={recipient_email} status={log_entry.status}"
        )
    except Exception as log_err:
        logger.error(f"[email_log] Failed to write email log entry: {log_err}")


def create_booking(db: Session, booking_data: BookingCreate) -> Booking:
    # ── 1. Phone validation & normalisation ───────────────────────────────────
    phone_cleaned = clean_phone_number(booking_data.phone)
    if not validate_phone_format(phone_cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Pakistani phone number format. Must start with 03 and have 11 digits.",
        )

    # ── 2. Get or create User ─────────────────────────────────────────────────
    user = db.query(User).filter(User.phone == phone_cleaned).first()
    if not user:
        user = User(
            full_name=booking_data.full_name,
            phone=phone_cleaned,
            email=booking_data.email,
            preferred_city=booking_data.pickup_city,
        )
        db.add(user)
        db.flush()  # Populate user.id without committing

    # ── 3. Retrieve Tour ──────────────────────────────────────────────────────
    tour = db.query(Tour).filter(Tour.id == booking_data.tour_id).first()
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target tour not found.",
        )

    # ── 4. Atomic seat deduction ──────────────────────────────────────────────
    stmt = (
        update(Tour)
        .where(Tour.id == booking_data.tour_id)
        .where(Tour.available_seats >= booking_data.seats)
        .values(available_seats=Tour.available_seats - booking_data.seats)
    )
    result = db.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Overbooking rejected. Only {tour.available_seats} seats remaining on this tour.",
        )

    # ── 5. Group discount calculation ─────────────────────────────────────────
    discount_pct = 0
    if booking_data.seats >= 10:
        discount_pct = 10
    elif booking_data.seats >= 5:
        discount_pct = 5

    raw_total    = booking_data.seats * tour.price_per_head
    discount_amt = int(raw_total * (discount_pct / 100))
    final_total  = raw_total - discount_amt

    # ── 6. Persist Booking ────────────────────────────────────────────────────
    db_booking = Booking(
        user_id=user.id,
        tour_id=tour.id,
        seats=booking_data.seats,
        price_per_head=tour.price_per_head,
        total_price=final_total,
        pickup_city=booking_data.pickup_city,
        booking_status="pending",
        payment_status="unpaid",
    )
    db.add(db_booking)

    try:
        db.commit()
        db.refresh(db_booking)
        # Eagerly refresh associated objects before session might be closed by caller
        db.refresh(user)
        db.refresh(tour)
    except Exception as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database transaction error: {str(db_err)}",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # PHASE 6: Post-commit email pipeline
    # Everything below is fire-and-log — it MUST NOT raise or affect the booking.
    # ──────────────────────────────────────────────────────────────────────────

    recipient_email = user.email or ""

    # ── 7. Generate PDF invoice in-memory ─────────────────────────────────────
    pdf_buffer = None
    try:
        pdf_buffer = generate_invoice_pdf(
            booking_id=str(db_booking.id),
            customer_name=user.full_name,
            tour_name=tour.tour_name,
            tour_date=tour.date,
            pickup_city=db_booking.pickup_city,
            seats=db_booking.seats,
            price_per_head=db_booking.price_per_head,
            total_paid=db_booking.total_price,
            contact_number=user.phone,
        )
        logger.info(f"[pdf] Invoice generated for booking {str(db_booking.id)[:8]}.")
    except Exception as pdf_err:
        logger.error(f"[pdf] PDF generation failed for booking {str(db_booking.id)[:8]}: {pdf_err}")
        # pdf_buffer stays None — email will still send but without attachment

    # ── 8. Send confirmation email ────────────────────────────────────────────
    if not recipient_email:
        logger.info(
            f"[email] No email on file for booking {str(db_booking.id)[:8]} — skipping dispatch."
        )
        # Log skipped as "failed" with informative error so admin dashboards catch it
        _log_email_attempt(
            db,
            db_booking.id,
            recipient_email="NO_EMAIL",
            result={"success": False, "error": "Customer has no email address on file."},
        )
    else:
        email_result = send_booking_confirmation(
            recipient_email=recipient_email,
            booking_id=str(db_booking.id),
            customer_name=user.full_name,
            tour_name=tour.tour_name,
            tour_date=tour.date,
            pickup_city=db_booking.pickup_city,
            seats=db_booking.seats,
            price_per_head=db_booking.price_per_head,
            total_paid=db_booking.total_price,
            contact_number=user.phone,
            pdf_buffer=pdf_buffer,
        )

        if email_result["success"]:
            logger.info(
                f"[email] Confirmation email delivered to '{recipient_email}' "
                f"for booking {str(db_booking.id)[:8]}."
            )
        else:
            logger.warning(
                f"[email] Email failed for booking {str(db_booking.id)[:8]}: "
                f"{email_result.get('error')}"
            )

        # ── 9. Write email_logs entry ─────────────────────────────────────────
        _log_email_attempt(db, db_booking.id, recipient_email, email_result)

    return db_booking
