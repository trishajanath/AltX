Here's the complete `main.py` file for your FastAPI todo application, incorporating all specified features and requirements.

This single file includes configuration, database setup (using SQLModel for simplicity with SQLite), API routes, CORS, error handling, and lifecycle events. In a larger project, you would typically split `config`, `models`, `database`, and `routes` into separate Python files for better organization.

**Project Structure (Conceptual for a larger app):**

```
todo-service/
├── .env                  # Environment variables (e.g., DATABASE_URL, CORS_ORIGINS)
├── main.py               # Application entry point (provided below)
├── config.py             # (Optional) For Pydantic BaseSettings
├── database.py           # (Optional) For database engine, session, and setup
├── models.py             # (Optional) For SQLModel definitions
└── routes.py             # (Optional) For API endpoint definitions
```

**`main.py`**

```python
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, Request, status, Depends, HTTPException, APIRouter
from fastapi.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Pydantic-settings for configuration management
from pydantic_settings import BaseSettings, SettingsConfigDict

# SQLModel for database ORM (built on SQLAlchemy and Pydantic)
from sqlmodel import create_engine, Field, Session, SQLModel, select

# --- 1. Configuration (Production-ready with Pydantic-settings) ---
class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or a .env file.
    """
    APP_NAME: str = "Todo Service API"
    DATABASE_URL: str = "sqlite:///./database.db"  # SQLite database file
    
    # For production, define specific origins (e.g., ["https://yourfrontend.com"])
    # For development, allow localhost or specific development origins.
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000", "http://localhost:8000"]
    
    DEBUG_MODE: bool = False # Set to True for detailed logs and Swagger/Redoc UI

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()

# --- 2. Logging Configuration ---
logging.basicConfig(level=logging.INFO if not settings.DEBUG_MODE else logging.DEBUG)
logger = logging.getLogger(__name__)

# --- 3. Database Setup (SQLModel - integrates models and DB access) ---

# Define SQLModel models for Todo tasks
class TodoBase(SQLModel):
    """Base model for Todo, defining common fields."""
    title: str = Field(index=True, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)

class Todo(TodoBase, table=True):
    """Database model for a Todo item."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # You can add custom validators or methods here if needed
    def __repr__(self):
        return f"Todo(id={self.id}, title='{self.title}', completed={self.completed})"

# Pydantic models for request/response bodies (schema validation)
class TodoCreate(TodoBase):
    """Model for creating a new Todo item (inherits from TodoBase)."""
    pass

class TodoUpdate(SQLModel):
    """Model for updating an existing Todo item (all fields optional)."""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

# Database engine and session management
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG_MODE)

def create_db_and_tables():
    """Creates all defined database tables."""
    logger.info("Attempting to create database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created (if they didn't exist).")

def get_session() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session.
    It yields a session and ensures it's closed afterwards,
    making it suitable for FastAPI's dependency injection.
    """
    with Session(engine) as session:
        yield session

# --- 4. API Routes (Encapsulated in an APIRouter) ---
api_router = APIRouter()

@api_router.post("/tasks/", response_model=Todo, status_code=status.HTTP_201_CREATED, summary="Add a new task")
def create_task(
    task: TodoCreate, 
    session: Session = Depends(get_session)
):
    """
    **Add Tasks**: Create a new todo task.
    - **title**: The title of the task (required).
    - **description**: An optional description for the task.
    - **completed**: Initial status, defaults to `false`.
    """
    db_task = Todo.model_validate(task) # Convert TodoCreate to Todo model
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    logger.info(f"Task created: {db_task.id} - '{db_task.title}'")
    return db_task

@api_router.get("/tasks/", response_model=List[Todo], summary="Filter and list tasks")
def get_tasks(
    completed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    **Filter Tasks**: Retrieve a list of todo tasks.
    - **completed**: Optional filter to get only completed (`true`) or incomplete (`false`) tasks.
    - **skip**: Number of items to skip (for pagination).
    - **limit**: Maximum number of items to return (for pagination).
    """
    query = select(Todo)
    if completed is not None:
        query = query.where(Todo.completed == completed)
    
    tasks = session.exec(query.offset(skip).limit(limit)).all()
    logger.debug(f"Retrieved {len(tasks)} tasks (completed={completed}, skip={skip}, limit={limit}).")
    return tasks

@api_router.get("/tasks/{task_id}", response_model=Todo, summary="Get a task by ID")
def get_task(
    task_id: int, 
    session: Session = Depends(get_session)
):
    """
    Retrieve a single todo task by its ID.
    """
    task = session.get(Todo, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    return task

@api_router.put("/tasks/{task_id}", response_model=Todo, summary="Update an existing task")
def update_task(
    task_id: int, 
    task_update: TodoUpdate, 
    session: Session = Depends(get_session)
):
    """
    Update an existing todo task by ID.
    Only provided fields will be updated.
    """
    db_task = session.get(Todo, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")

    # Update task fields from the Pydantic model (excluding unset fields)
    task_data = task_update.model_dump(exclude_unset=True)
    for key, value in task_data.items():
        setattr(db_task, key, value)
    
    db_task.updated_at = datetime.utcnow() # Always update timestamp on modification

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    logger.info(f"Task updated: {db_task.id} - '{db_task.title}'")
    return db_task

@api_router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task")
def delete_task(
    task_id: int, 
    session: Session = Depends(get_session)
):
    """
    **Delete Tasks**: Delete a todo task by its ID.
    """
    task = session.get(Todo, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    session.delete(task)
    session.commit()
    logger.info(f"Task deleted: {task_id}")
    return {"ok": True} # HTTP 204 No Content typically doesn't return a body

@api_router.patch("/tasks/{task_id}/complete", response_model=Todo, summary="Mark task complete")
def mark_task_complete(
    task_id: int, 
    session: Session = Depends(get_session)
):
    """
    **Mark Complete**: Mark a todo task as complete.
    """
    db_task = session.get(Todo, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    db_task.completed = True
    db_task.updated_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    logger.info(f"Task {task_id} marked complete.")
    return db_task

@api_router.patch("/tasks/{task_id}/uncomplete", response_model=Todo, summary="Mark task incomplete")
def mark_task_uncomplete(
    task_id: int, 
    session: Session = Depends(get_session)
):
    """
    Mark a todo task as incomplete.
    """
    db_task = session.get(Todo, task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found")
    db_task.completed = False
    db_task.updated_at = datetime.utcnow()
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    logger.info(f"Task {task_id} marked uncomplete.")
    return db_task

# --- 5. FastAPI Application Lifecycle and Configuration ---

# Async context manager for application startup/shutdown events (FastAPI 0.100+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    On startup, it initializes the database tables.
    """
    logger.info(f"Starting up {settings.APP_NAME} (Debug Mode: {settings.DEBUG_MODE})...")
    create_db_and_tables() # Create DB tables on startup
    logger.info("Application startup complete.")
    yield # Application runs
    logger.info("Shutting down application.")

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="A simple Todo web service with features: Add tasks, Mark complete, Delete tasks, Filter tasks.",
    docs_url="/docs" if settings.DEBUG_MODE else None,       # Disable Swagger UI in production
    redoc_url="/redoc" if settings.DEBUG_MODE else None,     # Disable ReDoc UI in production
    lifespan=lifespan,
)

# --- 6. CORS Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,             # Allow cookies to be sent with cross-origin requests
    allow_methods=["*"],                # Allow all HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS)
    allow_headers=["*"],                # Allow all headers
)

# --- 7. Health Check Endpoint ---
@app.get("/health", response_model=Dict[str, str], summary="Health Check")
async def health_check():
    """
    **Health Check Endpoint**:
    Checks the health of the service.
    Returns a status 'ok' if the service is running.
    """
    return {"status": "ok", "message": "Todo Service is healthy"}

# --- 8. Standard Error Handling ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handles FastAPI's HTTPException (e.g., 404 Not Found, 422 Unprocessable Entity)
    and returns a structured JSON response.
    """
    logger.warning(f"HTTP Error {exc.status_code} for {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handles all other unexpected exceptions (e.g., database connection issues,
    coding errors) and returns a generic 500 error.
    """
    logger.exception(f"Unhandled exception for {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred."},
    )

# --- 9. Route Module Integration ---
# Prefix all API routes with /api/v1 for versioning
app.include_router(api_router, prefix="/api/v1")

# --- How to Run This Application ---
# 1. Save this code as `main.py`.
# 2. (Optional) Create a `.env` file in the same directory:
#    DATABASE_URL="sqlite:///./my_custom_todo_db.db"
#    CORS_ORIGINS='["http://localhost:3000", "https://yourfrontend.com"]'
#    DEBUG_MODE=True
# 3. Install dependencies:
#    pip install fastapi "uvicorn[standard]" sqlmodel pydantic-settings
# 4. Run the application using Uvicorn:
#    uvicorn main:app --reload --port 8000
#
# Then, access the API:
# - Documentation (if DEBUG_MODE=True): http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
# - API Endpoints: http://localhost:8000/api/v1/tasks/