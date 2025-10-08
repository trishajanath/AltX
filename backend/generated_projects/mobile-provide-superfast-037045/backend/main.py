import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# The following import assumes a 'routes.py' file exists in the same directory
# and contains an APIRouter instance named 'router'.
#
# Example for routes.py:
#
# from fastapi import APIRouter
#
# router = APIRouter()
#
# @router.get("/example")
# async def get_example():
#     return {"message": "This is an example route"}
#
from routes import router as api_router

# --- App Initialization ---
app = FastAPI(
    title="mobile-provide-superfast-037045",
    description="API for mobile-provide-superfast-037045",
    version="1.0.0",
)

# --- CORS Middleware ---
# Allows all origins, methods, and headers.
# Adjust the 'allow_origins' list for production environments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Root Endpoint / Health Check ---
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "API is healthy"}

# --- Include API Routes ---
# All routes from routes.py will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# --- Main Entry Point (for development) ---
if __name__ == "__main__":
    # This block allows running the app directly with 'python main.py'
    # Uvicorn is a lightning-fast ASGI server.
    uvicorn.run(app, host="0.0.0.0", port=8000)