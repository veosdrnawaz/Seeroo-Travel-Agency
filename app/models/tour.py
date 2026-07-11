import uuid
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID
from app.db.base import Base

class Tour(Base):
    __tablename__ = "tours"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_name = Column(String, index=True, nullable=False)
    date = Column(String, nullable=False)  # e.g., "18 July 2026"
    price_per_head = Column(Integer, nullable=False)
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    category = Column(String, nullable=False)  # e.g., "Family Short Tour"
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    bookings = relationship("Booking", back_populates="tour", cascade="all, delete-orphan")
