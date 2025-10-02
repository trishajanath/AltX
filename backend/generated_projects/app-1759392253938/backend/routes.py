# In a real application, these models would be in a separate 'models.py' file.
# For this self-contained example, they are defined here to fulfill the request.
from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime, timezone

# --- Pydantic Models (simulating import from .models) ---

class Project(BaseModel):
    """Model for a project to be displayed on the portfolio."""
    id: int
    name: str
    description: str
    technologies: List[str]
    image_url: str
    project_url: str

class ContactMessage(BaseModel):
    """Model for an incoming contact form submission."""
    name: str
    email: EmailStr
    message: str

class ContactMessageInDB(ContactMessage):
    """Model for a contact message as it is stored in our 'database'."""
    id: int
    timestamp: datetime


# --- FastAPI Imports and Router Setup ---

from fastapi import APIRouter, HTTPException, status

# All routes in this file will be prefixed with /api/v1
router = APIRouter(prefix="/api/v1")


# --- In-Memory Storage (simulating a database) ---

db_projects: List[Project] = [
    Project(
        id=1,
        name="AI-Powered Personal Finance Tracker",
        description="A web application that uses machine learning to categorize expenses and provide budget insights.",
        technologies=["Python", "FastAPI", "React", "Scikit-learn", "PostgreSQL"],
        image_url="/images/project-finance.jpg",
        project_url="https://github.com/user/finance-tracker"
    ),
    Project(
        id=2,
        name="Real-time Collaborative Whiteboard",
        description="A collaborative tool for teams to brainstorm ideas in real-time using WebSockets.",
        technologies=["Node.js", "Express", "Socket.IO", "Vue.js"],
        image_url="/images/project-whiteboard.jpg",
        project_url="https://github.com/user/whiteboard-app"
    ),
    Project(
        id=3,
        name="E-commerce Product Recommendation API",
        description="A RESTful API that provides personalized product recommendations based on user behavior.",
        technologies=["Python", "Flask", "Pandas", "Docker", "Redis"],
        image_url="/images/project-ecommerce.jpg",
        project_url="https://github.com/user/recommendation-api"
    )
]

db_contact_messages: List[ContactMessageInDB] = []


# --- API Endpoints (CRUD Operations) ---

@router.get(
    "/projects",
    response_model=List[Project],
    summary="Get All Projects",
    description="Retrieve a list of all projects to display on the portfolio."
)
async def get_all_projects():
    """
    Provides a list of all available projects.
    """
    return db_projects


@router.get(
    "/projects/{project_id}",
    response_model=Project,
    summary="Get a Specific Project",
    description="Fetch detailed information for a specific project by its ID."
)
async def get_project_by_id(project_id: int):
    """
    Fetches a single project by its unique integer ID.

    - **project_id**: The ID of the project to retrieve.
    """
    # Search for the project in our in-memory list
    project = next((p for p in db_projects if p.id == project_id), None)

    if project is None:
        # If the project is not found, raise a 404 Not Found error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )
    return project


@router.post(
    "/contact",
    response_model=ContactMessageInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a Contact Form",
    description="Submit a message from the contact form and store it."
)
async def submit_contact_form(message: ContactMessage):
    """
    Accepts a contact form submission and stores it in-memory.

    - **name**: The name of the person submitting the form.
    - **email**: The email address of the person.
    - **message**: The content of the message.
    """
    # Create a new ID for the message (simple increment for this example)
    new_id = len(db_contact_messages) + 1

    # Create a new message object with server-side data (ID, timestamp)
    new_message = ContactMessageInDB(
        id=new_id,
        timestamp=datetime.now(timezone.utc),
        **message.model_dump()
    )

    # "Save" the message to our in-memory list
    db_contact_messages.append(new_message)

    # Return the created message, including the server-generated ID and timestamp
    return new_message