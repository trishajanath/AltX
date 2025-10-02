from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routes import api_router

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# 1. Create FastAPI app instance
app = FastAPI(
    title="Web-based College Attendance System",
    description="API for managing college attendance, students, courses, and faculty.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/v1/openapi.json"
)

# 2. Configure CORS middleware
# WARNING: This is a permissive CORS configuration suitable for development.
# For production, you MUST restrict allow_origins to your frontend's domain.
# Example: allow_origins=["https://your-frontend-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Add root health check endpoint
@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Welcome to the College Attendance System API"}

# 4. Include the API router with a prefix
# All routes defined in 'routes.py' will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# To run this application:
# 1. Install dependencies: pip install fastapi uvicorn sqlalchemy python-dotenv
#    For PostgreSQL: pip install psycopg2-binary
# 2. Run the command: uvicorn main:app --reload --app-dir backend