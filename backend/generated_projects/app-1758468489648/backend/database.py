from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from .models import Event

# This file simulates a database using an in-memory dictionary.
# In a real-world application, this would be replaced with a database connection
# (e.g., PostgreSQL with SQLAlchemy or an ORM like Tortoise-ORM).

# Using a dictionary for O(1) lookups by ID.
DB: Dict[UUID, Event] = {}

def initialize_mock_data():
    """
    Clears the existing in-memory DB and populates it with some realistic
    sample data for development and testing.
    """
    DB.clear()
    
    now = datetime.now(timezone.utc)
    
    mock_events = [
        Event(
            id=uuid4(),
            title="Fall Semester Welcome Social",
            description="Meet new friends and enjoy free pizza and music at the main quad.",
            event_date=now + timedelta(days=10),
            location="Main Quad",
            organizer="Student Government Association",
            category="Social"
        ),
        Event(
            id=uuid4(),
            title="Data Science with Python Workshop",
            description="A hands-on workshop covering pandas, numpy, and scikit-learn. Laptops required.",
            event_date=now + timedelta(days=25, hours=4),
            location="Library, Room 202",
            organizer="Tech Club",
            category="Workshop"
        ),
        Event(
            id=uuid4(),
            title="Annual Tech Career Fair",
            description="Connect with top tech companies looking to hire interns and full-time graduates.",
            event_date=now + timedelta(days=45, hours=2),
            location="University Gymnasium",
            organizer="Career Services",
            category="Career Fair"
        ),
        Event(
            id=uuid4(),
            title="Varsity Basketball vs. Rival University",
            description="Come support the home team in the biggest game of the season!",
            event_date=now + timedelta(days=18, hours=19),
            location="Sports Arena",
            organizer="Athletics Department",
            category="Sports"
        ),
    ]
    
    for event in mock_events:
        DB[event.id] = event

# Initialize with mock data when the application starts
initialize_mock_data()