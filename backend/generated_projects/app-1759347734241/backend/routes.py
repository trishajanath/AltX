from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import get_db

api_router = APIRouter()

@api_router.post("/events/", response_model=schemas.Event, status_code=201)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Create a new college event.
    """
    if event.end_date  {
  try {
    const response = await apiClient.get('/events/');
    return response.data;
  } catch (error) {
    console.error('Error fetching events:', error);
    throw error;
  }
};

export const createEvent = async (eventData) => {
  try {
    const response = await apiClient.post('/events/', eventData);
    return response.data;
  } catch (error) {
    console.error('Error creating event:', error);
    throw error;
  }
};