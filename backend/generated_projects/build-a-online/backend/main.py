```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .routes import router as api_router

# 
🛡️ Advanced Security Analysis:
# This setup includes key security best practices:
# 1.  CORS Configuration: Strict origin whitelisting prevents unauthorized domains from making requests.
#     Using '*' for origins is a major security risk (CSRF) and is avoided here.
# 2.  Centralized Routing: Using an APIRouter helps in organizing the code and applying middleware/dependencies cleanly.
# 3.  Pydantic Validation: All incoming data is rigorously validated against the Pydantic models in `models.py`.
#     This is the first line of defense against injection attacks, data type mismatches, and malformed payloads.
# 4.  Custom Exception Handling: Provides a consistent, non-revealing error format to clients,
#     avoiding leakage of internal application states or stack traces.
# 5.  Health Check Endpoint: Essential for production monitoring, load balancers, and container orchestrators (like Kubernetes).

#  FastAPI Application Initialization 
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

#  CORS Middleware Configuration 
# This is a critical security feature for frontend integrations.
# It allows the React frontend (running on localhost:5173) to access the API.
# In production, you would replace the localhost origin with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

#  Custom Exception Handler for Validation Errors 
# This ensures that API validation errors are returned in a clean, consistent JSON format.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

#  API Router Inclusion 
# Includes all the endpoints defined in the routes.py file.
app.include_router(api_router, prefix=settings.API_V1_STR)

#  Root and Health Check Endpoints 
@app.get("/", tags=["Health"])
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": f"Welcome to the {settings.PROJECT_NAME}"}

@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for monitoring services.
    Returns a 200 OK status if the API is running.
    """
    return {"status": "ok"}

#  Startup/Shutdown Events (Optional) 
# Useful for initializing resources like database connections.
@app.on_event("startup")
async def startup_event():
    """
    Code to run on application startup.
    For example, connecting to a database.
    """
    print("FastAPI application starting up...")
    # In a real app, you might initialize a database connection pool here.

@app.on_event("shutdown")
async def shutdown_event():
    """
    Code to run on application shutdown.
    For example, closing database connections.
    """
    print("FastAPI application shutting down...")
    # Clean up resources, like closing a database connection pool.
```