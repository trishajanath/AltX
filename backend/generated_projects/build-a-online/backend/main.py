from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .models import HealthCheck
from .routes import router as music_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="A modern, production-ready backend for an online web music player.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

#  Middleware Configuration 

# Set up CORS (Cross-Origin Resource Sharing)
# This is a security measure to control which frontends can access the API.
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

#  API Routers 

# Include the main router for music-related endpoints
app.include_router(music_router, prefix=settings.API_V1_STR, tags=["Music"])

#  Core Endpoints 

@app.get("/", include_in_schema=False)
def read_root():
    """
    Redirects the root path to the API documentation.
    """
    return RedirectResponse(url="/docs")

@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Health Check",
    description="Returns the operational status of the API."
)
def health_check():
    """
    Health check endpoint.
    A simple endpoint to verify that the API is running and responsive.
    Useful for load balancers and uptime monitoring.
    """
    return {"status": "ok"}

#  Application Startup 
# Example of how to run the application using uvicorn:
# uvicorn main:app --reload