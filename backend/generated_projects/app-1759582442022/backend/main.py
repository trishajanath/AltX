import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# This section would typically be in a separate file like `routes.py`
# --------------------------------------------------------------------
api_router = APIRouter()

@api_router.get("/items/", tags=["Items"])
async def read_items():
    """
    Example endpoint to retrieve a list of items.
    """
    return [{"id": 1, "name": "Sample Item 1"}, {"id": 2, "name": "Sample Item 2"}]

@api_router.get("/users/me", tags=["Users"])
async def read_user_me():
    """
    Example endpoint to retrieve the current user's data.
    """
    return {"user_id": "current_user", "email": "user@example.com"}
# --------------------------------------------------------------------


# Create the main FastAPI application instance
app = FastAPI(
    title="app-1759582442022",
    description="FastAPI application with CORS, a versioned API, and a health check.",
    version="1.0.0",
)

# Add CORS (Cross-Origin Resource Sharing) middleware
# This allows web pages from any origin to make requests to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define the root health check endpoint
@app.get("/", tags=["Health Check"])
def health_check():
    """
    Provides a simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Include the API router with the specified prefix
# All routes defined in `api_router` will be available under `/api/v1`
app.include_router(api_router, prefix="/api/v1")

# The following block allows running the app directly with `python main.py`
# It's useful for development but not recommended for production.
# A production deployment would use a process manager like Gunicorn or Uvicorn directly.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)