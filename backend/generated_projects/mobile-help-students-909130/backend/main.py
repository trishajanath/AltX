import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Assuming a routes.py file exists in the same directory
# from .routes import router as api_router
# For a simple structure, a direct import is fine.
from routes import router as api_router

# Create FastAPI app instance
app = FastAPI(
    title="mobile-help-students-909130",
    description="API for the Mobile Help Students project.",
    version="1.0.0"
)

# CORS (Cross-Origin Resource Sharing)
# This allows web pages from any domain to make requests to this API.
# For production, you should restrict this to your frontend's domain.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Endpoint to check if the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Include the API router
# All routes from routes.py will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# The following block allows running the app directly with `python main.py`
# This is useful for development.
# For production, you would use a process manager like Gunicorn or Uvicorn directly.
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)