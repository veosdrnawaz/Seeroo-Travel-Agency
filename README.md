# Seeroo Travels Attock - Backend Booking System 🌄

This is the production-grade FastAPI backend for the **SEEROO TRAVELS ATTOCK** booking system. It handles user registration, active tours catalogs, and seat reservations with atomic transactional consistency.

## 🛠️ Features
- **FastAPI Core**: High-performance API routing and auto-generated Swagger documentation.
- **SQLAlchemy 2.0**: Object-relational mapping supporting dynamic dialect selection (local SQLite or PostgreSQL).
- **Atomic Concurrency Control**: Prevents seat double-booking or overbooking under concurrent workloads via direct SQL atomic updates.
- **Pydantic Validation**: Strong request model checks and sanitized inputs.
- **Auto-Seeding**: Seeds signature Shogran and Siran Valley tours on database startup.

---

## 📁 Directory Structure
```text
├── requirements.txt      # Dependency configurations
├── .env                  # Environment parameters
├── app/                  # Main FastAPI Application
│   ├── main.py           # Entry point and initialization
│   ├── core/             # Settings configuration & validation
│   ├── db/               # SQLAlchemy engines & sessions
│   ├── models/           # User, Tour, and Booking entities
│   ├── schemas/          # Pydantic request/response models
│   ├── routes/           # REST endpoints
│   └── services/         # Transactional workflows
```

---

## 🚀 Local Installation & Setup

### 1. Create a Virtual Environment
```bash
# Python 3.12+ recommended
python -m venv venv
venv\Scripts\activate      # On Windows
source venv/bin/activate    # On macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Settings
Configure your database dialect in the `.env` file at the root:
```env
# Default SQLite fallback
DATABASE_URL=sqlite:///./seeroo_travels.db

# To use PostgreSQL, swap with:
# DATABASE_URL=postgresql://username:password@localhost:5432/seeroo_travels
```

### 4. Start the Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API documentation will be available at:
* **Interactive Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc format**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Endpoints

### 1. Tours Router (`/tours`)
- `GET /tours`: Get list of active tours (auto-seeds default Shogran and Siran valley if empty).
- `GET /tours/{id}`: Get details of a specific tour.
- `POST /tours`: Register a new tour (requires `tour_name`, `date`, `price_per_head`, `total_seats`, `available_seats`, `category`).

### 2. Bookings Router (`/bookings`)
- `POST /bookings`: Submit a seat reservation.
  - Automatically creates a new user profile if the phone number is not registered.
  - Performs atomic update to check and decrement seat inventory.
  - Automatically applies group discount rates (5% off for 5-9 seats, 10% off for 10+ seats).
  - Returns `201 Created` with a full invoice breakdown.
- `GET /bookings/{id}`: Get reservation details and invoice.
