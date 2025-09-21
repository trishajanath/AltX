# main.py
# Main application entry point for the FastAPI server.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .routes import router as api_router
from .database import initialize_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for application lifespan events.
    This is the recommended way to handle startup and shutdown logic in modern FastAPI.
    """
    #  Startup 
    print("🚀 Starting application...")
    initialize_db()
    yield
    #  Shutdown 
    print("👋 Shutting down application...")

# Create the FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

#  Middleware Configuration 

# Set up CORS (Cross-Origin Resource Sharing)
# This is crucial for allowing frontend applications from different origins
# to communicate with this API.
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

#  API Router 
# Include the routes defined in the routes.py file.
# The prefix makes all routes in that file start with /api.
app.include_router(api_router, prefix=settings.API_V1_STR)

#  Health Check Endpoint 
@app.get("/health", tags=["Health Check"])
async def health_check():
    """

    A simple health check endpoint to confirm the API is running.
    This is useful for load balancers, container orchestrators (like Kubernetes),
    and monitoring systems.
    """
    return {"status": "ok", "message": "API is healthy"}

# To run the application:
# 1. Make sure you are in the directory containing this file.
# 2. Run the command: uvicorn main:app --reload
#    - `uvicorn`: The ASGI server.
#    - `main`: The Python file (main.py).
#    - `app`: The FastAPI instance object in main.py.
#    - `--reload`: Automatically restart the server when code changes.