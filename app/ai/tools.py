import json
import logging
import uuid
from typing import Optional
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.models.tour import Tour
from app.schemas.booking import BookingCreate
from app.services import booking_service, tour_service
from app.services.vector_store import search as vector_search
from app.services.vector_document_builder import get_tour_static_details

logger = logging.getLogger("seeroo_tools")

def error_response(code: str, message: str) -> str:
    """Helper to return standardized JSON error messages."""
    return json.dumps({
        "status": "error",
        "error_code": code,
        "message": message
    })

@tool
def search_tours(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    month: Optional[str] = None
) -> str:
    """
    Searches for available tours using similarity semantic queries and optional filters.
    Args:
        query: Semantic query text (e.g. 'cheap family trips')
        category: Optional category filter (e.g. 'Family Short Tour')
        max_price: Optional maximum budget limit per head (in PKR)
        month: Optional month filter (e.g. 'July')
    """
    filters = {}
    if category:
        filters["category"] = category
    if max_price is not None:
        filters["max_price"] = max_price
    if month:
        filters["month"] = month
        
    try:
        results = vector_search(query, filters=filters, top_k=5)
        if results == "NO_MATCH_FOUND":
            return json.dumps({"status": "success", "results": []})
            
        # Standardize matching JSON list
        matches = []
        for r in results:
            matches.append({
                "tour_id": r["id"],
                "document": r["document"],
                "metadata": r["metadata"]
            })
        return json.dumps({"status": "success", "results": matches})
    except Exception as e:
        logger.error(f"Error in tool search_tours: {str(e)}")
        return error_response("SEARCH_FAILED", str(e))

@tool
def get_tour_details(tour_id: str) -> str:
    """
    Retrieves rich itinerary and logistics details (pickup points, services, locations) for a specific tour by ID.
    Args:
        tour_id: UUID of the tour
    """
    db = SessionLocal()
    try:
        try:
            tour_uuid = uuid.UUID(tour_id)
        except ValueError:
            return error_response("INVALID_ID", "Provided tour_id is not a valid UUID.")
            
        tour = db.query(Tour).filter(Tour.id == tour_uuid).first()
        if not tour:
            return error_response("TOUR_NOT_FOUND", f"No tour found with ID {tour_id}")
            
        details = get_tour_static_details(tour.tour_name)
        
        response_data = {
            "status": "success",
            "tour_id": str(tour.id),
            "tour_name": tour.tour_name,
            "category": tour.category,
            "date": tour.date,
            "price_per_head": tour.price_per_head,
            "available_seats": tour.available_seats,
            "locations": details.get("locations", []),
            "services": details.get("services", []),
            "pickup_points": details.get("pickup_points", []),
            "description": details.get("summary", "")
        }
        return json.dumps(response_data)
    except Exception as e:
        logger.error(f"Error in tool get_tour_details: {str(e)}")
        return error_response("LOOKUP_FAILED", str(e))
    finally:
        db.close()

@tool
def calculate_price(tour_id: str, seats: int) -> str:
    """
    Calculates total booking cost for a group size, applying automatic volume discounts.
    Volume discounts: 5% off for 5-9 seats, 10% off for 10+ seats.
    Args:
        tour_id: UUID of the tour
        seats: Number of seats required
    """
    db = SessionLocal()
    try:
        try:
            tour_uuid = uuid.UUID(tour_id)
        except ValueError:
            return error_response("INVALID_ID", "Provided tour_id is not a valid UUID.")
            
        if seats <= 0:
            return error_response("INVALID_SEATS", "Seats must be greater than 0.")
            
        tour = db.query(Tour).filter(Tour.id == tour_uuid).first()
        if not tour:
            return error_response("TOUR_NOT_FOUND", f"No tour found with ID {tour_id}")
            
        # Calculation logic matching services layer
        discount_pct = 0
        if seats >= 10:
            discount_pct = 10
        elif seats >= 5:
            discount_pct = 5
            
        raw_total = seats * tour.price_per_head
        discount_amt = int(raw_total * (discount_pct / 100))
        final_total = raw_total - discount_amt
        
        response_data = {
            "status": "success",
            "tour_id": str(tour.id),
            "tour_name": tour.tour_name,
            "seats": seats,
            "price_per_head": tour.price_per_head,
            "raw_total": raw_total,
            "discount_percentage": discount_pct,
            "discount_amount": discount_amt,
            "total_price": final_total
        }
        return json.dumps(response_data)
    except Exception as e:
        logger.error(f"Error in tool calculate_price: {str(e)}")
        return error_response("PRICING_ERROR", str(e))
    finally:
        db.close()

@tool
def check_seat_availability(tour_id: str, seats: int) -> str:
    """
    Checks if a tour has enough open seats remaining for a booking size.
    Args:
        tour_id: UUID of the tour
        seats: Number of seats required
    """
    db = SessionLocal()
    try:
        try:
            tour_uuid = uuid.UUID(tour_id)
        except ValueError:
            return error_response("INVALID_ID", "Provided tour_id is not a valid UUID.")
            
        if seats <= 0:
            return error_response("INVALID_SEATS", "Seats must be greater than 0.")
            
        tour = db.query(Tour).filter(Tour.id == tour_uuid).first()
        if not tour:
            return error_response("TOUR_NOT_FOUND", f"No tour found with ID {tour_id}")
            
        is_available = tour.available_seats >= seats
        
        response_data = {
            "status": "success",
            "tour_id": str(tour.id),
            "tour_name": tour.tour_name,
            "requested_seats": seats,
            "available_seats": tour.available_seats,
            "available": is_available
        }
        return json.dumps(response_data)
    except Exception as e:
        logger.error(f"Error in tool check_seat_availability: {str(e)}")
        return error_response("AVAILABILITY_ERROR", str(e))
    finally:
        db.close()

@tool
def create_booking(
    user_name: str,
    phone: str,
    tour_id: str,
    seats: int,
    pickup_city: str,
    email: Optional[str] = None
) -> str:
    """
    Executes database seat reservation transactions and registers lead travelers in a secure transaction.
    Args:
        user_name: Lead traveler full name
        phone: Pakistani mobile phone (11-digits starting with 03)
        tour_id: UUID of the tour being booked
        seats: Quantity of seats requested
        pickup_city: City of departure (e.g. Attock, Wah, Kamra, Taxila)
        email: Optional email address
    """
    db = SessionLocal()
    try:
        try:
            tour_uuid = uuid.UUID(tour_id)
        except ValueError:
            return error_response("INVALID_ID", "Provided tour_id is not a valid UUID.")
            
        booking_data = BookingCreate(
            tour_id=tour_uuid,
            seats=seats,
            pickup_city=pickup_city,
            full_name=user_name,
            phone=phone,
            email=email
        )
        
        # Invoke service layer transaction
        booking = booking_service.create_booking(db, booking_data)
        
        response_data = {
            "status": "success",
            "booking_id": str(booking.id),
            "user_id": str(booking.user_id),
            "tour_id": str(booking.tour_id),
            "seats": booking.seats,
            "price_per_head": booking.price_per_head,
            "total_price": booking.total_price,
            "pickup_city": booking.pickup_city,
            "booking_status": booking.booking_status,
            "payment_status": booking.payment_status,
            "created_at": booking.created_at.isoformat()
        }
        return json.dumps(response_data)
        
    except Exception as e:
        # Check if it was a custom HTTPException raised by the service layer
        detail_msg = getattr(e, "detail", str(e))
        logger.error(f"Error executing create_booking: {detail_msg}")
        return error_response("BOOKING_FAILED", detail_msg)
    finally:
        db.close()
