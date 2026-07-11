from pydantic import BaseModel, Field, ConfigDict
import uuid
from datetime import datetime

class TourBase(BaseModel):
    tour_name: str = Field(..., description="Name of the trip location")
    date: str = Field(..., description="Trip date, e.g. 18 July 2026")
    price_per_head: int = Field(..., gt=0, description="Price per traveler in PKR")
    total_seats: int = Field(..., gt=0, description="Total seating capacity")
    available_seats: int = Field(..., ge=0, description="Currently remaining open seats")
    category: str = Field(..., description="Tour category, e.g. Family Short Tour")

class TourCreate(TourBase):
    pass

class TourResponse(TourBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
