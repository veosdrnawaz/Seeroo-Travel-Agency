import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID
from app.db.base import Base

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True)
    seats = Column(Integer, nullable=False)
    price_per_head = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    pickup_city = Column(String, nullable=False)
    booking_status = Column(String, default="pending", nullable=False)  # pending/confirmed/cancelled
    payment_status = Column(String, default="unpaid", nullable=False)  # unpaid/paid/refunded
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    tour = relationship("Tour", back_populates="bookings")
    email_logs = relationship("EmailLog", back_populates="booking", cascade="all, delete-orphan")
