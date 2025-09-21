from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import application-specific components
from config import settings
from routes import router as api_router
from routes import RecipeNotFoundException

#  Application Lifespan Management 
# Using an async context manager for lifespan events is the modern approach
# for handling startup and shutdown logic in FastAPI.

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on application startup
    print(f"Starting up '{settings.PROJECT_NAME}'...")
    # In a real app, you would initialize resources here, e.g.:
    # app.state.db_connection_pool = await create_db_pool()
    yield
    # Code to run on application shutdown
    print(f"Shutting down '{settings.PROJECT_NAME}'...")
    # Clean up resources, e.g.:
    # await app.state.db_connection_pool.close()

#  FastAPI App Initialization 
# Initialize the main FastAPI application instance with lifespan management.
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

#  Middleware Configuration 
# Configure CORS to allow the frontend to communicate with this backend.
# This is a critical security feature for web applications.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all standard HTTP methods
    allow_headers=["*"],  # Allows all headers
)

#  Custom Exception Handlers 
# This handler catches the custom RecipeNotFoundException and ensures
# a consistent HTTP 404 response format is sent to the client.

@app.exception_handler(RecipeNotFoundException)
async def recipe_not_found_exception_handler(request: Request, exc: RecipeNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )

#  API Routers 

# Health check endpoint for monitoring and uptime checks.
@app.get("/health", tags=["Health Check"])
def health_check():
    """A simple endpoint to confirm that the API is running and responsive."""
    return {"status": "ok"}

# Include the main API router with all the recipe endpoints.
# All routes from routes.py will be prefixed with `/api/v1`.
app.include_router(api_router, prefix=settings.API_V1_STR)

# To run this application:
# 1. Make sure you have all packages from requirements.txt installed.
# 2. Run the command: uvicorn main:app --reload
# 3. Access the interactive API documentation at http://127.0.0.1:8000/docs