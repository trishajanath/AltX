# main.py
# Save this file as main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from the routes.py file
# Ensure you create a 'routes.py' file in the same directory.
from routes import router as api_v1_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759395385592",
    description="A FastAPI application with a versioned API.",
    version="1.0.0",
)

# --- Middleware Configuration ---

# Add CORS middleware to allow cross-origin requests.
# For production, you should restrict `allow_origins` to your frontend's domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# --- Root Endpoint / Health Check ---

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# --- Include API Routers ---

# Include the router from routes.py and prefix all its routes with /api/v1
app.include_router(api_v1_router)


# --- Instructions to run the app ---
# 1. Save the code above as `main.py`.
# 2. Save the code below as `routes.py` in the same directory.
# 3. Install the required packages:
#    pip install fastapi "uvicorn[standard]"
# 4. Run the development server from your terminal:
#    uvicorn main:app --reload
#
# You can then access the API at http://127.0.0.1:8000
# The health check is at: http://127.0.0.1:8000/
# The API v1 root is at: http://127.0.0.1:8000/api/v1/
# Interactive API docs (Swagger UI) are at: http://127.0.0.1:8000/docs


# ----------------------------------------------------------------------
# routes.py
# Save the code below in a separate file named routes.py
# ----------------------------------------------------------------------
"""
from fastapi import APIRouter, Path
from typing import Dict

# Create an API router with a prefix for all routes in this file
router = APIRouter(
    prefix="/api/v1",
    tags=["APIv1"],
)

@router.get("/")
async def get_v1_root() -> Dict[str, str]:
    \"\"\"
    Root endpoint for API version 1.
    \"\"\"
    return {"message": "Welcome to API v1 for app-1759395385592"}

@router.get("/items/{item_id}")
async def get_item(item_id: int = Path(..., title="The ID of the item to get", ge=1)) -> Dict[str, int]:
    \"\"\"
    Example endpoint to retrieve an item by its ID.
    \"\"\"
    return {"item_id": item_id}

"""