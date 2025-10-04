# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
# This assumes a file named routes.py exists in the same directory.
from routes import router as api_v1_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759586022988",
    description="FastAPI application with CORS, a health check, and a versioned API.",
    version="1.0.0",
)

# --- Middleware ---

# Configure CORS (Cross-Origin Resource Sharing)
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict this to your frontend's domain.
origins = [
    "*",  # Allows all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# --- Routers ---

# Include the router from routes.py with the specified prefix
app.include_router(api_v1_router, prefix="/api/v1")

# --- Root Endpoint / Health Check ---

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint.
    Returns a JSON response indicating the service is operational.
    """
    return {"status": "ok", "message": "Service is running"}

```
```python
# routes.py
from fastapi import APIRouter

# Create a new router object
router = APIRouter()

@router.get("/hello", summary="Example Endpoint")
async def read_hello():
    """
    An example endpoint that returns a welcome message.
    This will be accessible at /api/v1/hello
    """
    return {"message": "Hello from API v1"}

# Add more routes for your application below
# Example:
# @router.get("/items/{item_id}")
# async def read_item(item_id: int, q: str | None = None):
#     return {"item_id": item_id, "q": q}