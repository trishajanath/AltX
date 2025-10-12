from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date

# In a real application, the following Pydantic models would be in a separate 'models.py' file.
# from .models import Program, Faculty
# For this self-contained example, they are defined here.

from pydantic import BaseModel, EmailStr

class Program(BaseModel):
    """Represents an academic program."""
    id: int
    name: str
    department: str
    degree_level: str  # e.g., "Bachelor's", "Master's", "PhD"
    session_start_date: date
    description: str

class Faculty(BaseModel):
    """Represents a faculty member."""
    id: int
    name: str
    department: str
    title: str  # e.g., "Professor", "Associate Professor"
    email: EmailStr
    bio: str

# --- In-memory Storage (simulating a database) ---

db_programs: List[Program] = [
    Program(id=1, name="Computer Science", department="Engineering", degree_level="Bachelor's", session_start_date=date(2024, 9, 1), description="A comprehensive program on computing fundamentals."),
    Program(id=2, name="Data Science", department="Engineering", degree_level="Master's", session_start_date=date(2024, 9, 1), description="Advanced studies in data analysis, machine learning, and big data."),
    Program(id=3, name="History of Art", department="Arts & Humanities", degree_level="Bachelor's", session_start_date=date(2024, 9, 1), description="Explore the rich history of artistic expression across cultures."),
    Program(id=4, name="Business Administration", department="Business", degree_level="Master's", session_start_date=date(2025, 1, 15), description="Develop leadership and management skills for the modern business world."),
    Program(id=5, name="Quantum Physics", department="Sciences", degree_level="PhD", session_start_date=date(2024, 9, 1), description="Cutting-edge research in the field of quantum mechanics."),
]

db_faculty: List[Faculty] = [
    Faculty(id=1, name="Dr. Alan Turing", department="Engineering", title="Professor", email="alan.turing@university.edu", bio="Pioneer of theoretical computer science and artificial intelligence."),
    Faculty(id=2, name="Dr. Marie Curie", department="Sciences", title="Professor", email="marie.curie@university.edu", bio="Renowned for her research on radioactivity and a two-time Nobel prize winner."),
    Faculty(id=3, name="Dr. Ada Lovelace", department="Engineering", title="Associate Professor", email="ada.lovelace@university.edu", bio="Specializes in algorithms and computational theory."),
    Faculty(id=4, name="Dr. Vincent Van Gogh", department="Arts & Humanities", title="Lecturer", email="vincent.vangogh@university.edu", bio="Expert in Post-Impressionist painting and art theory."),
]

# --- APIRouter Setup ---

# All routes defined here will have the prefix /api/v1
router = APIRouter(prefix="/api/v1")


# --- Program Endpoints ---

@router.get(
    "/programs",
    response_model=List[Program],
    tags=["Programs"],
    summary="Retrieve all academic programs",
    description="Get a list of all academic programs, with optional filters for department, degree level, and session start date."
)
def get_programs(
    department: Optional[str] = Query(None, description="Filter programs by department name"),
    degree_level: Optional[str] = Query(None, description="Filter programs by degree level (e.g., Bachelor's)"),
    session_start_date: Optional[date] = Query(None, description="Filter programs by the exact session start date (YYYY-MM-DD)")
):
    """
    Retrieve all academic programs.
    - **department**: (optional) filter by department.
    - **degree_level**: (optional) filter by degree level.
    - **session_start_date**: (optional) filter by session start date.
    """
    filtered_programs = db_programs

    if department:
        filtered_programs = [p for p in filtered_programs if p.department.lower() == department.lower()]
    
    if degree_level:
        filtered_programs = [p for p in filtered_programs if p.degree_level.lower() == degree_level.lower()]

    if session_start_date:
        filtered_programs = [p for p in filtered_programs if p.session_start_date == session_start_date]
        
    return filtered_programs


@router.get(
    "/programs/{program_id}",
    response_model=Program,
    tags=["Programs"],
    summary="Get a single academic program by ID",
    description="Retrieve detailed information for a specific academic program using its unique ID."
)
def get_program_by_id(program_id: int):
    """
    Get detailed information for a single academic program.
    - **program_id**: The unique identifier of the program.
    """
    program = next((p for p in db_programs if p.id == program_id), None)
    if program is None:
        raise HTTPException(status_code=404, detail=f"Program with ID {program_id} not found")
    return program


# --- Faculty Endpoints ---

@router.get(
    "/faculty",
    response_model=List[Faculty],
    tags=["Faculty"],
    summary="Retrieve all faculty members",
    description="Get a list of all faculty members, with an optional filter for department."
)
def get_faculty(
    department: Optional[str] = Query(None, description="Filter faculty by department name")
):
    """
    Retrieve all faculty members.
    - **department**: (optional) filter by department.
    """
    if department:
        return [f for f in db_faculty if f.department.lower() == department.lower()]
    return db_faculty


@router.get(
    "/faculty/{faculty_id}",
    response_model=Faculty,
    tags=["Faculty"],
    summary="Get a single faculty member by ID",
    description="Retrieve the complete profile for a specific faculty member using their unique ID."
)
def get_faculty_by_id(faculty_id: int):
    """
    Get the complete profile for a single faculty member.
    - **faculty_id**: The unique identifier of the faculty member.
    """
    faculty_member = next((f for f in db_faculty if f.id == faculty_id), None)
    if faculty_member is None:
        raise HTTPException(status_code=404, detail=f"Faculty member with ID {faculty_id} not found")
    return faculty_member