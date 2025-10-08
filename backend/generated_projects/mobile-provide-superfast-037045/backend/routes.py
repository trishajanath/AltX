import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# This assumes you have a `models.py` file in the same directory.
# It should contain Pydantic models like:
# UserCreate, UserLogin, UserInDB, UserOut, UserProfile,
# Product, Address, Token, TokenData
from . import models

# --- Configuration and Setup ---

# Create an APIRouter instance with a prefix for all routes
router = APIRouter(prefix="/api/v1")

# Password hashing setup using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
# In a real app, load the secret key from environment variables for security
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme setup
# The tokenUrl should point to our token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# --- In-Memory "Database" ---
# Using dictionaries and lists to simulate a database for this example.

# Store user data: key is phone_number, value is UserInDB object
fake_users_db = {}

# Store product data
fake_products_db = [
    models.Product(id=1, name="Organic Bananas", category="Fruits", price=1.99),
    models.Product(id=2, name="Whole Milk, 1 Gallon", category="Dairy", price=3.49),
    models.Product(id=3, name="Artisan Sourdough Bread", category="Bakery", price=4.99),
    models.Product(id=4, name="Free-Range Eggs, Dozen", category="Dairy", price=5.29),
    models.Product(id=5, name="Avocado", category="Fruits", price=2.50),
    models.Product(id=6, name="Organic Chicken Breast", category="Meat", price=9.99),
]

# Store user addresses: key is phone_number, value is a list of Address objects
fake_addresses_db = {}


# --- Security and Helper Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
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

def get_user(phone_number: str) -> Optional[models.UserInDB]:
    """Retrieves a user from the fake database by phone number."""
    return fake_users_db.get(phone_number)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> models.UserInDB:
    """
    Dependency to get the current authenticated user.
    Decodes the JWT token, validates it, and fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
        token_data = models.TokenData(phone_number=phone_number)
    except JWTError:
        raise credentials_exception

    user = get_user(phone_number=token_data.phone_number)
    if user is None:
        raise credentials_exception
    return user


# --- API Endpoints ---

@router.post("/auth/token", response_model=models.Token, tags=["Authentication"])
async def login_for_access_token(form_data: models.UserLogin):
    """
    Authenticate user with phone number and password, returning a JWT access token.
    """
    user = get_user(form_data.phone_number)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.phone_number}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/register", response_model=models.UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def register_user(user_in: models.UserCreate):
    """
    Create a new user account.
    """
    if get_user(user_in.phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )

    hashed_password = get_password_hash(user_in.password)
    user_in_db = models.UserInDB(**user_in.dict(), hashed_password=hashed_password)

    # Store the new user in our fake DBs
    fake_users_db[user_in_db.phone_number] = user_in_db
    # Add a default address for the new user
    fake_addresses_db[user_in_db.phone_number] = [
        models.Address(street="123 Main St", city="Anytown", postal_code="12345")
    ]

    return user_in_db


@router.get("/products", response_model=List[models.Product], tags=["Products"])
async def get_products(category: Optional[str] = None, q: Optional[str] = None):
    """
    Retrieve a list of available products from the user's nearest fulfillment center.
    Supports filtering by `category` and searching by `q`.
    """
    products = fake_products_db[:]  # Create a copy to avoid modifying the original

    if category:
        products = [p for p in products if p.category.lower() == category.lower()]

    if q:
        products = [p for p in products if q.lower() in p.name.lower()]

    return products


@router.get("/profile/me", response_model=models.UserProfile, tags=["Profile"])
async def read_users_me(current_user: models.UserInDB = Depends(get_current_user)):
    """
    Get the authenticated user's profile information and addresses.
    """
    user_addresses = fake_addresses_db.get(current_user.phone_number, [])
    user_profile = models.UserProfile(
        phone_number=current_user.phone_number,
        full_name=current_user.full_name,
        addresses=user_addresses
    )
    return user_profile