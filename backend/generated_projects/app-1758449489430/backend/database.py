import uuid
from datetime import datetime, timedelta
from typing import List, Dict
from .models import Event, EventCategory

# =============================================================================
# In-Memory Database
# =============================================================================
# This section simulates a database using a Python dictionary.
# In a real-world application, this would be replaced with a connection
# to a persistent database like PostgreSQL, MySQL, or a NoSQL DB.
# The data is volatile and will be reset every time the application restarts.
# =============================================================================

DB: Dict[uuid.UUID, Event] = {}

def initialize_mock_data():
    """
    Populates the in-memory database with some realistic sample data.
    This is useful for development and testing the API endpoints without
    needing to manually create data first.
    """
    mock_events = [
        Event(
            id=uuid.uuid4(),
            title="Annual Tech Symposium 2024",
            description="A gathering of tech enthusiasts and professionals to discuss the latest trends in AI and Machine Learning.",
            event_datetime=datetime.now() + timedelta(days=10),
            location="Main Auditorium",
            category=EventCategory.ACADEMIC,
            organizer="Computer Science Club"
        ),
        Event(
            id=uuid.uuid4(),
            title="Inter-College Football Championship",
            description="The final match of the annual inter-college football tournament. Go team!",
            event_datetime=datetime.now() + timedelta(days=5, hours=4),
            location="University Sports Ground",
            category=EventCategory.SPORTS,
            organizer="Sports Committee"
        ),
        Event(
            id=uuid.uuid4(),
            title="Cultural Night: A 'Melody of Cultures'",
            description="An evening showcasing diverse cultural performances including music, dance, and drama.",
            event_datetime=datetime.now() + timedelta(days=20),
            location="Open Air Theatre",
            category=EventCategory.CULTURAL,
            organizer="Arts & Culture Society"
        ),
        Event(
            id=uuid.uuid4(),
            title="Python for Data Science Workshop",
            description="A hands-on workshop for beginners to learn the fundamentals of Python for data analysis.",
            event_datetime=datetime.now() + timedelta(days=3),
            location="Room 301, Engineering Block",
            category=EventCategory.WORKSHOP,
            organizer="Data Science Enthusiasts"
        ),
        Event(
            id=uuid.uuid4(),
            title="Spring Semester Welcome Mixer",
            description="A social event for new and returning students to connect and kick off the new semester.",
            event_datetime=datetime.now() + timedelta(days=2),
            location="Student Union Hall",
            category=EventCategory.SOCIAL,
            organizer="Student Government Association"
        )
    ]
    
    for event in mock_events:
        DB[event.id] = event

# Initialize the data when the module is loaded.
initialize_mock_data()