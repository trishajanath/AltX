from fastapi import APIRouter, HTTPException, status
from typing import List

# In a real application, these models would be in a separate `models.py` file.
# For this example to be self-contained, we define them here and import them below.
# --- models.py ---
from pydantic import BaseModel, EmailStr, HttpUrl

class Project(BaseModel):
    id: int
    name: str
    description: str
    url: HttpUrl

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str
# --- end models.py ---

# Import models as if they were in a separate file, per requirements
from .models import Project, ContactMessage


# --- In-memory Storage ---
# This acts as a simple "database" for demonstration purposes.
db_projects: List[Project] = [
    Project(id=1, name="Project Alpha", description="A revolutionary new framework for web development.", url="https://example.com/alpha"),
    Project(id=2, name="Project Beta", description="A personal portfolio website built with modern technologies.", url="https://example.com/beta"),
    Project(id=3, name="Project Gamma", description="An e-commerce platform for selling digital goods.", url="https://example.com/gamma"),
]

db_contact_messages: List[ContactMessage] = []


# --- APIRouter Setup ---
# Create an APIRouter instance with a prefix for all routes in this file.
router = APIRouter(
    prefix="/api/v1",
    tags=["API Endpoints"]
)


# --- CRUD Operations ---

@router.get("/projects", response_model=List[Project])
async def list_projects():
    """
    List all available projects.
    This endpoint provides a complete list of projects stored in-memory.
    """
    return db_projects


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    """
    Get a single project by its unique ID.
    If the project is not found, it returns a 404 error.
    """
    # Find the project in the in-memory list
    project = next((p for p in db_projects if p.id == project_id), None)

    if project is None:
        # If not found, raise a 404 Not Found error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project


@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def submit_contact_form(message: ContactMessage):
    """
    Submit a contact form message.
    The message is validated and stored in-memory.
    """
    # In a real application, you would process this message:
    # - Save it to a persistent database
    # - Send an email notification
    # - etc.
    db_contact_messages.append(message)

    print(f"Received new contact message from {message.name} ({message.email})")
    print(f"Total messages in-memory: {len(db_contact_messages)}")

    return {"status": "success", "message": "Your message has been received."}