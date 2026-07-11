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
    Seeds the default tours if they do not exist in the database.
    """
    existing_tours = db.query(Tour).all()
    if len(existing_tours) == 0:
        default_tours = [
            TourCreate(
                tour_name="Shogran & Siri Paye Meadows",
                date="18 July 2026",
                price_per_head=4500,
                total_seats=20,
                available_seats=20,
                category="Family Short Tour"
            ),
            TourCreate(
                tour_name="Siran Valley & Khanpur Dam",
                date="25 July 2026",
                price_per_head=3700,
                total_seats=20,
                available_seats=20,
                category="Family Short Tour"
            )
        ]
        for t in default_tours:
            create_tour(db, t)
