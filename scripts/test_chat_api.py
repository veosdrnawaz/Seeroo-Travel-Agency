import os
import sys
import json
import uuid

# Add project root to python path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.base import Base
from app.models.tour import Tour
from app.models.booking import Booking
from app.models.user import User
from app.services.tour_service import seed_default_tours
from app.services.embedding_service import index_tours

def print_separator(title):
    print("\n" + "=" * 60)
    print(f" {title} ")
    print("=" * 60)

def main():
    print("=== SEEROO TRAVELS CHAT API TESTER ===")
    
    # 1. Reset Database files and checkpoints db
    checkpoint_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "checkpoints.db"))
    if os.path.exists(checkpoint_file):
        try:
            os.remove(checkpoint_file)
            print("checkpoints.db removed cleanly.")
        except Exception as e:
            print(f"Warning: Could not remove checkpoints.db: {str(e)}")
            
    db = SessionLocal()
    try:
        db.query(Booking).delete()
        db.query(User).delete()
        db.query(Tour).delete()
        db.commit()
        
        # Seed default tours
        seed_default_tours(db)
        # Index to ChromaDB
        index_tours(db)
        
        shogran_tour = db.query(Tour).filter(Tour.tour_name.like("%Shogran%")).first()
        initial_seats = shogran_tour.available_seats
        print(f"Database reset. Shogran Available Seats: {initial_seats}")
    finally:
        db.close()
        
    client = TestClient(app)
    thread_id = f"thread-test-{uuid.uuid4().hex[:6]}"
    print(f"Active test thread: '{thread_id}'")
    
    # --- TURN 1: Search Request ---
    print_separator("TURN 1: Ask 'cheap tour under 4000'")
    payload = {"thread_id": thread_id, "message": "cheap tour under 4000"}
    res = client.post("/chat", json=payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    print(f"API Reply: '{data['reply']}'")
    print(f"Confirmation Required: {data['requires_confirmation']}")
    print(f"Booking ID: {data['booking_id']}")
    print(f"Error Payload: {data['error']}")
    
    # --- TURN 2: Follow-up Booking Request ---
    print_separator("TURN 2: Ask 'book 6 seats' (Check persistent memory)")
    payload = {"thread_id": thread_id, "message": "book 6 seats"}
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    print(f"API Reply: '{data['reply']}'")
    print(f"Confirmation Required: {data['requires_confirmation']}")
    print(f"Booking ID: {data['booking_id']}")
    print(f"Error Payload: {data['error']}")
    assert data["requires_confirmation"] is True, "Expected requires_confirmation to be True"
    
    # --- TURN 3: Lead Info & Confirm ---
    print_separator("TURN 3: Confirm 'Name: Muhammad Ahmad, Phone: 03001234567, Pickup: Attock'")
    payload = {
        "thread_id": thread_id, 
        "message": "Confirm booking. Name: Muhammad Ahmad, Phone: 03001234567, Pickup: Attock"
    }
    res = client.post("/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    print(f"API Reply: '{data['reply']}'")
    print(f"Confirmation Required: {data['requires_confirmation']}")
    print(f"Booking ID: {data['booking_id']}")
    print(f"Error Payload: {data['error']}")
    assert data["booking_id"] is not None, "Expected booking_id to be populated"
    
    saved_booking_id = data["booking_id"]
    
    # --- VERIFY STATE IN DATABASE ---
    print_separator("DATABASE INTEGRITY ASSERTIONS")
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == uuid.UUID(saved_booking_id)).first()
        user = db.query(User).filter(User.phone == "03001234567").first()
        shogran_tour = db.query(Tour).filter(Tour.tour_name.like("%Shogran%")).first()
        
        print(f"Booking saved in DB?: {booking is not None}")
        if booking:
            print(f"  User registered?: {user is not None} | Name: {user.full_name}")
            print(f"  Seats reserved: {booking.seats} | Total Cost: Rs. {booking.total_price}")
            print(f"  Pickup City: {booking.pickup_city}")
            print(f"  Tour seats left: {shogran_tour.available_seats} (Initial: {initial_seats})")
            if shogran_tour.available_seats == initial_seats - 6:
                print("  SUCCESS: Seats correctly decremented via transaction.")
            else:
                print("  ERROR: Seat count decrement mismatch!")
    finally:
        db.close()
        
    # --- TEST CASE 6: RATE LIMITING ---
    print_separator("TEST CASE: Rate Limiter Validation")
    limit_thread_id = f"thread-limit-{uuid.uuid4().hex[:6]}"
    print(f"Attempting 21 rapid messages on thread: '{limit_thread_id}'")
    
    limit_payload = {"thread_id": limit_thread_id, "message": "hello"}
    rate_limited_hit = False
    
    for i in range(21):
        res = client.post("/chat", json=limit_payload)
        data = res.json()
        if data.get("error") and data["error"].get("code") == "RATE_LIMIT_EXCEEDED":
            print(f"  Request [{i+1}] Blocked: {data['error']['message']}")
            rate_limited_hit = True
            break
        else:
            print(f"  Request [{i+1}] Passed (HTTP {res.status_code})")
            
    if rate_limited_hit:
        print("  SUCCESS: Rate limiter blocked request 21 as expected.")
    else:
        print("  ERROR: Rate limiter failed to block requests!")
        
    print("\n=== Chat API Test Suite Execution Complete ===")

if __name__ == "__main__":
    main()
