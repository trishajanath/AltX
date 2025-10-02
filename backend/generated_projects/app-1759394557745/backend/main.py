# main.py
# To run this app, save the second code block as routes.py in the same directory.
# Then run: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759394557745",
    description="A FastAPI application with CORS, a versioned API, and a health check.",
    version="1.0.0",
)

# --- Middleware ---

# Set up CORS (Cross-Origin Resource Sharing)
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict this to your frontend's domain.
origins = [
    "*",  # In a real-world scenario, replace "*" with your frontend's URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


# --- Root Endpoint / Health Check ---

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint.
    Returns a JSON response indicating the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}


# --- API Router ---

# Include the router from routes.py with a URL prefix
# All routes defined in routes.py will be available under /api/v1
app.include_router(api_router, prefix="/api/v1", tags=["API V1"])

```

```python
# routes.py
# This file should be in the same directory as main.py

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

# Create a new router object
router = APIRouter()

# --- Pydantic Models for Request/Response ---

class Item(BaseModel):
    name: str = Field(..., example="Sample Item")
    description: str | None = Field(None, example="This is a description.")
    price: float = Field(..., gt=0, example=9.99)
    is_offer: bool | None = Field(None, example=False)

class ItemResponse(BaseModel):
    item_id: int
    item_data: Item


# --- API Endpoints ---

@router.get("/")
async def read_root():
    """
    Root endpoint for the v1 API.
    """
    return {"message": "Welcome to API v1 for app-1759394557745"}

@router.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(
    item_id: int = Path(..., title="The ID of the item to get", ge=1),
    q: str | None = None
):
    """
    Retrieve an item by its ID.
    - **item_id**: The unique identifier for the item.
    - **q**: An optional query parameter.
    """
    # In a real application, you would fetch this data from a database
    sample_item_data = {
        "name": f"Item {item_id}",
        "price": 10.50,
        "description": f"Details for item {item_id}"
    }
    return {"item_id": item_id, "item_data": sample_item_data}

@router.post("/items/", response_model=ItemResponse, status_code=201)
async def create_item(item: Item):
    """
    Create a new item.
    """
    # In a real application, you would save the item to a database
    # and get a new ID. Here, we'll just simulate it.
    new_item_id = 123  # Simulated new ID from DB
    return {"item_id": new_item_id, "item_data": item}