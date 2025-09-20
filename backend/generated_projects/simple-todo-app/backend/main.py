```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Import settings and routes from local modules
from .config import settings
from . import routes

# 
# FastAPI App Initialization
# 
# We initialize the FastAPI app with metadata that will be used in the OpenAPI docs.
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="A simple, modern, and production-ready Todo App API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 
# CORS (Cross-Origin Resource Sharing) Middleware
# 
# This middleware is essential for frontend applications to communicate with the API.
# It controls which origins (domains) are allowed to make requests.
# The configuration is loaded from our settings file for better management.
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# 
# API Router Inclusion
# 
# We include the router from routes.py.
# All routes defined in that module will be prefixed with /api/v1.
# This is a standard practice for versioning APIs.
app.include_router(routes.router, prefix=settings.API_V1_STR)

# 
# Root and Health Check Endpoints
# 

@app.get("/", include_in_schema=False)
def read_root():
    """
    Redirects the root URL to the API documentation.
    This provides a user-friendly entry point to the API.
    """
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    This can be used by monitoring services (like Kubernetes liveness probes)
    to verify that the application is running and healthy.
    """
    return {"status": "ok", "project": settings.PROJECT_NAME}

# Example of startup event (not strictly necessary for this simple app)
# @app.on_event("startup")
# async def startup_event():
#     print("Application is starting up...")
#     # Here you could initialize database connections, etc.

# Example of shutdown event
# @app.on_event("shutdown")
# async def shutdown_event():
#     print("Application is shutting down...")
#     # Here you could close database connections, etc.
```