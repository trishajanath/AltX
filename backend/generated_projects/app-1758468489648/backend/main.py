from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import router as event_router
from .database import initialize_mock_data

# Initialize the FastAPI app with metadata from the config
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

#  Middleware Configuration 

# Configure CORS (Cross-Origin Resource Sharing)
# This is crucial for allowing the React frontend (running on a different port)
# to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # List of allowed origins from config
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

#  Event Handlers 

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform when the application starts up.
    Here, we initialize our in-memory database with mock data.
    """
    print("Application startup: Initializing mock data...")
    initialize_mock_data()
    print("Mock data initialized.")

#  API Routes 

@app.get("/", tags=["Root"], summary="Root Endpoint")
async def read_root():
    """
    A simple welcome message for the API root.
    """
    return {"message": f"Welcome to the {settings.APP_NAME}"}

@app.get("/health", tags=["Health Check"], summary="Health Check Endpoint")
async def health_check():
    """
    A simple health check endpoint that can be used by monitoring services
    to verify that the application is running.
    """
    return {"status": "ok"}

# Include the specific API routes for event management
# All routes in `event_router` will be prefixed with /api
# So, for example, a route `/` in routes.py becomes `/api/events/`
app.include_router(event_router, prefix="/api")