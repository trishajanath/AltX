# routes.py

from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime, timezone

# Import models from the sibling 'models.py' file
from .models import ContactForm, ContactResponse

# --- In-Memory Storage ---
# In a real-world application, you would use a database (e.g., PostgreSQL, MongoDB).
# For this example, we use a simple Python list to store data in memory.
# The data will be lost when the application restarts.
contact_submissions_db: List[ContactResponse] = []


# --- APIRouter ---
# Create a router with a prefix for all its routes.
# This helps in organizing the API endpoints.
router = APIRouter(
    prefix="/api/v1",
    tags=["Contact"],  # Group routes under "Contact" in the OpenAPI docs
)


# --- CRUD Endpoints ---

@router.post(
    "/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a contact form",
    description="Accepts contact form data (name, email, message) and stores it in-memory.",
)
async def submit_contact_form(form_data: ContactForm) -> ContactResponse:
    """
    Handles the submission of the contact form.

    This endpoint performs the 'Create' operation of CRUD.
    - Validates the incoming data against the `ContactForm` model.
    - Assigns a unique ID and a submission timestamp.
    - Stores the new submission in the in-memory list.
    - Returns the created submission record.

    Args:
        form_data: The contact form data from the request body, validated by FastAPI.

    Returns:
        The newly created contact submission record.

    Raises:
        HTTPException: A 500 Internal Server Error if an unexpected issue occurs.
    """
    try:
        # Generate a new ID. For this simple in-memory storage, we can use the
        # next index in the list.
        submission_id = len(contact_submissions_db) + 1

        # Create a new response object with the server-generated data
        new_submission = ContactResponse(
            id=submission_id,
            name=form_data.name,
            email=form_data.email,
            message=form_data.message,
            submitted_at=datetime.now(timezone.utc)  # Use timezone-aware datetime
        )

        # "Save" the new submission to our in-memory database
        contact_submissions_db.append(new_submission)

        return new_submission

    except Exception as e:
        # Proper error handling for any unexpected server-side issues.
        # FastAPI's Pydantic integration handles 422 Unprocessable Entity errors automatically.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred on the server: {e}"
        )

# Note: To make this file runnable, you would need:
# 1. A `models.py` file in the same directory with `ContactForm` and `ContactResponse` Pydantic models.
# 2. A `main.py` file to create the FastAPI app and include this router.
#
# Example `models.py`:
#
# from pydantic import BaseModel, EmailStr
# from datetime import datetime
#
# class ContactForm(BaseModel):
#     name: str
#     email: EmailStr
#     message: str
#
# class ContactResponse(BaseModel):
#     id: int
#     name: str
#     email: EmailStr
#     message: str
#     submitted_at: datetime
#
#
# Example `main.py`:
#
# from fastapi import FastAPI
# from . import routes
#
# app = FastAPI(
#     title="Contact Form API",
#     description="A simple API to handle contact form submissions.",
#     version="1.0.0"
# )
#
# app.include_router(routes.router)
#
# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the Contact Form API"}