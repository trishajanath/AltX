# main.py
# To run this application:
# 1. Save this file as `main.py`.
# 2. Save the second code block as `routes.py` in the same directory.
# 3. Install dependencies: pip install "fastapi[all]"
# 4. Run the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
from routes import router as api_router

# Initialize the FastAPI app
app = FastAPI(
    title="FastAPI Boilerplate",
    description="A simple FastAPI application with CORS and a structured router.",
    version="1.0.0"
)

# Define allowed origins for CORS.
# Using ["*"] is permissive. For production, you should list your specific frontend domains.
origins = [
    "*",
    # "http://localhost",
    # "http://localhost:3000",
    # "https://your.frontend.domain",
]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint at the root
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Endpoint to check if the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Include the API router with a prefix
# All routes defined in routes.py will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# Example of how to run the app directly (for simple testing, not for production)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

```

```python
# routes.py
# This file contains the API routes for the /api/v1 prefix.
# It should be saved in the same directory as main.py.

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

# Create an API router instance
router = APIRouter()

# Pydantic model for request body validation
class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, example="Laptop")
    description: str | None = Field(None, max_length=300, example="A powerful computing device")
    price: float = Field(..., gt=0, example=999.99)
    is_offer: bool | None = None

# A simple GET endpoint
@router.get("/", tags=["General"])
async def get_api_root():
    """
    Root endpoint for the v1 API.
    """
    return {"message": "Welcome to API version 1"}

# GET endpoint with a path parameter
@router.get("/items/{item_id}", tags=["Items"])
async def get_item(item_id: int = Path(..., title="The ID of the item to get", ge=1)):
    """
    Retrieve a single item by its ID.
    """
    return {"item_id": item_id, "name": f"Sample Item {item_id}"}

# POST endpoint to create a new item
@router.post("/items/", tags=["Items"], status_code=201)
async def create_item(item: Item):
    """
    Create a new item. This endpoint demonstrates request body validation.
    """
    return {"message": "Item created successfully", "item_data": item.dict()}