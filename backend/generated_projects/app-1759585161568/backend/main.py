# In order to run this application, you need two files.
# 1. Save the first block of code as `routes.py`.
# 2. Save the second block of code as `main.py`.
# 3. Run `uvicorn main:app --reload` in your terminal.

# File: routes.py
# ------------------------------------------------

from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_sample_data():
    """
    An example endpoint that returns sample data for app-1759585161568.
    This will be accessible at /api/v1/data
    """
    return {
        "app_id": "app-1759585161568",
        "status": "success",
        "data": {
            "item_id": 123,
            "item_name": "Sample Item",
            "is_available": True
        }
    }

# ------------------------------------------------
# File: main.py
# ------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from your routes file
from routes import router as api_v1_router

# Initialize the FastAPI app
app = FastAPI(
    title="app-1759585161568",
    description="A FastAPI application with CORS, a versioned API, and a health check.",
    version="1.0.0"
)

# Set up CORS (Cross-Origin Resource Sharing)
# This allows web pages from any domain to make requests to your API.
# For production, you should restrict this to specific domains.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint for health check
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Endpoint to verify that the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Include the API router with a specific prefix
# All routes defined in `routes.py` will be prefixed with /api/v1
app.include_router(
    api_v1_router,
    prefix="/api/v1",
    tags=["API v1"]
)

# To run this application:
# 1. Make sure you have `fastapi` and `uvicorn` installed:
#    pip install fastapi "uvicorn[standard]"
# 2. Save the code blocks above into `routes.py` and `main.py`.
# 3. In your terminal, run the command:
#    uvicorn main:app --reload
#
# You can then access the API documentation at http://127.0.0.1:8000/docs