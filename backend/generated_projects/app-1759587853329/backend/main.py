# main.py
# To run this application:
# 1. Save this code as `main.py`.
# 2. Save the second code block as `routes.py` in the same directory.
# 3. Run `pip install "fastapi[all]"`.
# 4. Run `uvicorn main:app --reload`.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759587853329",
    description="A FastAPI application with a health check and a versioned API.",
    version="1.0.0",
)

# --- Middleware ---

# Set up CORS (Cross-Origin Resource Sharing)
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict this to specific domains.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- Root Endpoint / Health Check ---

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint.
    Returns a JSON response indicating the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}


# --- Include API Routers ---

# Include the router from routes.py with a URL prefix
# All routes defined in routes.py will be available under /api/v1
app.include_router(api_router, prefix="/api/v1")


# --- Optional: Lifecycle Events ---

@app.on_event("startup")
async def startup_event():
    """
    Code to run on application startup.
    """
    print("Application startup complete.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Code to run on application shutdown.
    """
    print("Application shutdown complete.")


# routes.py
# This file should be in the same directory as main.py

from fastapi import APIRouter, Path
from pydantic import BaseModel

# Create an API router instance
router = APIRouter()

# --- Pydantic Models for Request/Response ---

class Item(BaseModel):
    id: int
    name: str
    description: str | None = None

# --- API Endpoints ---

@router.get("/greet", tags=["General"])
async def greet_user(name: str = "World"):
    """
    A simple greeting endpoint.
    Accepts an optional 'name' query parameter.
    """
    return {"message": f"Hello, {name}!"}


@router.get("/items/{item_id}", response_model=Item, tags=["Items"])
async def get_item(item_id: int = Path(..., title="The ID of the item to get", ge=1)):
    """
    Fetches a single item by its ID.
    This is a sample endpoint and returns a mock item.
    """
    return {
        "id": item_id,
        "name": f"Sample Item {item_id}",
        "description": "This is a sample description."
    }