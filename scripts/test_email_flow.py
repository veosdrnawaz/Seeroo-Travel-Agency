"""
test_email_flow.py
──────────────────
Phase 6 integration test for the transactional email delivery system.

Tests:
  1. Creates a test booking (uses test DB or main DB).
  2. Verifies:
     a. PDF invoice is generated in-memory without errors.
     b. Email send is attempted (real SMTP if configured, mock fallback).
     c. email_logs entry is created for the booking.
  3. Simulates SMTP failure (monkeypatches _smtp_send to raise).
  4. Verifies:
     a. Booking creation still succeeds.
     b. email_logs row is created with status "failed".

Usage:
  python scripts/test_email_flow.py

Environment:
  SMTP_USER / SMTP_PASS must be set in .env for a real send test.
  Without credentials the test runs in "skip-send" mode and still
  verifies the DB log entry is created with status "failed".
"""

import io
import os
import sys
import uuid

# ── Force UTF-8 output on Windows terminals ────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from unittest.mock import patch

# ── Ensure project root is importable ─────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.tour import Tour
from app.models.booking import Booking
from app.models.email_log import EmailLog
from app.schemas.booking import BookingCreate
from app.services import booking_service
from app.services.pdf_service import generate_invoice_pdf

# ── Test database (isolated from production) ──────────────────────────────────
TEST_DB_URL = f"sqlite:///{os.path.join(ROOT, 'test_seeroo_travels.db')}"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine)

SEEDED_TOUR_ID = "a1b2c3d4-0001-0001-0001-000000000001"
SEEDED_TOUR_ID_2 = "a1b2c3d4-0001-0001-0001-000000000002"

PASS  = "✅ PASS"
FAIL  = "❌ FAIL"
SKIP  = "⚠️  SKIP"
SEP   = "─" * 60


def setup_test_db():
    """Create all tables and seed one test tour."""
    Base.metadata.create_all(bind=engine)

    db = TestSession()
    try:
        # Ensure test tour exists
        tour = db.query(Tour).filter(Tour.id == uuid.UUID(SEEDED_TOUR_ID)).first()
        if not tour:
            tour = Tour(
                id=uuid.UUID(SEEDED_TOUR_ID),
                tour_name="Shogran Valley Test Tour",
                date="25 July 2026",
                price_per_head=4500,
                total_seats=30,
                available_seats=30,
                category="Family Short Tour",
            )
            db.add(tour)
            db.commit()
        print(f"  Tour ready: {tour.tour_name} (ID={str(tour.id)[:8]}…)")
    finally:
        db.close()


def cleanup_test_data(db, phone: str):
    """Remove test user/bookings/email_logs created during this run."""
    user = db.query(User).filter(User.phone == phone).first()
    if user:
        for b in user.bookings:
            for el in b.email_logs:
                db.delete(el)
            db.delete(b)
        db.delete(user)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — PDF Invoice Generation
# ─────────────────────────────────────────────────────────────────────────────
def test_pdf_generation():
    print(f"\n{SEP}")
    print("TEST 1: Server-side PDF generation")
    print(SEP)
    try:
        buf = generate_invoice_pdf(
            booking_id=str(uuid.uuid4()),
            customer_name="Test User",
            tour_name="Shogran Valley Tour",
            tour_date="25 July 2026",
            pickup_city="Attock",
            seats=3,
            price_per_head=4500,
            total_paid=13500,
            contact_number="03001234567",
        )
        assert isinstance(buf, io.BytesIO), "Expected BytesIO"
        data = buf.read()
        assert len(data) > 1000, f"PDF too small ({len(data)} bytes) — likely empty"
        assert data[:4] == b"%PDF", "Generated file is not a valid PDF"
        print(f"  PDF size: {len(data):,} bytes")
        print(f"  {PASS} PDF generated successfully in-memory")
        return True
    except Exception as e:
        print(f"  {FAIL} PDF generation error: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Full booking flow (real/skip SMTP) + email_logs entry
# ─────────────────────────────────────────────────────────────────────────────
def test_booking_with_email_log():
    print(f"\n{SEP}")
    print("TEST 2: Booking creation → email dispatch → email_logs entry")
    print(SEP)

    phone = "03011112200"
    db = TestSession()

    # clean up any stale test data
    cleanup_test_data(db, phone)

    booking_data = BookingCreate(
        full_name="Ahmad Test User",
        phone=phone,
        email="testuser@example.com",
        tour_id=uuid.UUID(SEEDED_TOUR_ID),
        seats=2,
        pickup_city="Attock",
    )

    result_booking = None
    try:
        result_booking = booking_service.create_booking(db, booking_data)
        print(f"  Booking ID   : {str(result_booking.id)[:8].upper()}…")
        print(f"  Seats booked : {result_booking.seats}")
        print(f"  Total price  : Rs. {result_booking.total_price:,}")
        print(f"  {PASS} Booking created successfully")
    except Exception as e:
        print(f"  {FAIL} Booking creation failed: {e}")
        db.close()
        return False

    # Check email_logs
    import time; time.sleep(0.3)   # let any async writes settle
    db.expire_all()
    log = (
        db.query(EmailLog)
        .filter(EmailLog.booking_id == result_booking.id)
        .first()
    )

    if log:
        print(f"  Email log    : status={log.status}  recipient={log.recipient_email}")
        if log.status == "sent":
            print(f"  {PASS} email_logs entry created — status=sent")
        else:
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_pass = os.getenv("SMTP_PASS", "")
            if not smtp_user or not smtp_pass:
                print(f"  {SKIP} SMTP not configured — expected 'failed' log: '{log.error_message}'")
            else:
                print(f"  ⚠️  email_logs status=failed (SMTP configured but send failed): {log.error_message}")
    else:
        print(f"  {FAIL} No email_logs entry found for booking")
        db.close()
        return False

    db.close()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Simulated SMTP failure: booking succeeds, log is 'failed'
# ─────────────────────────────────────────────────────────────────────────────
def test_smtp_failure_isolation():
    print(f"\n{SEP}")
    print("TEST 3: SMTP failure — booking must still succeed, log must be 'failed'")
    print(SEP)

    phone = "03022223300"
    db = TestSession()
    cleanup_test_data(db, phone)

    booking_data = BookingCreate(
        full_name="SMTP Fail Test",
        phone=phone,
        email="smtpfail@example.com",
        tour_id=uuid.UUID(SEEDED_TOUR_ID),
        seats=1,
        pickup_city="Wah",
    )

    import smtplib

    def mock_smtp_fail(*args, **kwargs):
        raise smtplib.SMTPException("Simulated SMTP server unreachable")

    result_booking = None
    with patch("app.services.email_service._smtp_send", side_effect=mock_smtp_fail):
        # Also ensure SMTP_USER/SMTP_PASS are non-empty so we reach _smtp_send
        with patch.dict(os.environ, {"SMTP_USER": "test@example.com", "SMTP_PASS": "testpass"}):
            # Reload env vars inside email_service module
            import importlib
            import app.services.email_service as es
            es._SMTP_USER = "test@example.com"
            es._SMTP_PASS = "testpass"
            try:
                result_booking = booking_service.create_booking(db, booking_data)
                print(f"  Booking ID   : {str(result_booking.id)[:8].upper()}…")
                print(f"  {PASS} Booking succeeded despite SMTP failure ✓")
            except Exception as e:
                print(f"  {FAIL} Booking raised exception on SMTP failure (WRONG!): {e}")
                db.close()
                return False
            finally:
                # Restore actual env
                es._SMTP_USER = os.getenv("SMTP_USER", "")
                es._SMTP_PASS = os.getenv("SMTP_PASS", "")

    # Check email_logs for 'failed' entry
    import time; time.sleep(0.3)
    db.expire_all()
    log = (
        db.query(EmailLog)
        .filter(EmailLog.booking_id == result_booking.id)
        .first()
    )

    if not log:
        print(f"  {FAIL} No email_logs entry found after SMTP failure")
        db.close()
        return False

    if log.status == "failed":
        print(f"  Email log    : status=failed  error='{log.error_message}'")
        print(f"  {PASS} email_logs correctly records 'failed' on SMTP error")
    else:
        print(f"  {FAIL} Expected status='failed', got '{log.status}'")
        db.close()
        return False

    db.close()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  PHASE 6 — TRANSACTIONAL EMAIL FLOW TEST SUITE")
    print("=" * 60)

    print("\n[Setup] Initialising test database…")
    setup_test_db()

    results = {
        "PDF Generation"            : test_pdf_generation(),
        "Booking + Email Log"       : test_booking_with_email_log(),
        "SMTP Failure Isolation"    : test_smtp_failure_isolation(),
    }

    print(f"\n{SEP}")
    print("SUMMARY")
    print(SEP)
    all_pass = True
    for name, passed in results.items():
        status = PASS if passed else FAIL
        print(f"  {status}  {name}")
        if not passed:
            all_pass = False

    print(SEP)
    if all_pass:
        print("  ✅ ALL TESTS PASSED — Phase 6 email layer is production-ready.")
    else:
        print("  ❌ SOME TESTS FAILED — Review output above.")
    print()
