from sqlalchemy.orm import Session
from app.models.tour import Tour
from app.schemas.tour import TourCreate
import uuid
from typing import List, Optional

def get_tours(db: Session) -> List[Tour]:
    return db.query(Tour).all()

def get_tour_by_id(db: Session, tour_id: uuid.UUID) -> Optional[Tour]:
    return db.query(Tour).filter(Tour.id == tour_id).first()

def create_tour(db: Session, tour_data: TourCreate) -> Tour:
    db_tour = Tour(
        tour_name=tour_data.tour_name,
        date=tour_data.date,
        price_per_head=tour_data.price_per_head,
        total_seats=tour_data.total_seats,
        available_seats=tour_data.available_seats,
        category=tour_data.category
    )
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour

def seed_default_tours(db: Session):
    """
    Seeds the default tours with static UUIDs to ensure alignment across
    database states, vector search metadata, and LLM agents.
    """
    existing_tours = db.query(Tour).all()
    if len(existing_tours) == 0:
        shogran = Tour(
            id=uuid.UUID("05d29dfa-b9da-4d95-8d17-e1917e9c9959"),
            tour_name="Shogran & Siri Paye Meadows",
            date="18 July 2026",
            price_per_head=4500,
            total_seats=20,
            available_seats=20,
            category="Family Short Tour"
        )
        siran = Tour(
            id=uuid.UUID("2ad29dfa-b9da-4d95-8d17-e1917e9c9958"),
            tour_name="Siran Valley & Khanpur Dam",
            date="25 July 2026",
            price_per_head=3700,
            total_seats=20,
            available_seats=20,
            category="Family Short Tour"
        )
        db.add(shogran)
        db.add(siran)
        db.commit()
