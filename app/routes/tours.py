from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.db.session import get_db
from app.schemas.tour import TourResponse, TourCreate
from app.services import tour_service

router = APIRouter(prefix="/tours", tags=["Tours"])

@router.get("", response_model=List[TourResponse])
def read_tours(db: Session = Depends(get_db)):
    tours = tour_service.get_tours(db)
    return tours

@router.get("/{tour_id}", response_model=TourResponse)
def read_tour(tour_id: uuid.UUID, db: Session = Depends(get_db)):
    db_tour = tour_service.get_tour_by_id(db, tour_id)
    if not db_tour:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tour with ID {tour_id} not found."
        )
    return db_tour

@router.post("", response_model=TourResponse, status_code=status.HTTP_201_CREATED)
def create_new_tour(tour_data: TourCreate, db: Session = Depends(get_db)):
    return tour_service.create_tour(db, tour_data)
