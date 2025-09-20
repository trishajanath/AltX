```python
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from config import settings
from routes import router as api_router

#  AI Model Loading 
# This dictionary will hold our loaded AI models.
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager to handle application startup and shutdown events.
    This is the modern replacement for @app.on_event("startup") and "shutdown".
    """
    # Startup: Load ML models
    print("Application startup: Loading AI models...")
    # In a real app, you would replace these mocks with actual model loading.
    # from ai_services import SentimentAnalysisService, RecommendationService
    # ml_models["sentiment_analyzer"] = SentimentAnalysisService()
    # ml_models["recommender"] = RecommendationService()
    ml_models["sentiment_analyzer"] = "Mock Sentiment Model Loaded"
    ml_models["recommender"] = "Mock Recommender Model Loaded"
    print("AI models loaded successfully.")
    
    yield
    
    # Shutdown: Clean up resources
    print("Application shutdown: Clearing ML models...")
    ml_models.clear()
    print("Resources cleaned up.")

#  FastAPI App Initialization 
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

#  Middleware Configuration 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Custom Exception Handlers 
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors to provide more informative responses.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors()
        },
    )

#  API Router Inclusion 
app.include_router(api_router, prefix=settings.API_V1_STR)

#  Root and Health Check Endpoints 
@app.get("/", tags=["Root"])
async def read_root():
    """
A welcome endpoint for the E-Commerce API.
"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API v{settings.PROJECT_VERSION}",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to verify that the API is running.
    """
    # You could add checks for database connectivity or other services here.
    return {"status": "ok", "models_loaded": list(ml_models.keys())}

# To run this application:
# 1. Create a virtual environment and install dependencies from requirements.txt
#    python -m venv venv
#    source venv/bin/activate
#    pip install -r requirements.txt
# 2. Run the server with uvicorn:
#    uvicorn main:app --reload
```