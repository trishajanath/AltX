import uuid
from typing import List, Optional
from fastapi import APIRouter, status, HTTPException

from . import models
from .database import DB

# Create an APIRouter instance. All routes defined in this file will be
# added to this router, which can then be included in the main FastAPI app.
router = APIRouter()

@router.get(
    "/events",
    response_model=List[models.Event],
    summary="Get a list of all college events",
    description="Returns a list of all events, optionally filtered by category. Events are sorted by date."
)
async def get_all_events(category: Optional[models.EventCategory] = None):
    """
    Retrieves all events from the in-memory database.

    - Business Logic:
      - If a 'category' query parameter is provided, the list is filtered to include
        only events of that specific category.
      - The final list of events is sorted by their `event_datetime` in ascending order,
        so upcoming events appear first.
    """
    events = list(DB.values())
    
    if category:
        events = [event for event in events if event.category == category]
        
    # Sort events by date, upcoming first
    events.sort(key=lambda x: x.event_datetime)
    
    return events

@router.post(
    "/events",
    response_model=models.Event,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new college event",
    description="Adds a new event to the college's event list."
)
async def create_event(event_in: models.EventCreate):
    """
    Creates a new event and adds it to the in-memory database.

    - Business Logic:
      - A new unique identifier (UUID) is generated for the event.
      - The input data from `EventCreate` model is combined with the new ID
        to create a full `Event` object.
      - The new event is stored in the in-memory dictionary.
      - The newly created event object is returned to the client.
    """
    new_id = uuid.uuid4()
    
    # Create the full Event model instance
    new_event = models.Event(
        id=new_id,
        **event_in.model_dump() # Unpack fields from the input model
    )
    
    DB[new_id] = new_event
    return new_event

@router.get(
    "/events/{event_id}",
    response_model=models.Event,
    summary="Get a single event by ID",
    description="Retrieves the details of a specific event using its unique ID.",
    responses={404: {"description": "Event not found"}}
)
async def get_event_by_id(event_id: uuid.UUID):
    """
    Retrieves a single event by its UUID.

    - Error Handling:
      - If an event with the given `event_id` is not found in the database,
        an HTTP 404 Not Found exception is raised, providing a clear
        error message to the client.
    """
    event = DB.get(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found."
        )
    return event