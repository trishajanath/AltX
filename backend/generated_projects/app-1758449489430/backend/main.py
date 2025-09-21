from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import settings
from .routes import router as api_router
from .models import HealthCheck

# 
# Application Initialization
# 

# Create the FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description="A simple API for managing college events.",
    version="1.0.0"
)

# 
# Middleware Configuration
# 

# Set up CORS (Cross-Origin Resource Sharing) middleware.
# This is crucial for allowing the React frontend (running on a different port)
# to communicate with this backend.
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# 
# Custom Exception Handlers
# 

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for Pydantic's validation errors.
    This provides a more structured error response to the client, making it
    easier for frontend developers to handle input errors.
    """
    details = []
    for error in exc.errors():
        details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=422,
        content={"detail": details},
    )

# 
# API Routers and Endpoints
# 

# Include the API router from the 'routes.py' file.
# All routes defined in that router will be prefixed with '/api/v1'.
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Root endpoint: Redirects to the API documentation for discoverability.
@app.get("/", include_in_schema=False)
async def root():
    """
    Redirects the root URL to the API documentation.
    """
    return RedirectResponse(url="/docs")

# Health check endpoint: Essential for monitoring and deployment environments.
@app.get(
    "/api/health",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Perform a Health Check",
    description="Responds with a 200 OK status if the API is running."
)
def perform_health_check():
    """
    This endpoint can be used by monitoring services (like Kubernetes liveness probes)
    to verify that the application is operational.
    """
    return {"status": "ok"}

# 
# Startup and Shutdown Events (Optional)
# 

# @app.on_event("startup")
# async def startup_event():
#     """
#     Code to run on application startup.
#     For example, connecting to a database.
#     """
#     print("Application startup...")

# @app.on_event("shutdown")
# async def shutdown_event():
#     """
#     Code to run on application shutdown.
#     For example, disconnecting from a database.
#     """
#     print("Application shutdown...")