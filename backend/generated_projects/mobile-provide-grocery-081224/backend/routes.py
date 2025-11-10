import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# In a real application, these models would be in a separate 'models.py' file.
# For demonstration, their structure is implied by their usage below.
#
# models.py would contain:
#
# from pydantic import BaseModel, EmailStr, Field
# from typing import List, Optional
#
# class UserBase(BaseModel):
#     email: EmailStr
#     name: str
#
# class UserCreate(UserBase):
#     password: str
#
# class UserOut(UserBase):
#     id: str
#
# class UserInDB(UserOut):
#     hashed_password: str
#     dietary_preferences: List[str] = []
#
# class Product(BaseModel):
#     id: str
#     name: str
#     category: str
#     description: Optional[str] = None
#     tags: List[str] = []
#
# class Token(BaseModel):
#     access_token: str
#     token_type: str
#
from .models import User, UserCreate, UserOut, Product, Token, UserInDB

# --- In-Memory Storage ---
# This acts as a simple, non-persistent database for demonstration purposes.
db_users: dict[str, UserInDB] = {}
db_products: List[Product] = []
db_purchase_history: dict[str, List[str]] = {}

# --- Routers Setup ---
# Separate router for authentication to keep auth logic isolated.
auth_router = APIRouter(tags=["Authentication"])
# Main API router with a versioned prefix.
api_router = APIRouter(prefix="/api/v1", tags=["Products"])

# --- Security and Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# --- Helper Functions ---

def fake_hash_password(password: str) -> str:
    """In a real app, use a library like passlib. Never store plain text."""
    return "fakehashed_" + password

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Retrieve a user from the in-memory DB by email."""
    return db_users.get(email)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    A dependency to get the current user from a token.
    For this example, we'll decode the "token" (which is just the user's email)
    and fetch the user. In a real app, this would involve JWT decoding and validation.
    """
    user = get_user_by_email(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# --- Pre-populating In-Memory Data for Demonstration ---

def populate_initial_data():
    """Clears and fills the in-memory DB with sample data."""
    global db_users, db_products, db_purchase_history
    db_users.clear()
    db_products.clear()
    db_purchase_history.clear()

    # Sample Users
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    db_users = {
        "user1@example.com": UserInDB(
            id=user1_id,
            email="user1@example.com",
            name="Alice",
            hashed_password=fake_hash_password("password123"),
            dietary_preferences=["gluten-free", "vegan"]
        ),
        "user2@example.com": UserInDB(
            id=user2_id,
            email="user2@example.com",
            name="Bob",
            hashed_password=fake_hash_password("password456"),
            dietary_preferences=["organic"]
        ),
    }

    # Sample Products
    db_products = [
        Product(id=str(uuid.uuid4()), name="Organic Whole Wheat Bread", category="Bakery", tags=["organic", "vegan"]),
        Product(id=str(uuid.uuid4()), name="Gluten-Free Sourdough", category="Bakery", tags=["gluten-free"]),
        Product(id=str(uuid.uuid4()), name="Almond Milk", category="Dairy Alternatives", tags=["vegan", "gluten-free"]),
        Product(id=str(uuid.uuid4()), name="Organic Gala Apples", category="Produce", tags=["organic"]),
        Product(id=str(uuid.uuid4()), name="Cheddar Cheese Block", category="Dairy", tags=[]),
        Product(id=str(uuid.uuid4()), name="Grass-fed Beef Steak", category="Meat", tags=["gluten-free"]),
    ]

    # Sample Purchase History
    db_purchase_history = {
        user1_id: [db_products[0].id],  # Alice bought Organic Whole Wheat Bread
    }

populate_initial_data()


# --- Authentication Endpoints ---

@auth_router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    """
    Create a new user account with email, password, and name.
    """
    if get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = fake_hash_password(user_in.password)
    user_id = str(uuid.uuid4())
    
    new_user = UserInDB(
        id=user_id,
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_password,
        dietary_preferences=[] # Preferences can be set via another endpoint
    )
    
    db_users[user_in.email] = new_user
    
    return UserOut(id=user_id, email=new_user.email, name=new_user.name)


@auth_router.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a JWT access token.
    Uses form data (username & password).
    """
    user = get_user_by_email(form_data.username)
    if not user or user.hashed_password != fake_hash_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real app, you would create a proper JWT token here.
    # For this example, the "token" is just the user's email.
    access_token = user.email
    
    return {"access_token": access_token, "token_type": "bearer"}


# --- API V1 Endpoints ---

@api_router.get("/products", response_model=List[Product])
async def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    Retrieve a paginated list of products, with query parameters for
    search, category, and dietary tags.
    Example: /api/v1/products?search=bread&tags=gluten-free,vegan
    """
    results = db_products

    if search:
        results = [p for p in results if search.lower() in p.name.lower()]

    if category:
        results = [p for p in results if p.category.lower() == category.lower()]

    if tags:
        # Filter by products that have ALL the specified tags
        required_tags = {tag.strip().lower() for tag in tags.split(',')}
        results = [
            p for p in results 
            if required_tags.issubset(set(pt.lower() for pt in p.tags))
        ]

    return results[skip : skip + limit]


@api_router.get("/products/recommendations", response_model=List[Product])
async def get_recommendations(current_user: UserInDB = Depends(get_current_user)):
    """
    Get a list of recommended products based on the user's purchase
    history and dietary preferences. Requires authentication.
    """
    user_purchases = set(db_purchase_history.get(current_user.id, []))
    user_preferences = set(pref.lower() for pref in current_user.dietary_preferences)
    
    recommendations = []
    
    # Simple recommendation logic:
    # 1. Find products matching user's dietary preferences.
    # 2. Exclude items they have already purchased.
    for product in db_products:
        if product.id in user_purchases:
            continue
        
        product_tags = set(tag.lower() for tag in product.tags)
        
        # Recommend if any of the product's tags match user's preferences
        if user_preferences.intersection(product_tags):
            recommendations.append(product)
            
    if not recommendations:
        # Fallback: if no preference-based recommendations, suggest popular items
        # (Here, we just take the first 5 items not purchased)
        recommendations = [p for p in db_products if p.id not in user_purchases][:5]

    return recommendations