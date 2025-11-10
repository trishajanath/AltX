import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# Assuming models are defined in a sibling file `models.py`
# You would need to create this file with the Pydantic models.
# Example models.py content is provided in comments at the bottom of this file.
from .models import User, Course, Token, TokenData, UserInDB

# --- Configuration and Security Setup ---

# This would be in a .env file in a real application
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# --- In-Memory Database ---

# In a real app, this would be a database connection and service layer.
# For this example, we use a simple dictionary.
# Note: We are storing plain text passwords for simplicity.
# In a real application, ALWAYS store hashed passwords.
DB: Dict[str, List[Dict[str, Any]]] = {
    "users": [
        {
            "id": 1,
            "email": "teacher@example.com",
            "full_name": "Dr. Ada Lovelace",
            "role": "teacher",
            "hashed_password": pwd_context.hash("password123"),
        },
        {
            "id": 2,
            "email": "student1@example.com",
            "full_name": "Charles Babbage",
            "role": "student",
            "hashed_password": pwd_context.hash("password456"),
        },
        {
            "id": 3,
            "email": "student2@example.com",
            "full_name": "Grace Hopper",
            "role": "student",
            "hashed_password": pwd_context.hash("password789"),
        },
        {
            "id": 4,
            "email": "student3@example.com",
            "full_name": "Alan Turing",
            "role": "student",
            "hashed_password": pwd_context.hash("password101"),
        },
    ],
    "courses": [
        {
            "id": 101,
            "name": "Introduction to Computer Science",
            "teacher_id": 1,
            "student_ids": [2, 3],
        },
        {
            "id": 102,
            "name": "Advanced Algorithms",
            "teacher_id": 1,
            "student_ids": [3, 4],
        },
    ],
}

# --- Helper Functions ---

def get_user(email: str) -> UserInDB | None:
    """Find a user by email in the in-memory database."""
    for user_data in DB["users"]:
        if user_data["email"] == email:
            return UserInDB(**user_data)
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Dependency to get the current user from a JWT token.
    Raises HTTPException if the token is invalid or the user doesn't exist.
    """
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
    
    user = get_user(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# --- API Router ---

router = APIRouter(prefix="/api/v1")

# --- Endpoints ---

@router.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login. Takes email and password, returns a JWT access token.
    Use case: A teacher logs in at the start of the day.
    """
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
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


@router.get("/users/me", response_model=User, tags=["Users"])
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Get profile information for the currently authenticated user.
    Use case: The frontend fetches user details to display their name and role.
    """
    return current_user


@router.get("/courses", response_model=List[Course], tags=["Courses"])
async def get_user_courses(current_user: UserInDB = Depends(get_current_user)):
    """
    Get a list of courses relevant to the user. For a teacher, it's the
    courses they teach. For a student, it's the courses they are enrolled in.
    """
    user_courses = []
    if current_user.role == "teacher":
        for course_data in DB["courses"]:
            if course_data["teacher_id"] == current_user.id:
                user_courses.append(Course(**course_data))
    elif current_user.role == "student":
        for course_data in DB["courses"]:
            if current_user.id in course_data["student_ids"]:
                user_courses.append(Course(**course_data))
    return user_courses


@router.get("/courses/{course_id}/roster", response_model=List[User], tags=["Courses"])
async def get_course_roster(course_id: int, current_user: UserInDB = Depends(get_current_user)):
    """
    For a teacher, retrieve the full list of enrolled students for a specific course.
    Use case: Populate the AttendanceGrid for a class session.
    """
    # 1. Check user permissions
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view a course roster.",
        )

    # 2. Find the course
    course = next((c for c in DB["courses"] if c["id"] == course_id), None)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found.",
        )

    # 3. Verify the teacher owns this course
    if course["teacher_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this course's roster.",
        )

    # 4. Fetch student details
    roster = []
    student_ids = course.get("student_ids", [])
    for user_data in DB["users"]:
        if user_data["id"] in student_ids:
            roster.append(User(**user_data))
            
    return roster

# --- Example models.py content ---
"""
# In a separate file named `models.py`

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class UserRole(str, Enum):
    teacher = "teacher"
    student = "student"

class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: str

class Course(BaseModel):
    id: int
    name: str
    teacher_id: int
    student_ids: List[int]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
"""