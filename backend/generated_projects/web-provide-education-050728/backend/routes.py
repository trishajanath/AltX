import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

# --- Configuration ---
# In a real app, use environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ===============================================================================
# |                                 MODELS                                      |
# |                  (In a real app, this would be in models.py)                |
# ===============================================================================

# --- Auth Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- User Models ---
class User(BaseModel):
    id: int
    email: str
    full_name: str

class UserInDB(User):
    # In a real app, this would be a hashed password
    password: str

# --- Course Models ---
class Assignment(BaseModel):
    id: int
    course_id: int
    title: str
    due_date: datetime

class Announcement(BaseModel):
    id: int
    course_id: int
    title: str
    content: str

class Course(BaseModel):
    id: int
    name: str
    instructor_id: int

class CourseDetail(Course):
    assignments: List[Assignment]
    announcements: List[Announcement]

# --- Gradebook Models ---
class StudentGrade(BaseModel):
    assignment_id: int
    assignment_title: str
    grade: Optional[int] = None

class GradebookEntry(BaseModel):
    student_id: int
    student_name: str
    grades: List[StudentGrade]

class GradebookResponse(BaseModel):
    course_id: int
    course_name: str
    gradebook: List[GradebookEntry]


# ===============================================================================
# |                             IN-MEMORY STORAGE                               |
# |                   (This simulates a database)                               |
# ===============================================================================

DB_USERS = {
    1: UserInDB(id=1, email="instructor@example.com", full_name="Dr. Ada Lovelace", password="password123"),
    2: UserInDB(id=2, email="student1@example.com", full_name="Charles Babbage", password="password123"),
    3: UserInDB(id=3, email="student2@example.com", full_name="Grace Hopper", password="password123"),
}

DB_COURSES = {
    101: Course(id=101, name="Introduction to Computer Science", instructor_id=1),
    102: Course(id=102, name="Advanced Algorithms", instructor_id=1),
}

DB_ENROLLMENTS = [
    {"user_id": 1, "course_id": 101, "role": "instructor"},
    {"user_id": 1, "course_id": 102, "role": "instructor"},
    {"user_id": 2, "course_id": 101, "role": "student"},
    {"user_id": 3, "course_id": 101, "role": "student"},
    {"user_id": 3, "course_id": 102, "role": "student"},
]

DB_ASSIGNMENTS = {
    1: Assignment(id=1, course_id=101, title="Assignment 1: Basics", due_date=datetime(2023, 10, 1)),
    2: Assignment(id=2, course_id=101, title="Assignment 2: Data Structures", due_date=datetime(2023, 10, 15)),
    3: Assignment(id=3, course_id=102, title="Project Proposal", due_date=datetime(2023, 11, 1)),
}

DB_ANNOUNCEMENTS = {
    1: Announcement(id=1, course_id=101, title="Welcome!", content="Welcome to CS101!"),
    2: Announcement(id=2, course_id=101, title="Midterm Reminder", content="The midterm is next week."),
}

DB_SUBMISSIONS = [
    {"assignment_id": 1, "student_id": 2, "grade": 95},
    {"assignment_id": 2, "student_id": 2, "grade": 88},
    {"assignment_id": 1, "student_id": 3, "grade": 92},
    # Student 3 has not submitted assignment 2 yet
]

# ===============================================================================
# |                           ROUTER SETUP & PREFIX                           |
# ===============================================================================

router = APIRouter(
    prefix="/api/v1",
    tags=["API v1"],
)

# ===============================================================================
# |                         AUTHENTICATION & DEPENDENCIES                       |
# ===============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Helper to find a user by email in the in-memory DB."""
    for user in DB_USERS.values():
        if user.email == email:
            return user
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decodes token, validates, and returns the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# ===============================================================================
# |                                  ENDPOINTS                                  |
# ===============================================================================

@router.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login. Takes email and password, returns a JWT access token.
    """
    user = get_user_by_email(form_data.username)
    # In a real app, use a secure password hashing and verification function
    if not user or user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/courses", response_model=List[Course], tags=["Users", "Courses"])
async def read_user_courses(current_user: User = Depends(get_current_user)):
    """
    Get all courses for the currently authenticated user (either enrolled
    as a student or teaching as an instructor).
    """
    user_course_ids = {
        enrollment["course_id"]
        for enrollment in DB_ENROLLMENTS
        if enrollment["user_id"] == current_user.id
    }
    
    user_courses = [
        course for course_id, course in DB_COURSES.items() if course_id in user_course_ids
    ]
    
    return user_courses


@router.get("/courses/{course_id}", response_model=CourseDetail, tags=["Courses"])
async def read_course_details(course_id: int, current_user: User = Depends(get_current_user)):
    """
    Get detailed information for a single course, including its
    assignments and announcements.
    """
    # Check if course exists
    course = DB_COURSES.get(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Check if user is authorized to view this course
    is_authorized = any(
        enrollment["user_id"] == current_user.id and enrollment["course_id"] == course_id
        for enrollment in DB_ENROLLMENTS
    )
    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this course")

    # Get related data
    assignments = [a for a in DB_ASSIGNMENTS.values() if a.course_id == course_id]
    announcements = [a for a in DB_ANNOUNCEMENTS.values() if a.course_id == course_id]

    return CourseDetail(
        **course.dict(),
        assignments=assignments,
        announcements=announcements
    )


@router.get("/courses/{course_id}/gradebook", response_model=GradebookResponse, tags=["Courses", "Instructors"])
async def read_course_gradebook(course_id: int, current_user: User = Depends(get_current_user)):
    """
    For instructors: retrieve all students and their submission grades
    for a specific course.
    """
    # Check if course exists
    course = DB_COURSES.get(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Authorization: Only the instructor can view the gradebook
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the course instructor can view the gradebook")

    # Get students enrolled in the course
    student_enrollments = [
        e for e in DB_ENROLLMENTS if e["course_id"] == course_id and e["role"] == "student"
    ]
    student_ids = {e["user_id"] for e in student_enrollments}
    
    # Get assignments for the course
    course_assignments = [a for a in DB_ASSIGNMENTS.values() if a.course_id == course_id]

    gradebook_entries = []
    for student_id in student_ids:
        student = DB_USERS.get(student_id)
        if not student:
            continue

        student_grades = []
        for assignment in course_assignments:
            submission = next(
                (s for s in DB_SUBMISSIONS if s["assignment_id"] == assignment.id and s["student_id"] == student_id),
                None
            )
            student_grades.append(
                StudentGrade(
                    assignment_id=assignment.id,
                    assignment_title=assignment.title,
                    grade=submission["grade"] if submission else None
                )
            )
        
        gradebook_entries.append(
            GradebookEntry(
                student_id=student.id,
                student_name=student.full_name,
                grades=student_grades
            )
        )

    return GradebookResponse(
        course_id=course.id,
        course_name=course.name,
        gradebook=gradebook_entries
    )