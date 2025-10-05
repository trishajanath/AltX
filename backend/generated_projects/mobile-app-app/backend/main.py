# main.py
# To run this app:
# 1. Save the code as main.py
# 2. Install FastAPI and Uvicorn: pip install fastapi "uvicorn[standard]"
# 3. Run the server: uvicorn main:app --reload
# 4. Access the docs at http://127.0.0.1:8000/docs

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# --- API Router (Normally in a separate file like `routes.py`) ---

# In a larger application, this APIRouter would be in a separate file
# like `api/routes.py` and imported into main.py.
api_router = APIRouter()

# Example data (simulating a database)
mock_db = {
    "users": {
        "user1": {"username": "alex", "email": "alex@example.com"},
        "user2": {"username": "brian", "email": "brian@example.com"},
    },
    "items": [
        {"id": 1, "name": "Smartphone", "owner_id": "user1"},
        {"id": 2, "name": "Laptop", "owner_id": "user1"},
        {"id": 3, "name": "Tablet", "owner_id": "user2"},
    ]
}

@api_router.get("/users", tags=["Users"])
async def get_users() -> Dict[str, Any]:
    """
    Retrieve all users.
    """
    return mock_db["users"]

@api_router.get("/users/{user_id}", tags=["Users"])
async def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Retrieve a single user by their ID.
    """
    if user_id in mock_db["users"]:
        return mock_db["users"][user_id]
    return {"error": "User not found"}

@api_router.get("/items", tags=["Items"])
async def get_items() -> List[Dict[str, Any]]:
    """
    Retrieve all items.
    """
    return mock_db["items"]


# --- Main FastAPI Application ---

# Initialize the FastAPI app
app = FastAPI(
    title="Mobile App App API",
    description="Backend API for the Mobile App App.",
    version="1.0.0",
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows a frontend running on a different domain to communicate with this API.
# For development, we allow all origins. In production, you should restrict this
# to the specific domains of your mobile app's frontend or gateway.
origins = [
    "*",  # Allows all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include the API router with a versioned prefix
# All routes defined in `api_router` will now be accessible under `/api/v1`
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    A simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Mobile App App API is healthy"}