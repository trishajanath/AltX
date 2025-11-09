import uuid
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# In a real application, these models would be in a separate 'models.py' file.
# For this self-contained example, they are defined here.
# --- Start: Models ---
from pydantic import BaseModel, EmailStr

class Product(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    price: float

class User(BaseModel):
    email: EmailStr

class UserCreate(User):
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
# --- End: Models ---


# --- Configuration and Security ---
# CRITICAL: Load secret from environment. For production, set a strong, unique SECRET_KEY.
# Example generation: `openssl rand -hex 32`
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_insecure_default_key_for_development_only_change_it")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- In-Memory Storage (Simulating a Database) ---
db_users: List[UserInDB] = [
    UserInDB(
        email="user1@example.com",
        hashed_password=get_password_hash("password123")
    ),
    UserInDB(
        email="user2@example.com",
        hashed_password=get_password_hash("securepass")
    )
]

db_products: List[Product] = [
    Product(id=str(uuid.uuid4()), name="Laptop Pro", description="A high-performance laptop for professionals.", category="electronics", tags=["computer", "pro", "work"], price=1499.99),
    Product(id=str(uuid.uuid4()), name="Wireless Mouse", description="Ergonomic wireless mouse with long battery life.", category="electronics", tags=["computer", "accessory"], price=49.99),
    Product(id=str(uuid.uuid4()), name="Organic Coffee Beans", description="Fair-trade, single-origin coffee beans.", category="groceries", tags=["coffee", "organic", "beverage"], price=19.99),
    Product(id=str(uuid.uuid4()), name="Running Shoes", description="Lightweight shoes for marathon runners.", category="apparel", tags=["sports", "running", "footwear"], price=120.00),
    Product(id=str(uuid.uuid4()), name="Smart Home Hub", description="Control all your smart devices from one hub.", category="electronics", tags=["smart home", "iot", "computer"], price=99.50),
    Product(id=str(uuid.uuid4()), name="Yoga Mat", description="Eco-friendly and non-slip yoga mat.", category="sports", tags=["yoga", "fitness", "accessory"], price=35.00),
]

# --- Helper Functions for DB Operations ---
def get_user(email: str) -> Optional[UserInDB]:
    for user in db_users:
        if user.email == email:
            return user
    return None

# --- APIRouter Initialization ---
router = APIRouter(
    prefix="/api/v1",
    tags=["api"],
)

# --- Authentication Endpoints ---
@router.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    """
    User registration. Creates a new user account with a hashed password.
    """
    db_user = get_user(user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    hashed_password = get_password_hash(user.password)
    new_user = UserInDB(email=user.email, hashed_password=hashed_password)
    db_users.append(new_user)
    return User(email=new_user.email)

@router.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login. Accepts email and password, returns a JWT access token upon success.
    """
    user = get_user(form_data.username) # OAuth2 form uses 'username' for the email field
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


# --- Product Endpoints ---
@router.get("/products", response_model=List[Product])
def get_products(
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100)
):
    """
    Retrieve a paginated list of products.
    Supports filtering by 'category' and 'tags' via query parameters.
    """
    filtered_products = db_products

    if category:
        filtered_products = [p for p in filtered_products if p.category.lower() == category.lower()]

    if tags:
        # Product must have all the tags specified in the query
        tag_set = set(t.lower() for t in tags)
        filtered_products = [
            p for p in filtered_products if tag_set.issubset(set(pt.lower() for pt in p.tags))
        ]

    return filtered_products[skip : skip + limit]

@router.get("/products/search", response_model=List[Product])
def search_products(q: str = Query(..., min_length=3)):
    """
    Performs a full-text search on product names and descriptions
    based on a query parameter 'q'.
    """
    search_term = q.lower()
    search_results = [
        p for p in db_products
        if search_term in p.name.lower() or search_term in p.description.lower()
    ]

    if not search_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No products found matching '{q}'"
        )

    return search_results
