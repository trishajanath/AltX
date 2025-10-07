import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# --- Configuration and In-Memory Storage ---

# This would typically be in a .env file or config module
SECRET_KEY = "a_very_secret_key_for_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# In-memory "database"
# In a real application, this would be a database (e.g., PostgreSQL, MongoDB)
db_users: Dict[str, Any] = {}
db_assignments: List[Dict[str, Any]] = []
user_id_counter = 1
assignment_id_counter = 1


# --- Pydantic Models ---
# In a real application, these would be in a separate `models.py` file.

class AssignmentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AssignmentBase(BaseModel):
    title: str
    course_id: int
    due_date: date

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    id: int
    owner_id: int
    status: AssignmentStatus = AssignmentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Security and Helper Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(username: str) -> Optional[UserInDB]:
    """Retrieves a user from the in-memory database."""
    user_dict = db_users.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decodes token, validates, and returns the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(id=user.id, username=user.username)


# --- API Routers ---

# Router for authentication endpoints
auth_router = APIRouter(
    tags=["Authentication"]
)

# Router for API v1 endpoints
api_router = APIRouter(
    prefix="/api/v1",
    tags=["Assignments"],
    dependencies=[Depends(get_current_user)] # Protect all v1 routes
)


# --- Authentication Endpoints ---

@auth_router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    """
    Create a new user account.
    """
    if get_user(user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    global user_id_counter
    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(
        id=user_id_counter,
        username=user.username,
        hashed_password=hashed_password
    )
    db_users[user.username] = user_in_db.dict()
    user_id_counter += 1
    
    return User(id=user_in_db.id, username=user_in_db.username)

@auth_router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a JWT access token.
    """
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- API v1 Endpoints ---

@api_router.post("/assignments", response_model=Assignment, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment: AssignmentCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new assignment. Expects a JSON body with title, course_id, and due_date.
    """
    global assignment_id_counter
    new_assignment = Assignment(
        id=assignment_id_counter,
        owner_id=current_user.id,
        **assignment.dict()
    )
    db_assignments.append(new_assignment.dict())
    assignment_id_counter += 1
    return new_assignment

@api_router.get("/assignments", response_model=List[Assignment])
def get_assignments(
    status: Optional[AssignmentStatus] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all assignments for the authenticated user.
    Supports query parameters for filtering, e.g., '/api/v1/assignments?status=pending&course_id=...'.
    """
    user_assignments = [
        a for a in db_assignments if a["owner_id"] == current_user.id
    ]

    if status:
        user_assignments = [
            a for a in user_assignments if a["status"] == status.value
        ]
    
    if course_id is not None:
        user_assignments = [
            a for a in user_assignments if a["course_id"] == course_id
        ]
        
    return user_assignments