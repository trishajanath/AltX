from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

# --- Models (Normally in a separate 'models.py' file) ---

class Role(str, Enum):
    """Enumeration for user roles."""
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"

class User(BaseModel):
    """Represents a user in the system (internal model)."""
    id: int
    email: EmailStr
    hashed_password: str
    role: Role
    organization_id: int

class UserInRoster(BaseModel):
    """Represents a user's public information for an event roster."""
    id: int
    email: EmailStr
    role: Role

class Geofence(BaseModel):
    """Represents geofencing data for an event."""
    latitude: float
    longitude: float
    radius_meters: int

class EventCreate(BaseModel):
    """Model for creating a new event."""
    name: str = Field(..., min_length=3, max_length=100)
    start_time: datetime
    end_time: datetime
    geofence_data: Geofence
    assigned_user_ids: List[int] = []

class Event(EventCreate):
    """Represents a full event object in the system."""
    id: int
    organization_id: int

class Token(BaseModel):
    """Model for the JWT access token response."""
    access_token: str
    token_type: str

# --- In-Memory Storage (Simulating a database) ---

# Note: Passwords should be properly hashed in a real application (e.g., with passlib)
db_users: Dict[int, User] = {
    1: User(id=1, email="admin@org1.com", hashed_password="password_admin", role=Role.ADMIN, organization_id=101),
    2: User(id=2, email="manager@org1.com", hashed_password="password_manager", role=Role.MANAGER, organization_id=101),
    3: User(id=3, email="user1@org1.com", hashed_password="password_user1", role=Role.USER, organization_id=101),
    4: User(id=4, email="user2@org2.com", hashed_password="password_user2", role=Role.USER, organization_id=102),
}

db_events: Dict[int, Event] = {
    10: Event(
        id=10,
        name="Weekly Team Sync",
        start_time=datetime.now() - timedelta(days=1),
        end_time=datetime.now() - timedelta(days=1, hours=-1),
        organization_id=101,
        geofence_data=Geofence(latitude=34.0522, longitude=-118.2437, radius_meters=100),
        assigned_user_ids=[1, 2, 3]
    ),
    11: Event(
        id=11,
        name="Project Kickoff",
        start_time=datetime.now() + timedelta(days=2),
        end_time=datetime.now() + timedelta(days=2, hours=-2),
        organization_id=101,
        geofence_data=Geofence(latitude=34.0522, longitude=-118.2437, radius_meters=50),
        assigned_user_ids=[2, 3]
    ),
    12: Event(
        id=12,
        name="Org 2 Meeting",
        start_time=datetime.now() + timedelta(days=3),
        end_time=datetime.now() + timedelta(days=3, hours=-1),
        organization_id=102,
        geofence_data=Geofence(latitude=40.7128, longitude=-74.0060, radius_meters=200),
        assigned_user_ids=[4]
    ),
}
# Helper for creating new event IDs
_next_event_id = 13

# --- Security and Authentication Dependencies ---

# This is a simplified security scheme. In a real app, use a proper JWT library.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_user_by_email(email: str) -> Optional[User]:
    """Helper to find a user by email from the in-memory DB."""
    for user in db_users.values():
        if user.email == email:
            return user
    return None

def fake_decode_token(token: str) -> Optional[User]:
    """A fake token decoder that extracts the email from the token."""
    # In a real app, this would verify the JWT signature, expiry, etc.
    if token.startswith("token-for-"):
        email = token.split("token-for-")[1]
        return get_user_by_email(email)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependency to get the current user from a token."""
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def require_admin_or_manager(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the user has Admin or Manager role."""
    if current_user.role not in [Role.ADMIN, Role.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin or Manager role required.",
        )
    return current_user

# --- APIRouter Setup ---

router = APIRouter(prefix="/api/v1")

# --- Route Implementations ---

@router.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login. Takes email and password, returns a JWT access token.
    Use case: Any user logging into the application.
    """
    user = get_user_by_email(form_data.username)
    # In a real app, use a secure password comparison function like passlib.verify
    if not user or user.hashed_password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In a real app, create a proper JWT with an expiry date
    access_token = f"token-for-{user.email}"
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/events", response_model=List[Event], tags=["Events"])
async def get_events(
    start_date: Optional[datetime] = Query(None, description="Filter events starting on or after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events ending on or before this date"),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a list of events for the user's organization, filterable by date range.
    Use case: Populating the EventCalendarView.
    """
    org_events = [
        event for event in db_events.values()
        if event.organization_id == current_user.organization_id
    ]

    filtered_events = org_events
    if start_date:
        filtered_events = [event for event in filtered_events if event.start_time >= start_date]
    if end_date:
        filtered_events = [event for event in filtered_events if event.end_time <= end_date]

    return sorted(filtered_events, key=lambda e: e.start_time)


@router.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED, tags=["Events"])
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(require_admin_or_manager)
):
    """
    Create a new event with geofencing data. (Admin/Manager role required).
    Use case: A manager scheduling a new weekly team meeting.
    """
    global _next_event_id
    if event_data.start_time >= event_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event end time must be after start time."
        )

    new_event = Event(
        id=_next_event_id,
        organization_id=current_user.organization_id,
        **event_data.dict()
    )
    db_events[new_event.id] = new_event
    _next_event_id += 1
    return new_event


@router.get("/events/{event_id}/roster", response_model=List[UserInRoster], tags=["Events"])
async def get_event_roster(
    event_id: int = Path(..., gt=0, description="The ID of the event to retrieve the roster for"),
    current_user: User = Depends(get_current_user)
):
    """
    Get the list of users assigned to a specific event.
    Use case: Viewing who is expected to attend a meeting.
    """
    event = db_events.get(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found."
        )

    if event.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this event's roster."
        )

    roster = []
    for user_id in event.assigned_user_ids:
        user = db_users.get(user_id)
        if user:
            roster.append(UserInRoster(id=user.id, email=user.email, role=user.role))

    return roster