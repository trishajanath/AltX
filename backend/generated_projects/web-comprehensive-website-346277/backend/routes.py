from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

# Assuming a models.py file exists in the same directory with Pydantic models
# For context, the models.py file would look something like this:
#
# from pydantic import BaseModel
# from typing import List
#
# class Program(BaseModel):
#     id: int
#     name: str
#     department: str
#     degree_level: str  # e.g., 'UG', 'PG', 'PhD'
#     description: str
#     courses: List[str]
#
# class Faculty(BaseModel):
#     id: int
#     name: str
#     department: str
#     title: str
#     email: str
#     bio: str
#
# class Alumni(BaseModel):
#     id: int
#     name: str
#     graduation_year: int
#     program: str
#     achievement: str
#     featured: bool

from .models import Program, Faculty, Alumni

# --- In-Memory Storage (acting as a simple database) ---

db_programs = [
    Program(id=1, name="Bachelor of Science in Computer Science", department="CSE", degree_level="UG", description="A comprehensive undergraduate program in computer science.", courses=["Intro to Programming", "Data Structures", "Algorithms"]),
    Program(id=2, name="Master of Science in Data Science", department="CSE", degree_level="PG", description="An advanced program focusing on data analysis and machine learning.", courses=["Machine Learning", "Big Data Analytics", "Statistical Methods"]),
    Program(id=3, name="Bachelor of Arts in Electrical Engineering", department="EEE", degree_level="UG", description="Foundational program in electrical and electronics engineering.", courses=["Circuit Theory", "Digital Logic Design", "Signals and Systems"]),
    Program(id=4, name="PhD in Mechanical Engineering", department="ME", degree_level="PhD", description="Doctoral research program in mechanical engineering.", courses=["Advanced Thermodynamics", "Fluid Dynamics", "Research Methodology"]),
]

db_faculty = [
    Faculty(id=1, name="Dr. Alan Turing", department="CSE", title="Professor", email="alan.t@university.edu", bio="Pioneer in computer science and artificial intelligence."),
    Faculty(id=2, name="Dr. Marie Curie", department="PHY", title="Associate Professor", email="marie.c@university.edu", bio="Expert in physics and computational chemistry."),
    Faculty(id=3, name="Dr. Ada Lovelace", department="CSE", title="Assistant Professor", email="ada.l@university.edu", bio="Specializes in algorithms and computational theory."),
    Faculty(id=4, name="Dr. Nikola Tesla", department="EEE", title="Professor", email="nikola.t@university.edu", bio="Leading researcher in wireless energy and AC systems."),
]

db_alumni = [
    Alumni(id=1, name="John Doe", graduation_year=2018, program="B.S. in Computer Science", achievement="Founder of a successful tech startup.", featured=True),
    Alumni(id=2, name="Jane Smith", graduation_year=2020, program="M.S. in Data Science", achievement="Lead Data Scientist at a major corporation.", featured=True),
    Alumni(id=3, name="Peter Jones", graduation_year=2015, program="B.A. in Electrical Engineering", achievement="Invented a new energy-efficient transistor.", featured=False),
    Alumni(id=4, name="Emily White", graduation_year=2019, program="B.S. in Computer Science", achievement="Published influential research on AI ethics.", featured=True),
    Alumni(id=5, name="Michael Brown", graduation_year=2021, program="PhD in Mechanical Engineering", achievement="Developed a breakthrough in robotics.", featured=True),
    Alumni(id=6, name="Sarah Green", graduation_year=2017, program="B.S. in Computer Science", achievement="Key developer for a popular open-source project.", featured=True),
    Alumni(id=7, name="David Black", graduation_year=2022, program="M.S. in Data Science", achievement="Won a national data science competition.", featured=True),
]


# --- APIRouter Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["University Info"],
)


# --- Route Definitions ---

@router.get("/programs", response_model=List[Program])
async def get_programs(
    department: Optional[str] = Query(None, description="Filter programs by department code (e.g., CSE)"),
    level: Optional[str] = Query(None, description="Filter programs by degree level (e.g., UG, PG)")
):
    """
    Retrieve all academic programs, with optional query parameters for filtering
    by department and degree_level.
    """
    results = db_programs
    if department:
        results = [p for p in results if p.department.lower() == department.lower()]
    if level:
        results = [p for p in results if p.degree_level.lower() == level.lower()]
    return results


@router.get("/programs/{program_id}", response_model=Program)
async def get_program_by_id(program_id: int):
    """
    Get detailed information for a single academic program by its unique ID.
    """
    program = next((p for p in db_programs if p.id == program_id), None)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.get("/faculty", response_model=List[Faculty])
async def get_faculty(
    name: Optional[str] = Query(None, description="Search faculty members by name (case-insensitive)"),
    department: Optional[str] = Query(None, description="Filter faculty by department code (e.g., CSE)")
):
    """
    Get a list of faculty members, searchable by name and filterable by department.
    """
    results = db_faculty
    if department:
        results = [f for f in results if f.department.lower() == department.lower()]
    if name:
        results = [f for f in results if name.lower() in f.name.lower()]
    return results


@router.get("/alumni/featured", response_model=List[Alumni])
async def get_featured_alumni():
    """
    Retrieve a list of 5-10 featured alumni profiles for a spotlight carousel.
    """
    featured = [alumnus for alumnus in db_alumni if alumnus.featured]
    return featured