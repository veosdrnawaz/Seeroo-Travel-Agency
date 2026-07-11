from app.models.tour import Tour

# Static metadata repository for known signature tours to enrich DB columns
TOUR_METADATA_REGISTRY = {
    "Shogran & Siri Paye Meadows": {
        "locations": ["Kiwai Waterfall", "Shogran Valley", "Siri Meadows", "Paye Alpine Meadows"],
        "services": ["AC Saloon Coaster", "Buffet Breakfast", "Chicken Karahi Dinner", "Jeep transfers (Kiwai-Paye)", "Tour Guide Coordination", "First-Aid Support"],
        "pickup_points": ["Attock (Fawara Chowk)", "Wah Cantt (G.T. Road Plaza)", "Kamra (Cantt Gate)", "Taxila (Main Chowk)"],
        "summary": "Ascend to the breathtaking alpine lawns of Siri Paye. A high-altitude lush valley surrounded by snow-capped peaks. Beautiful jeep tracks, pine forests, and a perfect weekend escape for families."
    },
    "Siran Valley & Khanpur Dam": {
        "locations": ["Siran River Valley", "Khanpur Dam Lake"],
        "services": ["AC Saloon Coaster", "Buffet Breakfast", "Chicken Biryani Dinner", "Boating Activity Coordination", "Tour Guide Coordination", "First-Aid Support"],
        "pickup_points": ["Attock (Fawara Chowk)", "Wah Cantt (G.T. Road Plaza)", "Kamra (Cantt Gate)", "Taxila (Main Chowk)"],
        "summary": "Witness the serene waters of the Siran River followed by boating, cliff jumping, and sightseeing at Khanpur Dam. Perfect mix of peace and water sports adventure."
    }
}

DEFAULT_METADATA = {
    "locations": ["Northern Pakistan Valley"],
    "services": ["AC Transport", "Breakfast & Dinner", "Tour Coordination"],
    "pickup_points": ["Attock", "Wah", "Kamra", "Taxila"],
    "summary": "Enjoy a comfortable weekend excursion with coordination, food, and transport included."
}

def get_tour_static_details(tour_name: str) -> dict:
    # Match registry or fallback to defaults
    for name, data in TOUR_METADATA_REGISTRY.items():
        if name.lower() in tour_name.lower() or tour_name.lower() in name.lower():
            return data
    return DEFAULT_METADATA

def build_tour_document(tour: Tour) -> str:
    """
    Converts a database Tour record into a deterministic, cleanly formatted semantic text document.
    """
    details = get_tour_static_details(tour.tour_name)
    
    # Format and join values, checking for null values
    tour_name = tour.tour_name or "Unknown Tour"
    category = tour.category or "Short Tour"
    date_val = tour.date or "Flexible Date"
    price = f"Rs. {tour.price_per_head}" if tour.price_per_head else "Contact for Price"
    seats = f"{tour.available_seats} remaining of {tour.total_seats}" if tour.available_seats is not None else "Check Availability"
    
    locations = ", ".join(details.get("locations", []))
    services = ", ".join(details.get("services", []))
    pickup = ", ".join(details.get("pickup_points", []))
    summary = details.get("summary", "")
    
    doc = f"""Tour Name: {tour_name}
Category: {category}
Date: {date_val}
Price Per Head: {price}
Seat Availability: {seats}
Locations: {locations}
Services: {services}
Pickup Points: {pickup}
Description: {summary}"""

    return doc.strip()
