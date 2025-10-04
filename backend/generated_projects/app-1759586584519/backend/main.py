# In a file named: routes.py
# -------------------------------------

from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["API V1"])
async def get_root_v1():
    """
    Root endpoint for API version 1.
    """
    return {"message": "Welcome to API v1 for app-1759586584519"}

@router.get("/items/{item_id}", tags=["API V1"])
async def read_item(item_id: int, q: str | None = None):
    """
    Example endpoint to retrieve an item by its ID.
    """
    return {"item_id": item_id, "q": q}


# In a file named: main.py
# -------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from routes.py
# Ensure routes.py is in the same directory as main.py
from routes import router as api_v1_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759586584519",
    description="A FastAPI application with a versioned API and health check.",
    version="1.0.0",
)

# CORS (Cross-Origin Resource Sharing) Middleware
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict the origins to your frontend's domain.
origins = [
    "*",  # Allows all origins
    # "http://localhost",
    # "http://localhost:3000",
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint at the root ("/")
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Include the router from routes.py with the /api/v1 prefix
app.include_router(api_v1_router, prefix="/api/v1")

# To run this application:
# 1. Save the first part as `routes.py`.
# 2. Save the second part as `main.py`.
# 3. Make sure you have the necessary libraries:
#    pip install "fastapi[all]"
# 4. Run the server from your terminal:
#    uvicorn main:app --reload