# routes.py
# This file contains the API endpoints (routes) related to student management.
# It uses an APIRouter to group related endpoints, which helps in organizing
# the application as it grows.

from fastapi import APIRouter, HTTPException, status, Response
from typing import List
import uuid

from models import Student, StudentCreate, AttendanceUpdate, AttendanceStatus
from database import STUDENT_ROSTER

# Create an API router for student-related endpoints
student_router = APIRouter()

#  Business Logic Helper Functions 

def find_student_by_id(student_id: uuid.UUID) -> Student:
    """Helper function to find a student in the in-memory roster."""
    student = STUDENT_ROSTER.get(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found."
        )
    return student

#  API Endpoints 

@student_router.get("/", response_model=List[Student], status_code=status.HTTP_200_OK)
async def get_all_students():
    """
    Retrieve the entire list of students from the roster.
    This endpoint is useful for the frontend to display all students.
    """
    return list(STUDENT_ROSTER.values())

@student_router.post("/", response_model=Student, status_code=status.HTTP_201_CREATED)
async def add_student(student_data: StudentCreate):
    """
    Add a new student to the roster.
    The student's attendance status will default to 'unmarked'.
    A unique UUID is generated for the new student.
    """
    new_id = uuid.uuid4()
    new_student = Student(
        id=new_id,
        full_name=student_data.full_name,
        attendance_status=AttendanceStatus.UNMARKED
    )
    STUDENT_ROSTER[new_id] = new_student
    return new_student

@student_router.get("/{student_id}", response_model=Student, status_code=status.HTTP_200_OK)
async def get_student_by_id(student_id: uuid.UUID):
    """
    Retrieve details for a single student by their unique ID.
    Raises a 404 error if the student is not found.
    """
    return find_student_by_id(student_id)

@student_router.patch("/{student_id}/attendance", response_model=Student, status_code=status.HTTP_200_OK)
async def update_student_attendance(student_id: uuid.UUID, attendance_data: AttendanceUpdate):
    """
    Update the attendance status of a specific student.
    This endpoint is designed for marking a student as present or absent.
    Raises a 404 error if the student is not found.
    """
    student_to_update = find_student_by_id(student_id)
    student_to_update.attendance_status = attendance_data.status
    STUDENT_ROSTER[student_id] = student_to_update
    return student_to_update

@student_router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student(student_id: uuid.UUID):
    """
    Remove a student from the roster by their unique ID.
    This is a destructive action. Raises a 404 if the student doesn't exist.
    Returns a 204 No Content response on successful deletion.
    """
    find_student_by_id(student_id)  # Check if student exists
    del STUDENT_ROSTER[student_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)