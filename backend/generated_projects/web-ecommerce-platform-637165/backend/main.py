# main.py
# To run this application:
# 1. Save this code as `main.py`.
# 2. Save the second code block as `routes.py` in the same directory.
# 3. Install dependencies: `pip install "fastapi[all]"`
# 4. Run the server: `uvicorn main:app --reload`

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the router from your routes file
from routes import router as api_router

# Create the FastAPI app instance
app = FastAPI(
    title="Web E-commerce Platform API",
    description="API for the web-ecommerce-platform-637165 project.",
    version="1.0.0",
)

# Define allowed origins for CORS.
# Using ["*"] allows all origins, which is convenient for development.
# For production, you should restrict this to your frontend's domain.
origins = [
    "*",
    # "http://localhost",
    # "http://localhost:3000",
    # "https://your-frontend-domain.com",
]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Health check endpoint at the root URL
@app.get("/", tags=["Health Check"])
async def health_check():
    """
    Provides a simple health check endpoint.
    Returns a JSON response indicating the API is running.
    """
    return {"status": "ok", "message": "API is running"}

# Include the API router with a specific prefix
# All routes defined in `routes.py` will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

# Optional: Add startup/shutdown events if needed for database connections, etc.
@app.on_event("startup")
async def startup_event():
    print("Application startup...")
    # Example: await database.connect()

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown...")
    # Example: await database.disconnect()

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)