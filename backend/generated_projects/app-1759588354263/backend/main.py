# main.py
# To run this application:
# 1. Save this file as `main.py`.
# 2. Save the accompanying `routes.py` file in the same directory.
# 3. Install dependencies: pip install fastapi "uvicorn[standard]"
# 4. Run the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from the routes module
from routes import router as api_v1_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759588354263",
    description="A FastAPI application with CORS, a versioned API, and a health check.",
    version="1.0.0",
)

# --- Middleware Configuration ---

# Configure CORS (Cross-Origin Resource Sharing)
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict this to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# --- API Routers ---

# Include the router from routes.py with the specified prefix
# All routes defined in the `api_v1_router` will be available under /api/v1
app.include_router(api_v1_router, prefix="/api/v1", tags=["API v1"])


# --- Root Endpoint / Health Check ---

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint to verify that the service is running.
    """
    return {"status": "ok", "message": "Service is up and running"}

```

```python
# routes.py
# This file should be in the same directory as main.py

from fastapi import APIRouter

# Create a new router object
router = APIRouter()

@router.get("/example")
async def get_example():
    """
    An example endpoint for the v1 API.
    This will be accessible at /api/v1/example
    """
    return {"message": "This is an example response from API v1"}

# You can add more routes to this router
@router.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """
    An example endpoint with a path parameter and an optional query parameter.
    Accessible at /api/v1/items/{item_id}
    """
    return {"item_id": item_id, "q": q}