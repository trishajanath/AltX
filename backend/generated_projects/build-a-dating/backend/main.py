```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import router as api_router
from .models import HealthCheck

#  Application Object 
# Provides metadata for OpenAPI docs
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="A functional backend for a Tinder-like dating application using FastAPI.",
    version="1.0.0"
)

#  Middleware 

# CORS (Cross-Origin Resource Sharing)
# This allows the frontend (e.g., a React app on localhost:5173) to communicate with this backend.
# In production, you would restrict this to your actual frontend domain.
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],  # Allows all standard HTTP methods
        allow_headers=["*"],  # Allows all headers
    )

#  Exception Handlers 

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled exceptions and returns a generic 500 error.
    This prevents leaking stack traces or sensitive information to the client.
    """
    # In a real app, you would log the exception details here.
    # import logging
    # logging.exception("An unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

#  API Routers 

# Health check endpoint
@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Perform a Health Check",
    description="Verifies that the API service is up and running."
)
def health_check():
    """
    Endpoint to confirm that the API is operational.
    """
    return HealthCheck(status="ok")

# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["Dating App"])

#  Startup/Shutdown Events (Optional) 
@app.on_event("startup")
async def startup_event():
    """
    Code to run on application startup.
    This is a good place for initializing database connections, etc.
    """
    print("🚀 Starting Build-A-Dating App API...")
    # Since there's no DB, we just print a message.
    # In a real app: await database.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """
    Code to run on application shutdown.
    This is for gracefully closing connections.
    """
    print("👋 Shutting down Build-A-Dating App API...")
    # In a real app: await database.disconnect()

```