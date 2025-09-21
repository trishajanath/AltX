```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from .config import settings
from . import routes

# 
# FastAPI App Initialization
# 
app = FastAPI(
    title=settings.APP_NAME,
    description="A modern, high-performance API backend for a Temu-like e-commerce platform.",
    version="1.0.0",
    contact={
        "name": "GitHub Copilot",
        "url": "https://github.com/features/copilot",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    # Disables the default /docs and /redoc to be served under the API prefix
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc"
)

# 
# Middleware Configuration
# 

# Add CORS Middleware
# This is crucial for allowing the frontend application (e.g., React on localhost:5173)
# to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all standard HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Add a simple middleware to measure request processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 
# API Routers
# 
# Include the routes from the routes.py file, prefixing them with /api/v1
app.include_router(routes.router, prefix=settings.API_V1_PREFIX)

# 
# Root and Health Check Endpoints
# 

@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint providing a welcome message and basic API information.
    """
    return {
        "message": f"Welcome to the {settings.APP_NAME}",
        "documentation_urls": {
            "swagger_ui": app.docs_url,
            "redoc": app.redoc_url
        }
    }

@app.get(
    "/health",
    tags=["Health Check"],
    summary="Perform a Health Check",
    response_description="Returns the operational status of the API."
)
def perform_health_check():
    """

    This endpoint is used by monitoring services (like Kubernetes liveness probes)
    to verify that the application is running and healthy.
    """
    return JSONResponse(content={"status": "ok"})

# 
# Main Entry Point (for running with `python main.py`)
# In production, you would use a process manager like Gunicorn or Uvicorn directly.
# Example: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```