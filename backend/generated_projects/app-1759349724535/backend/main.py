from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Assuming a `routes.py` file in the same directory containing an APIRouter instance.
# Example `routes.py`:
# from fastapi import APIRouter
# router = APIRouter()
# @router.get("/projects")
# def get_projects():
#     return {"message": "List of construction projects"}
from routes import router as api_router

# 1. Create FastAPI app instance
app = FastAPI(
    title="Construction Company Website API",
    description="API for managing projects, services, and client inquiries for the construction company website.",
    version="1.0.0",
)

# 2. Configure CORS middleware
# This allows all origins for development purposes.
# For production, you should restrict `allow_origins` to your frontend's domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# 3. Include the API router from routes.py
# All routes defined in the `api_router` will be prefixed with /api/v1.
app.include_router(api_router, prefix="/api/v1")

# 4. Add a root health check endpoint
@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Welcome to the Construction Company API!"}

# To run this application:
# 1. Make sure you have a `routes.py` file in the same directory.
# 2. Run the command: uvicorn main:app --reload