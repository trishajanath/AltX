from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Assuming your routes are defined in a file named `routes.py`
# in the same directory.
from routes import router as api_router

# 1. Create FastAPI app instance
app = FastAPI(
    title="Ecommerce Platform API",
    description="API for the ecommerce platform app-1759346830816.",
    version="1.0.0",
)

# 2. Configure CORS middleware
# This allows cross-origin requests, which is essential for frontend applications
# consuming this API from a different domain.
# For production, you should restrict origins to your frontend's domain.
origins = [
    "*",  # Allows all origins for development purposes
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# 3. Include the main API router
# All routes defined in the `routes.py` file will be included here.
# A prefix helps in versioning and organizing the API endpoints.
app.include_router(api_router, prefix="/api/v1")

# 4. Add a root endpoint for health checks
@app.get("/", tags=["Health Check"])
async def read_root():
    """
    Root endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Welcome to the Ecommerce Platform API"}

# To run this application:
# 1. Make sure you have a `routes.py` file with a FastAPI APIRouter instance named `router`.
# 2. Run the command: uvicorn main:app --reload