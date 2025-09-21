# database.py
# This file simulates a database for the purpose of this demonstration.
# In a production environment, this would be replaced with actual database
# connection logic (e.g., using SQLAlchemy with PostgreSQL or SQLite).

import uuid
from typing import Dict
from models import Student, AttendanceStatus

#  In-Memory Data Store 
# This dictionary acts as a simple, non-persistent database.
# The keys are student UUIDs and the values are Student model instances.
# Data will be lost when the server restarts.

STUDENT_ROSTER: Dict[uuid.UUID, Student] = {}

#  Realistic Sample Data 
# Pre-populating the 'database' with some sample data makes it easier to
# test and develop the frontend without having to add data manually each time.

def populate_initial_data():
    """
    Clears and populates the in-memory roster with sample student data.
    """
    global STUDENT_ROSTER
    STUDENT_ROSTER.clear()

    sample_students = [
        Student(id=uuid.uuid4(), full_name="Alice Johnson", attendance_status=AttendanceStatus.PRESENT),
        Student(id=uuid.uuid4(), full_name="Bob Williams", attendance_status=AttendanceStatus.ABSENT),
        Student(id=uuid.uuid4(), full_name="Charlie Brown", attendance_status=AttendanceStatus.UNMARKED),
        Student(id=uuid.uuid4(), full_name="Diana Prince", attendance_status=AttendanceStatus.PRESENT),
    ]

    for student in sample_students:
        STUDENT_ROSTER[student.id] = student

# Initialize the roster with sample data when the application starts
populate_initial_data()

print(f"
✅ In-memory database initialized with {len(STUDENT_ROSTER)} sample students.")