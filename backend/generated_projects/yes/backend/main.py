# main.py
# To run this application:
# 1. Save this code as `main.py`.
# 2. Save the second code block as `routes.py` in the same directory.
# 3. Install dependencies: pip install "fastapi[all]"
# 4. Run the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from your routes file
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="My FastAPI Project",
    description="A sample FastAPI application with a structured layout.",
    version="1.0.0",
)

# Define allowed origins for CORS
# Using ["*"] is permissive. For production, you should restrict this
# to your frontend's domain, e.g., ["https://your-frontend.com"].
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "*" # Allow all for development purposes
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
    Simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}

# Include the API router with a prefix
# All routes defined in `routes.py` will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# Example of how to run the app if this file is executed directly
# This is useful for debugging but `uvicorn` is recommended for production
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

```

```python
# routes.py
# This file should be in the same directory as main.py

from fastapi import APIRouter, Path
from pydantic import BaseModel

# Create an API router instance
router = APIRouter()

# Define a Pydantic model for request body validation (example)
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

# Define a sample route for the API
@router.get("/", tags=["General"])
async def read_api_root():
    """
    Root endpoint for the v1 API.
    """
    return {"message": "Welcome to API v1"}

@router.get("/items/{item_id}", tags=["Items"])
async def read_item(
    item_id: int = Path(..., title="The ID of the item to get", ge=1),
    q: str | None = None
):
    """
    Retrieve a single item by its ID.
    """
    return {"item_id": item_id, "q": q}

@router.post("/items/", tags=["Items"], status_code=201)
async def create_item(item: Item):
    """
    Create a new item.
    """
    return {"item_name": item.name, "status": "created"}