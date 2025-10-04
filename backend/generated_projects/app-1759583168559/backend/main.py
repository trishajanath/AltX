import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# In a larger application, the APIRouter and its routes would be in a separate file
# like `api/routes.py`. For this request, it's included here.
#
# --- Start of conceptual routes.py ---

# Create a new router with a prefix for versioning the API
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/info")
async def get_app_info():
    """
    Returns basic information about the application.
    """
    return {"app_name": "app-1759583168559", "api_version": "v1"}

@api_router.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """
    A sample endpoint to retrieve an item by its ID.
    """
    return {"item_id": item_id, "q": q}

# --- End of conceptual routes.py ---


# Initialize the main FastAPI application
app = FastAPI(
    title="app-1759583168559",
    description="A simple FastAPI application with CORS and a versioned API.",
    version="1.0.0"
)

# Set up CORS (Cross-Origin Resource Sharing) middleware
# This allows requests from any origin. For production, you should
# restrict this to a list of allowed domains.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the router from our "routes.py" section
app.include_router(api_router)

# Define the root health check endpoint
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}

# The following block allows running the app directly with `python main.py`
# It's common for development but for production, a process manager like Gunicorn
# with Uvicorn workers is recommended.
if __name__ == "__main__":
    # To run this app:
    # 1. Save the code as main.py
    # 2. Install dependencies: pip install fastapi "uvicorn[standard]"
    # 3. Run from the terminal: uvicorn main:app --reload
    #
    # You can then access:
    # - Health check: http://127.0.0.1:8000/
    # - API endpoint: http://127.0.0.1:8000/api/v1/info
    # - Interactive API docs: http://127.0.0.1:8000/docs
    uvicorn.run(app, host="0.0.0.0", port=8000)