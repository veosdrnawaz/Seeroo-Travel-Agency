import os
import sys

# Add project root to python path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.tour import Tour
from app.models.booking import Booking
from app.services.tour_service import seed_default_tours
from app.services.embedding_service import index_tours
from app.services.vector_store import search

def main():
    print("=== SEEROO TRAVELS VECTORS SEARCH TESTER ===")
    
    # 1. Initialize SQLite Database Tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Seed Tours if empty
        seed_default_tours(db)
        
        # 3. Index Tours to ChromaDB
        success = index_tours(db)
        if not success:
            print("ERROR: Failed to index tours into ChromaDB.")
            sys.exit(1)
            
    finally:
        db.close()
        
    print("\nIndexing completed successfully. Executing query test cases...\n")
    
    # 4. Test Query Cases
    test_cases = [
        {
            "description": "1. Cheap tour under 4000 (Filter: max_price = 4000)",
            "query": "cheap tour under 4000",
            "filters": {"max_price": 4000}
        },
        {
            "description": "2. Family tour in July (Filter: month = July)",
            "query": "family tour in July",
            "filters": {"month": "July"}
        },
        {
            "description": "3. Girls only trip (Semantic match)",
            "query": "girls only trip",
            "filters": None
        },
        {
            "description": "4. Trip with breakfast and dinner (Semantic match)",
            "query": "trip with breakfast and dinner",
            "filters": None
        },
        {
            "description": "5. Shogran tour (Semantic match)",
            "query": "Shogran tour",
            "filters": None
        },
        {
            "description": "6. Non-existent filter match (Should return NO_MATCH_FOUND)",
            "query": "trip in August",
            "filters": {"month": "August"}
        }
    ]
    
    for case in test_cases:
        print(f"\n>>> Test Case: {case['description']}")
        print(f"   Query: '{case['query']}'")
        if case['filters']:
            print(f"   Filters: {case['filters']}")
            
        results = search(case['query'], filters=case['filters'], top_k=2)
        
        if results == "NO_MATCH_FOUND":
            print("   [Result] NO_MATCH_FOUND")
        else:
            print(f"   [Result] Found {len(results)} matches:")
            for idx, match in enumerate(results):
                tour_name = match['metadata'].get('tour_name', '')
                # If metadata name isn't present, extract first line of document
                if not tour_name:
                    tour_name = match['document'].split('\n')[0]
                price = match['metadata'].get('price_per_head', 0)
                date = match['metadata'].get('date', '')
                dist = f" (Distance: {match['distance']:.4f})" if match['distance'] is not None else ""
                print(f"     [{idx+1}] {tour_name} - Price: Rs. {price} - Date: {date}{dist}")
                
    print("\n=== All Test Cases Executed ===")

if __name__ == "__main__":
    main()
