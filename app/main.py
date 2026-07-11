import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base import Base
# Import models to ensure they are registered on the metadata
from app.models.user import User
from app.models.tour import Tour
from app.models.booking import Booking

from app.routes import tours, bookings
from app.services.tour_service import seed_default_tours

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("seeroo_backend")

# Initialize Database tables
try:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Seed Default Tours
db = SessionLocal()
try:
    logger.info("Seeding default tours...")
    seed_default_tours(db)
    logger.info("Seeding completed.")
except Exception as e:
    logger.error(f"Error seeding database: {str(e)}")
finally:
    db.close()

# Initialize FastAPI App
app = FastAPI(
    title="Seeroo Travels Attock API",
    description="Backend API for booking short tours with atomic seat transaction safety.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validation Error Middleware override for structured error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation failure on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Input validation failed. Please check field structures."}
    )

# Global logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response Status: {response.status_code}")
    return response

# Register Routes
app.include_router(tours.router)
app.include_router(bookings.router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "database": settings.DATABASE_URL.split(":///")[0]}
