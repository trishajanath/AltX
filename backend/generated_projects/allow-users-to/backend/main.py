# main.py
# To run this application:
# 1. Save this file as main.py
# 2. Save the second code block as routes.py in the same directory.
# 3. Install dependencies: pip install fastapi "uvicorn[standard]"
# 4. Run the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="User Management API",
    description="API to allow users to perform actions.",
    version="1.0.0",
)

# Define allowed origins for CORS.
# Using ["*"] allows all origins, which is convenient for development
# but should be restricted in a production environment.
origins = [
    "*",
    # "http://localhost",
    # "http://localhost:8080",
    # "https://your-frontend-domain.com",
]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}

# Include the API router with a prefix
# All routes defined in routes.py will be available under /api/v1
app.include_router(api_router, prefix="/api/v1")


# routes.py
# This file contains the API routes for the application.
# It is included by main.py.

from fastapi import APIRouter, HTTPException, status

# Create an instance of APIRouter
router = APIRouter()

# In-memory "database" for demonstration purposes
fake_users_db = {
    "user1": {"username": "john_doe", "email": "john.doe@example.com", "full_name": "John Doe"},
    "user2": {"username": "jane_smith", "email": "jane.smith@example.com", "full_name": "Jane Smith"},
}

@router.get("/users", tags=["Users"])
async def get_all_users():
    """
    Retrieve a list of all users.
    """
    return list(fake_users_db.values())

@router.get("/users/{username}", tags=["Users"])
async def get_user_by_username(username: str):
    """
    Retrieve a specific user by their username.
    """
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username '{username}' not found",
        )
    return fake_users_db[username]

@router.get("/status", tags=["Status"])
async def get_api_status():
    """
    Get the status of the API v1 endpoints.
    """
    return {"status": "ok", "message": "API v1 is running"}