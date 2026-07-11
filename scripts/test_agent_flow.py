import os
import sys
import uuid

# Add project root to python path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.tour import Tour
from app.models.booking import Booking
from app.services.tour_service import seed_default_tours
from app.services.embedding_service import index_tours
from app.ai.agent import run_agent

def print_separator(title):
    print("\n" + "=" * 60)
    print(f" {title} ")
    print("=" * 60)

def main():
    # 1. Database Setup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Clear existing bookings/users/tours for clean test run
        db.query(Booking).delete()
        db.query(User).delete()
        db.query(Tour).delete()
        db.commit()
        
        # Seed default tours
        seed_default_tours(db)
        # Index to ChromaDB
        index_tours(db)
        
        # Verify Shogran tour ID and initial seats
        shogran_tour = db.query(Tour).filter(Tour.tour_name.like("%Shogran%")).first()
        initial_seats = shogran_tour.available_seats
        print(f"Database Initialized. Shogran Tour ID: {shogran_tour.id} | Available Seats: {initial_seats}")
        
    finally:
        db.close()

    # Chat history tracker
    chat_history = []

    # Scenario 1: Search cheap tour
    print_separator("SCENARIO 1: Search cheap tour under 4000")
    res = run_agent("cheap tour under 4000", chat_history)
    print(f"Agent Output: {res['output']}")
    print(f"Tool Calls Made: {res['tool_calls']}")

    # Scenario 2: Detail inquiry
    print_separator("SCENARIO 2: Tell me about Shogran tour")
    res = run_agent("Tell me about Shogran tour", chat_history)
    print(f"Agent Output: {res['output']}")
    print(f"Tool Calls Made: {res['tool_calls']}")

    # Scenario 3: Non-existent filter match (Should return NO_MATCH_FOUND message)
    print_separator("SCENARIO 3: Search trip in August (Invalid tour query)")
    res = run_agent("trip in August", chat_history)
    print(f"Agent Output: {res['output']}")
    print(f"Tool Calls Made: {res['tool_calls']}")

    # Scenario 4: Booking with insufficient seats (35 seats)
    print_separator("SCENARIO 4: Booking 35 seats for Shogran (Insufficient seats)")
    res = run_agent("Book 35 seats for Shogran", chat_history)
    print(f"Agent Output: {res['output']}")
    print(f"Tool Calls Made: {res['tool_calls']}")

    # Scenario 5: Successful multi-step booking of 6 seats
    print_separator("SCENARIO 5: Book 6 seats for Shogran - Inquiry Step")
    # Step A: Intent to book 6 seats triggers seat check and pricing discount calculation
    res = run_agent("Book 6 seats for Shogran", chat_history)
    print(f"Agent Output: {res['output']}")
    print(f"Tool Calls Made: {res['tool_calls']}")
    
    # Simulate appending the conversation history
    chat_history.append(("human", "Book 6 seats for Shogran"))
    chat_history.append(("assistant", res['output']))

    print("\n--- Confirmation Step ---")
    # Step B: User provides traveler information to finalize the booking
    confirm_msg = "Please confirm the booking. Name: Muhammad Ahmad, Phone: 03001234567, Pickup: Attock"
    res = run_agent(confirm_msg, chat_history)
    print(f"Agent Output: {res['output']}")
    print(f"Tool Calls Made: {res['tool_calls']}")

    # 5. Database Assertions
    print_separator("DATABASE VERIFICATION")
    db = SessionLocal()
    try:
        bookings = db.query(Booking).all()
        users = db.query(User).all()
        shogran_tour = db.query(Tour).filter(Tour.tour_name.like("%Shogran%")).first()
        
        print(f"Total Users Registered: {len(users)}")
        if users:
            print(f"  Lead User: {users[0].full_name} | Phone: {users[0].phone}")
            
        print(f"Total Bookings Registered: {len(bookings)}")
        if bookings:
            print(f"  Booking ID: {bookings[0].id}")
            print(f"  Seats Reserved: {bookings[0].seats} | Total Cost: Rs. {bookings[0].total_price}")
            print(f"  Status: {bookings[0].booking_status} | Pickup: {bookings[0].pickup_city}")
            
        print(f"Tour Seat Update:")
        print(f"  Shogran Initial Seats: {initial_seats}")
        print(f"  Shogran Remaining Seats: {shogran_tour.available_seats}")
        
        # Verify seats match
        expected_seats = initial_seats - 6
        if shogran_tour.available_seats == expected_seats:
            print("  SUCCESS: Seat count correctly decremented in database transaction.")
        else:
            print("  ERROR: Seat count decrement mismatch!")
            
    finally:
        db.close()

    print("\n=== Agent Flow Test Suite Execution Complete ===")

if __name__ == "__main__":
    main()
