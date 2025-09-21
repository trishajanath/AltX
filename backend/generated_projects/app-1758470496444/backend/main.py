from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import router as api_router
from .database import initialize_db

#  Application Setup 
# Create the main FastAPI application instance.
# The `title`, `description`, and `version` parameters are used for the auto-generated API documentation.
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="A simple and modern API for a Todo application.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" # Custom OpenAPI schema URL
)

#  Middleware Configuration 
# Configure CORS (Cross-Origin Resource Sharing) to allow the frontend to communicate with this backend.
# This is a critical security feature for web applications.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # List of allowed origins (e.g., your frontend URL)
    allow_credentials=True,             # Allow cookies to be included in requests
    allow_methods=["*"],                # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],                # Allow all headers
)

#  Event Handlers 
@app.on_event("startup")
def on_startup():
    """
    This function runs when the application starts up.
    It's a good place to initialize resources, like our in-memory database.
    """
    print(" Initializing in-memory database with sample data ")
    initialize_db()
    print(" Database initialized ")

#  API Router Inclusion 
# Include the API router defined in `routes.py`.
# All routes from the router will be prefixed with `/api`.
app.include_router(api_router, prefix=settings.API_V1_STR)

#  Root and Health Check Endpoint 
@app.get("/", tags=["Health Check"])
async def root():
    """
    A simple root endpoint that can be used as a health check.
    It confirms that the application is running and responsive.
    """
    return {"status": "ok", "message": f"Welcome to {settings.PROJECT_NAME}!"}

# To run this application:
# 1. Ensure you have all dependencies from requirements.txt installed (`pip install -r requirements.txt`).
# 2. Run the command: `uvicorn main:app --reload` in your terminal.
# 3. Access the API at http://127.0.0.1:8000
# 4. Access the interactive API documentation at http://127.0.0.1:8000/docs