import datetime
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# --- Pydantic Models ---
# In a real application, these would be in a separate `models.py` file.
# from .models import User, UserUpdate, Event, RSVP, Message

class User(BaseModel):
    id: int
    email: str
    chosen_name: Optional[str] = None
    pronouns: Optional[str] = None

class UserUpdate(BaseModel):
    chosen_name: Optional[str] = Field(None, description="User's preferred name")
    pronouns: Optional[str] = Field(None, description="User's preferred pronouns (e.g., she/her, they/them)")

class Event(BaseModel):
    id: int
    title: str
    description: str
    start_date: datetime.date
    end_date: datetime.date
    tags: List[str] = []

class RSVP(BaseModel):
    event_id: int
    user_id: int
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class Message(BaseModel):
    message: str

# --- In-Memory Storage (acting as a database) ---

db_users = {
    1: User(id=1, email="user@example.com", chosen_name="Alex", pronouns="they/them"),
    2: User(id=2, email="jane.doe@example.com", chosen_name="Jane", pronouns="she/her"),
}

db_events = [
    Event(
        id=101,
        title="Community Picnic",
        description="A fun picnic for everyone in the community.",
        start_date=datetime.date(2024, 8, 15),
        end_date=datetime.date(2024, 8, 15),
        tags=["Social", "Outdoor"]
    ),
    Event(
        id=102,
        title="Tech Meetup: Intro to FastAPI",
        description="Learn the basics of building APIs with FastAPI.",
        start_date=datetime.date(2024, 8, 20),
        end_date=datetime.date(2024, 8, 20),
        tags=["Tech", "Workshop"]
    ),
    Event(
        id=103,
        title="Weekend Music Festival",
        description="Three days of live music and fun.",
        start_date=datetime.date(2024, 9, 5),
        end_date=datetime.date(2024, 9, 7),
        tags=["Social", "Music"]
    ),
]

db_rsvps: List[RSVP] = []


# --- Dependency for Authentication Simulation ---

# In a real app, this would involve decoding a JWT token or checking a session.
# For this example, we'll just hardcode a user to simulate authentication.
async def get_current_user() -> User:
    user = db_users.get(1)
    if not user:
        # This case is unlikely with hardcoded data but good practice.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# --- APIRouter ---

router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"],
)


# --- User Endpoints ---

@router.get(
    "/users/me",
    response_model=User,
    summary="Get current user profile",
    description="Retrieve the profile of the currently authenticated user, including chosen name and pronouns."
)
async def get_user_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the profile for the currently authenticated user.
    """
    return current_user


@router.put(
    "/users/me",
    response_model=User,
    summary="Update current user profile",
    description="Update the authenticated user's profile information, primarily for changing chosen name or pronouns."
)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Updates the authenticated user's profile.
    Only non-null fields in the request body will be updated.
    """
    # Retrieve the user from the "database" to ensure we're modifying the persistent record
    db_user = db_users.get(current_user.id)
    if not db_user:
        # This should not happen if the user is authenticated, but it's a good safeguard.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    return db_user


# --- Event Endpoints ---

@router.get(
    "/events",
    response_model=List[Event],
    summary="Get a list of all events",
    description="Get a list of all events. Supports query parameters for filtering by date range and tags."
)
async def get_events(
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    tag: Optional[str] = None
):
    """
    Retrieves a list of events, with optional filtering:
    - **start_date**: The earliest date an event can start.
    - **end_date**: The latest date an event can end.
    - **tag**: A tag that events must have.
    """
    filtered_events = db_events

    if start_date:
        filtered_events = [event for event in filtered_events if event.end_date >= start_date]

    if end_date:
        filtered_events = [event for event in filtered_events if event.start_date <= end_date]

    if tag:
        filtered_events = [event for event in filtered_events if tag in event.tags]

    return filtered_events


@router.post(
    "/events/{event_id}/rsvp",
    response_model=Message,
    status_code=status.HTTP_201_CREATED,
    summary="RSVP for an event",
    description="Allows an authenticated user to RSVP for a specific event."
)
async def rsvp_for_event(
    event_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Creates an RSVP for the specified event for the current user.
    """
    # Check if the event exists
    event = next((event for event in db_events if event.id == event_id), None)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Check if the user has already RSVP'd
    existing_rsvp = next((rsvp for rsvp in db_rsvps if rsvp.event_id == event_id and rsvp.user_id == current_user.id), None)
    if existing_rsvp:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already RSVP'd to this event")

    # Create and store the new RSVP
    new_rsvp = RSVP(event_id=event_id, user_id=current_user.id)
    db_rsvps.append(new_rsvp)

    return {"message": f"Successfully RSVP'd to event '{event.title}'"}