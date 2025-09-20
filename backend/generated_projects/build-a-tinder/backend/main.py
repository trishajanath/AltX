```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .models import HealthCheck
from .routes import router as api_router

#  Application Initialization 

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A modern backend for a Tinder-like dating application.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

#  Middleware Configuration 

# 
🛡️ CORS (Cross-Origin Resource Sharing) Middleware
# This is a critical security feature that controls which domains can access your API.
# The configuration below allows the React frontend running on localhost:5173
# to communicate with the backend. For production, you would replace this with
# your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

#  Exception Handlers 

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors.
    This provides a more structured error response to the client,
    making it easier for frontend developers to handle input errors.
    """
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": error_details},
    )

#  API Routers 

# Include the main API router from routes.py
app.include_router(api_router)

#  Core Endpoints 

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    Useful for simple uptime checks or as a landing point for the API.
    """
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}"}

@app.get("/health", response_model=HealthCheck, tags=["Health Check"])
async def health_check():
    """

    Health check endpoint.
    Provides a simple, unauthenticated endpoint to verify that the API is running.
    Essential for monitoring, load balancers, and automated deployment systems.
    """
    return HealthCheck(status="ok", version=settings.APP_VERSION)

#  Startup/Shutdown Events (Optional) 

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    Example: Connecting to a database, initializing caches, etc.
    """
    print(f"Starting up {settings.APP_NAME}...")
    # In a real app, you would initialize your database connection pool here.
    # e.g., await database.connect()
    print("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    Example: Disconnecting from databases, closing network connections, etc.
    """
    print(f"Shutting down {settings.APP_NAME}...")
    # In a real app, you would gracefully close database connections here.
    # e.g., await database.disconnect()
    print("Application shutdown complete.")
```