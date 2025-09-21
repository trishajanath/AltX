```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import settings
from .routes import router as api_router

#  FastAPI App Initialization 
# This is the main entry point of the application.
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

#  CORS Middleware Configuration 
# This middleware handles Cross-Origin Resource Sharing, which is essential
# for allowing your frontend (e.g., a React app) to communicate with this backend.
# The configuration is strict, only allowing origins specified in the settings.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

#  Custom Exception Handlers 
# These handlers ensure that errors are returned in a clean, consistent JSON format.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors to provide more structured error messages.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors(),
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent leaking stack traces and return a
    standardized 500 error. In production, you would log the exception here.
    """
    # In a real app, you would log the full exception `exc` here.
    # For example: logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred.",
            "error_type": type(exc).__name__,
        },
    )

#  API Router Inclusion 
# The main application includes the router defined in routes.py.
# All routes from that file will be prefixed with /api/v1.
app.include_router(api_router, prefix=settings.API_V1_STR)

#  Root and Health Check Endpoints 

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": f"Welcome to the {settings.APP_NAME}"}

@app.get("/health", tags=["Health Check"], status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint used by monitoring services to verify API health.
    """
    return {"status": "ok"}

# To run this application:
# 1. Make sure you have installed the dependencies from requirements.txt:
#    pip install -r requirements.txt
# 2. Run the server using uvicorn:
#    uvicorn main:app --reload
```