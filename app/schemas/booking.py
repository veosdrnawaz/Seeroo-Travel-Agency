from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime
from app.schemas.user import UserResponse
from app.schemas.tour import TourResponse

class BookingCreate(BaseModel):
    tour_id: uuid.UUID = Field(..., description="ID of the tour being booked")
    seats: int = Field(..., gt=0, le=30, description="Number of seats required (1 to 30)")
    pickup_city: str = Field(..., description="Departure city e.g. Attock, Wah, Kamra, Taxila")
    
    # User registration fields (inlined to simplify booking workflow)
    full_name: str = Field(..., min_length=2, max_length=100, description="Lead traveler full name")
    phone: str = Field(..., description="WhatsApp mobile phone number (starts with 03)")
    email: Optional[str] = Field(None, description="Optional email address")

class BookingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tour_id: uuid.UUID
    seats: int
    price_per_head: int
    total_price: int
    pickup_city: str
    booking_status: str  # pending/confirmed/cancelled
    payment_status: str  # unpaid/paid/refunded
    created_at: datetime
    
    user: Optional[UserResponse] = None
    tour: Optional[TourResponse] = None

    model_config = ConfigDict(from_attributes=True)
