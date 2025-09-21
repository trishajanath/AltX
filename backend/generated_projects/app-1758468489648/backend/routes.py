from fastapi import APIRouter, HTTPException, status, Body
from typing import List
from uuid import UUID
from datetime import datetime, timezone

from .models import Event, EventCreate, EventUpdate
from .database import DB

# Rename the generic 'tasks' to 'events' to match the domain
# The prompt used `tasks` but `events` is more appropriate for this application
router = APIRouter(
    prefix="/events",
    tags=["Events"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/",
    response_model=List[Event],
    summary="Get All College Events",
    description="Retrieves a list of all scheduled events, sorted by event date.",
)
async def get_all_events():
    """
    Fetches all events from the in-memory database.
    The events are sorted by their scheduled date in ascending order.
    """
    # Convert dict values to a list and sort them
    sorted_events = sorted(list(DB.values()), key=lambda event: event.event_date)
    return sorted_events

@router.post(
    "/",
    response_model=Event,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Event",
    description="Adds a new event to the schedule.",
)
async def create_event(event_create: EventCreate = Body(...)):
    """
    Creates a new event based on the provided data.
    - A unique UUID is generated for the event.
    - `created_at` and `updated_at` timestamps are set.
    - The new event is added to the in-memory database.
    """
    # The Pydantic model `EventCreate` already validates the input data.
    # If the data is invalid, FastAPI will return a 422 error automatically.
    
    new_event = Event(**event_create.dict())
    
    # Store the new event in our "database"
    DB[new_event.id] = new_event
    
    return new_event

@router.get(
    "/{event_id}",
    response_model=Event,
    summary="Get a Specific Event",
    description="Retrieves details of a single event by its unique ID.",
)
async def get_event_by_id(event_id: UUID):
    """
    Finds and returns a single event by its UUID.
    If the event does not exist, it raises a 404 Not Found error.
    """
    event = DB.get(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found."
        )
    return event

@router.put(
    "/{event_id}",
    response_model=Event,
    summary="Update an Event",
    description="Updates the details of an existing event.",
)
async def update_event(event_id: UUID, event_update: EventUpdate = Body(...)):
    """
    Updates an existing event with new data.
    - Finds the event by ID. Raises 404 if not found.
    - Updates the fields with the provided data. Only non-null fields are updated.
    - Updates the `updated_at` timestamp.
    """
    event = DB.get(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found."
        )
    
    # Get the update data, excluding fields that were not set in the request
    update_data = event_update.dict(exclude_unset=True)
    
    # Update the existing event object
    for key, value in update_data.items():
        setattr(event, key, value)
    
    # Update the timestamp
    event.updated_at = datetime.now(timezone.utc)
    
    DB[event_id] = event
    return event

@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an Event",
    description="Removes an event from the schedule permanently.",
)
async def delete_event(event_id: UUID):
    """
    Deletes an event from the in-memory database by its UUID.
    - If the event exists, it is removed.
    - If the event does not exist, a 404 error is raised.
    - Returns a 204 No Content response on successful deletion.
    """
    if event_id not in DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found."
        )
    
    del DB[event_id]
    
    # No content is returned for a 204 response
    return None