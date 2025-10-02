# File: routes.py
# Description: FastAPI routes for the construction company API.

from fastapi import APIRouter, HTTPException, status, Query, Path, Depends
from fastapi.security import APIKeyHeader
from typing import List, Optional

# This code assumes a 'models.py' file exists in the same directory with the following Pydantic models:
#
# from pydantic import BaseModel, EmailStr
#
# class Project(BaseModel):
#     id: int
#     name: str
#     category: str
#     description: str
#     image_url: str
#
# class ContactForm(BaseModel):
#     name: str
#     email: EmailStr
#     message: str
#
# class MessageResponse(BaseModel):
#     message: str
#
from .models import Project, ContactForm, MessageResponse


# --- In-Memory Database Simulation ---

# Sample data for construction projects
db_projects = [
    Project(
        id=1,
        name="Downtown High-Rise",
        category="Commercial",
        description="A 50-story mixed-use skyscraper in the heart of the city.",
        image_url="/images/high-rise.jpg",
    ),
    Project(
        id=2,
        name="Suburban Family Homes",
        category="Residential",
        description="A community of 100 modern single-family homes.",
        image_url="/images/suburban-homes.jpg",
    ),
    Project(
        id=3,
        name="Coastal Bridge Reconstruction",
        category="Infrastructure",
        description="Reconstruction of the main coastal bridge to improve traffic flow and safety.",
        image_url="/images/bridge.jpg",
    ),
    Project(
        id=4,
        name="Green Valley Apartments",
        category="Residential",
        description="Eco-friendly apartment complex with 200 units and green spaces.",
        image_url="/images/apartments.jpg",
    ),
]


# --- API Router Setup ---

router = APIRouter(prefix="/api")


# --- Authentication Simulation ---

# Define a static API key for demonstration purposes.
# In a real application, this should be stored securely (e.g., environment variables).
API_KEY = "your-secret-api-key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Dependency to validate the API key from the 'X-API-Key' header."""
    if api_key == API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )


# --- API Endpoints ---

@router.get(
    "/projects",
    response_model=List[Project],
    summary="Get a list of all projects",
    description="Retrieves a list of all construction projects. Can be filtered by category.",
    tags=["Projects"],
)
async def get_projects(
    category: Optional[str] = Query(
        None,
        description="Filter projects by category (e.g., 'Residential', 'Commercial').",
        min_length=3,
        max_length=50,
    )
):
    """
    Retrieves a list of construction projects.
    - If a **category** query parameter is provided, it filters the projects.
    - Otherwise, it returns all projects.
    """
    if category:
        filtered_projects = [
            p for p in db_projects if p.category.lower() == category.lower()
        ]
        return filtered_projects
    return db_projects


@router.get(
    "/projects/{id}",
    response_model=Project,
    summary="Get a single project by ID",
    description="Retrieves detailed information for a single project by its unique ID.",
    tags=["Projects"],
    responses={
        404: {"description": "Project not found", "model": MessageResponse},
    },
)
async def get_project_by_id(
    id: int = Path(..., description="The unique identifier of the project.", gt=0)
):
    """
    Retrieves a single project by its ID.
    - Raises a **404 Not Found** error if the project with the specified ID does not exist.
    """
    project = next((p for p in db_projects if p.id == id), None)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {id} not found",
        )
    return project


@router.post(
    "/contact",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a contact form",
    description="Accepts contact form submissions, validates the data, and simulates sending an email. Requires a valid API key in the 'X-API-Key' header.",
    tags=["Contact"],
    responses={
        400: {"description": "Invalid data provided", "model": MessageResponse},
        401: {"description": "Unauthorized - Invalid or missing API Key", "model": MessageResponse},
        422: {"description": "Validation Error"},
    },
)
async def submit_contact_form(
    form_data: ContactForm,
    # This dependency enforces that a valid API key must be provided.
    api_key: str = Depends(get_api_key)
):
    """
    Handles contact form submissions.
    - **Authentication**: Requires a valid `X-API-Key` header.
    - **Validation**: Validates the incoming data against the `ContactForm` model.
      FastAPI handles 422 Unprocessable Entity for Pydantic validation errors automatically.
    - **Action**: Simulates sending an email notification.
    - **Response**: Returns a success message.
    """
    # Example of additional server-side validation beyond Pydantic's scope
    if not form_data.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message field cannot be empty or just whitespace.",
        )

    # Simulate sending an email in a real application
    print("--- New Contact Form Submission ---")
    print(f"Name: {form_data.name}")
    print(f"Email: {form_data.email}")
    print(f"Message: {form_data.message}")
    print("-----------------------------------")
    # In a real application, you would integrate an email service here,
    # e.g., using libraries like 'fastapi-mail' or 'smtplib'.

    return {"message": "Thank you for your message. We will get back to you shortly."}