from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Assuming a 'routes.py' file exists in the same directory
# with an APIRouter instance named 'api_router'
from routes import api_router

# 1. Create FastAPI app instance
app = FastAPI(
    title="College Event Management Application",
    description="API for managing college events, participants, and schedules.",
    version="1.0.0",
    project="app-1759347734241"
)

# 2. Configure CORS middleware
# This allows all origins, which is suitable for development.
# For production, you should restrict this to your frontend's domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 3. Add root health check endpoint
@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint to check the health and status of the API.
    """
    return {"status": "ok", "message": "Welcome to the College Event Management API!"}

# 4. Include the main API router
# All routes defined in 'routes.api_router' will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# To run this application:
# 1. Make sure you have a 'routes.py' file with an APIRouter instance named 'api_router'.
# 2. Run the command: uvicorn main:app --reload