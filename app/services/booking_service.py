from sqlalchemy.orm import Session
from sqlalchemy import update
from fastapi import HTTPException, status
from app.models.user import User
from app.models.tour import Tour
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.core.security import clean_phone_number, validate_phone_format
import uuid

def get_booking_by_id(db: Session, booking_id: uuid.UUID) -> Booking:
    return db.query(Booking).filter(Booking.id == booking_id).first()

def create_booking(db: Session, booking_data: BookingCreate) -> Booking:
    # 1. Phone number validation and normalization
    phone_cleaned = clean_phone_number(booking_data.phone)
    if not validate_phone_format(phone_cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Pakistani phone number format. Must start with 03 and have 11 digits."
        )

    # 2. Get or create User in transaction
    user = db.query(User).filter(User.phone == phone_cleaned).first()
    if not user:
        user = User(
            full_name=booking_data.full_name,
            phone=phone_cleaned,
            email=booking_data.email,
            preferred_city=booking_data.pickup_city
        )
        db.add(user)
        db.flush()  # Populates user.id without committing

    # 3. Retrieve Tour
    tour = db.query(Tour).filter(Tour.id == booking_data.tour_id).first()
    if not tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target tour not found."
        )

    # 4. Atomic seat deduction (concurrency check to prevent overbooking)
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
            detail=f"Overbooking rejected. Only {tour.available_seats} seats remaining on this tour."
        )

    # 5. Calculate group discounts (5-9 seats: 5% off, 10+ seats: 10% off)
    discount_pct = 0
    if booking_data.seats >= 10:
        discount_pct = 10
    elif booking_data.seats >= 5:
        discount_pct = 5
        
    raw_total = booking_data.seats * tour.price_per_head
    discount_amt = int(raw_total * (discount_pct / 100))
    final_total = raw_total - discount_amt

    # 6. Save Booking
    db_booking = Booking(
        user_id=user.id,
        tour_id=tour.id,
        seats=booking_data.seats,
        price_per_head=tour.price_per_head,
        total_price=final_total,
        pickup_city=booking_data.pickup_city,
        booking_status="pending",
        payment_status="unpaid"
    )
    db.add(db_booking)
    
    try:
        db.commit()
        db.refresh(db_booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database transaction error: {str(e)}"
        )
        
    return db_booking
