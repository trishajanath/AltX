# main.py
# This file is the entry point for the FastAPI application. It initializes the app,
# sets up CORS middleware, includes the API routers, and defines root/health endpoints.

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes import student_router
from config import settings

# Initialize the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A simple API to track student attendance in a classroom.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# 
🛡️ Configure CORS (Cross-Origin Resource Sharing)
# This is a critical security feature that controls which frontend domains
# are allowed to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all standard HTTP methods
    allow_headers=["*"],  # Allows all headers
)

#  API Routers 
# Include the specific routers for different parts of the application.
# This modular approach keeps the codebase clean and organized.
app.include_router(student_router, prefix="/api/students", tags=["Students"])

#  Root and Health Check Endpoints 

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint to welcome users to the API.
    """
    return {"message": f"Welcome to the {settings.APP_NAME}"}

@app.get("/api/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to verify that the API is running.
    Useful for monitoring and deployment checks.
    """
    return {"status": "ok", "version": settings.APP_VERSION}

#  Exception Handlers (Optional but good practice) 

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled exceptions to prevent leaking stack traces.
    """
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected server error occurred."},
    )