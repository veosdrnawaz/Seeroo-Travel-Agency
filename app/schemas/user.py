from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime

class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the traveler")
    phone: str = Field(..., description="WhatsApp or contact phone number (11 digits e.g. 03001234567)")
    email: Optional[EmailStr] = Field(None, description="Optional email address")
    preferred_city: str = Field(..., description="Departure city e.g. Attock, Wah, Kamra, Taxila")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
