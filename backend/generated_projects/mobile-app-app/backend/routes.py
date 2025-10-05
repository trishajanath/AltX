from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr

# In a real application, these models would be in a separate `models.py` file.
# To make this example self-contained and runnable, they are defined here.
# from . import models # This would be the import statement.

# --- Pydantic Models ---

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserPublic(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserInDB(UserPublic):
    hashed_password: str

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CoursePublic(CourseBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class CourseInDB(CoursePublic):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Router Setup ---
# All routes will be prefixed with /api/v1
router = APIRouter(prefix="/api/v1")

# --- In-Memory Storage ---
# Using dictionaries to simulate database tables
db_users: Dict[int, UserInDB] = {}
db_courses: Dict[int, CourseInDB] = {}
user_id_counter = 0
course_id_counter = 0

# --- Security & Dependencies ---
# The tokenUrl should point to the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Helper Functions ---

def get_password_hash(password: str) -> str:
    """A dummy password hashing function. Use passlib in a real app."""
    return f"hashed_{password}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """A dummy password verification function."""
    return get_password_hash(plain_password) == hashed_password

def get_user_by_email(email: str) -> UserInDB | None:
    """Find a user by email in the in-memory database."""
    for user in db_users.values():
        if user.email == email:
            return user
    return None

def get_user_by_id(user_id: int) -> UserInDB | None:
    """Find a user by ID in the in-memory database."""
    return db_users.get(user_id)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Dependency to get the current authenticated user.
    In a real app, this would decode a JWT. Here, the token is the user_id.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = int(token)
    except (ValueError, TypeError):
        raise credentials_exception

    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

# --- API Endpoints ---

@router.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(user_in: UserCreate):
    """
    Create a new user account.
    """
    if get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    global user_id_counter
    user_id_counter += 1
    
    hashed_password = get_password_hash(user_in.password)
    new_user = UserInDB(
        id=user_id_counter,
        email=user_in.email,
        hashed_password=hashed_password
    )
    db_users[new_user.id] = new_user
    
    return new_user

@router.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a JWT-like token.
    
    Accepts form data with `username` (as email) and `password`.
    """
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For this example, the token is simply the user's ID.
    access_token = str(user.id)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/courses", response_model=List[CoursePublic], tags=["Courses"])
async def get_all_courses(current_user: UserInDB = Depends(get_current_user)):
    """
    Retrieve all courses for the authenticated user.
    """
    user_courses = [
        course for course in db_courses.values() if course.owner_id == current_user.id
    ]
    return user_courses

@router.post("/courses", response_model=CoursePublic, status_code=status.HTTP_201_CREATED, tags=["Courses"])
async def create_course(
    course_in: CourseCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Create a new course for the authenticated user.
    """
    global course_id_counter
    course_id_counter += 1
    
    new_course = CourseInDB(
        id=course_id_counter,
        title=course_in.title,
        description=course_in.description,
        owner_id=current_user.id
    )
    db_courses[new_course.id] = new_course
    
    return new_course