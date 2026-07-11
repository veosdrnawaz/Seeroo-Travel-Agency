from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
from app.db.session import get_db
from app.schemas.booking import BookingResponse, BookingCreate
from app.services import booking_service

from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/bookings", tags=["Bookings"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def book_seats(booking_data: BookingCreate, db: Session = Depends(get_db)):
    return booking_service.create_booking(db, booking_data)

@router.get("/{booking_id}", response_model=BookingResponse)
def read_booking(booking_id: uuid.UUID, db: Session = Depends(get_db)):
    db_booking = booking_service.get_booking_by_id(db, booking_id)
    if not db_booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found."
        )
    return db_booking
