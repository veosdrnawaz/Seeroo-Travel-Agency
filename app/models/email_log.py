import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.types import UUID
from app.db.base import Base


class EmailLog(Base):
    """
    Audit log for every transactional email dispatch attempt.
    A row is written for every attempt regardless of success or failure.
    """
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_email = Column(String, nullable=False)
    status = Column(String, nullable=False)          # "sent" | "failed"
    error_message = Column(Text, nullable=True)      # null when sent
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship (optional — useful for admin queries)
    booking = relationship("Booking", back_populates="email_logs")
