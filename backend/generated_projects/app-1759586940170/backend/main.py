# main.py
# To run this application:
# 1. Save this file as main.py
# 2. Save the routes.py file (provided below) in the same directory.
# 3. Install dependencies: pip install fastapi "uvicorn[standard]"
# 4. Run the server: uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from the routes module
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="app-1759586940170",
    description="A FastAPI application with CORS, a prefixed API router, and a health check.",
    version="1.0.0",
)

# --- Middleware Configuration ---

# Add CORS middleware to allow cross-origin requests from any origin.
# For production, you should restrict this to specific domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- API Router ---

# Include the router from routes.py with the specified prefix.
# All routes defined in routes.py will be available under /api/v1.
app.include_router(api_router, prefix="/api/v1")

# --- Root Endpoint / Health Check ---

@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint to confirm the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# --- routes.py ---
# Create a new file named routes.py in the same directory and add the following code.

"""
from fastapi import APIRouter

# Create a new router object
router = APIRouter()

@router.get("/hello", tags=["Example"])
async def say_hello():
    '''
    An example endpoint that returns a simple greeting.
    Accessible at /api/v1/hello
    '''
    return {"message": "Hello from API v1"}

@router.get("/data", tags=["Data"])
async def get_data():
    '''
    Another example endpoint to demonstrate the router.
    Accessible at /api/v1/data
    '''
    return {"data": [1, 2, 3], "source": "app-1759586940170"}
"""