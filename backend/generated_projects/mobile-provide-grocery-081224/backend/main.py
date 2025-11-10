# main.py for mobile-provide-grocery-081224

# ==============================================================================
# IMPORTS
# ==============================================================================
import os
import logging
from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, 
                        Float, ForeignKey, Enum as SQLAlchemyEnum, Boolean)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
import re

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# --- General App Config ---
APP_TITLE = "mobile-provide-grocery-081224"
APP_DESCRIPTION = "A mobile-first grocery e-commerce platform designed for busy working professionals. It offers curated meal kits, subscription-based essentials, and rapid delivery slots to streamline weekly shopping. The sleek, modern interface with a black background and white text ensures a quick, focused, and visually comfortable shopping experience, day or night."

# --- Security & JWT Config ---
# In a real production environment, load this from environment variables.
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development_only_081224")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- Database Config ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./mobile_grocery_081224.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- CORS Config ---
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React
    "http://localhost:5173",  # Vite/Vue
    "http://localhost:8080",  # Other common dev servers
]

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================================================================
# DATABASE MODELS (ORM)
# ==============================================================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    dietary_preferences = Column(String, default="") # e.g., "Vegan,Gluten-Free"
    created_at = Column(DateTime, default=datetime.utcnow)

    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    category = Column(String, index=True) # e.g., "Dairy", "Produce", "Meat"
    tags = Column(String, default="") # e.g., "Vegan,Gluten-Free,Organic"
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class MealKit(Base):
    __tablename__ = "meal_kits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    description = Column(Text)
    price = Column(Float) # Bundle price
    image_url = Column(String)
    
    items = relationship("MealKitItem", back_populates="meal_kit")

class MealKitItem(Base):
    __tablename__ = "meal_kit_items"
    id = Column(Integer, primary_key=True, index=True)
    meal_kit_id = Column(Integer, ForeignKey("meal_kits.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

    meal_kit = relationship("MealKit", back_populates="items")
    product = relationship("Product")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending") # pending, processing, shipped, delivered, cancelled
    delivery_slot_start = Column(DateTime)
    delivery_slot_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer)
    price_at_purchase = Column(Float)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    frequency = Column(String) # "weekly", "bi-weekly"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    product = relationship("Product")

# ==============================================================================
# PYDANTIC MODELS (SCHEMAS)
# ==============================================================================

# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    dietary_preferences: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: str
    tags: Optional[str] = ""

class ProductCreate(ProductBase):
    stock_quantity: int

class ProductResponse(ProductBase):
    id: int
    stock_quantity: int

    class Config:
        from_attributes = True

# --- Meal Kit Schemas ---
class MealKitItemResponse(BaseModel):
    product: ProductResponse
    quantity: int
    
    class Config:
        from_attributes = True

class MealKitResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    items: List[MealKitItemResponse]

    class Config:
        from_attributes = True

# --- Cart Schemas ---
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)

class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_price: float

# --- Order Schemas ---
class OrderItemResponse(BaseModel):
    quantity: int
    price_at_purchase: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    delivery_slot_start: Optional[datetime] = None
    delivery_slot_end: Optional[datetime] = None
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# --- Subscription Schemas ---
class SubscriptionCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)
    frequency: str # "weekly" or "bi-weekly"

class SubscriptionResponse(BaseModel):
    id: int
    quantity: int
    frequency: str
    is_active: bool
    product: ProductResponse

    class Config:
        from_attributes = True

# --- Other Feature Schemas ---
class RecipeImportRequest(BaseModel):
    url: str

class RecipeIngredient(BaseModel):
    name: str
    quantity: str

class RecipeImportResponse(BaseModel):
    recipe_title: str
    ingredients: List[RecipeIngredient]

class DeliverySlot(BaseModel):
    start_time: datetime
    end_time: datetime

class BookDeliverySlotRequest(BaseModel):
    start_time: datetime

class UserPreferencesUpdate(BaseModel):
    dietary_preferences: List[str]

# ==============================================================================
# DEPENDENCIES & UTILS
# ==============================================================================

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Password & Token Utils ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(data=data, expires_delta=expires)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user."""
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
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# ==============================================================================
# FASTAPI APP INITIALIZATION
# ==============================================================================

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@mobilegrocery.dev",
    },
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Simple logging middleware for incoming requests."""
    start_time = time()
    response = await call_next(request)
    process_time = (time() - start_time) * 1000
    logger.info(f"Request: {request.method} {request.url.path} - Completed in {process_time:.2f}ms - Status: {response.status_code}")
    return response

# --- Startup Event ---
@app.on_event("startup")
def on_startup():
    """Create database tables and seed initial data on application startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")
    
    # Seed data if database is empty
    db = SessionLocal()
    if db.query(Product).count() == 0:
        logger.info("Seeding initial data...")
        seed_data(db)
        logger.info("Initial data seeded.")
    db.close()

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

# --- Health Check ---
@app.get("/", tags=["Health Check"])
async def health_check():
    """Root endpoint for health checks."""
    return {"status": "healthy", "app": APP_TITLE, "timestamp": datetime.utcnow()}

# --- Authentication Routes ---
auth_router = FastAPI()

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    access_token = create_access_token(data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in a user and return JWT tokens."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@auth_router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Refresh an access token using a valid refresh token."""
    user = await get_current_user(token=refresh_token, db=db) # Validate refresh token
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    new_refresh_token = create_refresh_token(data={"sub": user.email}) # Issue a new refresh token for security
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently authenticated user."""
    return current_user

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# --- User Profile Routes ---
user_router = FastAPI()

@user_router.put("/me/preferences", response_model=UserResponse)
async def update_dietary_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's dietary preferences."""
    current_user.dietary_preferences = ",".join(sorted(list(set(preferences.dietary_preferences))))
    db.commit()
    db.refresh(current_user)
    return current_user

app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])

# --- Product & Inventory Routes ---
product_router = FastAPI()

@product_router.get("/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a list of all products.
    Applies persistent dietary preference filtering from the user's profile.
    """
    query = db.query(Product).filter(Product.stock_quantity > 0)
    
    # Persistent Dietary Preference Filtering
    if current_user.dietary_preferences:
        preferences = current_user.dietary_preferences.split(',')
        for pref in preferences:
            query = query.filter(Product.tags.contains(pref))

    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
        
    return query.all()

@product_router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """Get details of a specific product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

app.include_router(product_router, prefix="/api/v1/products", tags=["Products"])

@app.get("/api/v1/inventory", tags=["Inventory"], response_model=Dict[int, int])
async def get_inventory(db: Session = Depends(get_db)):
    """Get current stock levels for all products."""
    products = db.query(Product).all()
    return {p.id: p.stock_quantity for p in products}

# --- Meal Kit Routes ---
meal_kit_router = FastAPI()

@meal_kit_router.get("/", response_model=List[MealKitResponse])
async def get_meal_kits(db: Session = Depends(get_db)):
    """Get a list of all available meal kits."""
    return db.query(MealKit).all()

app.include_router(meal_kit_router, prefix="/api/v1/meal-kits", tags=["Meal Kits"])

# --- Shopping Cart Routes ---
cart_router = FastAPI()

@cart_router.get("/", response_model=CartResponse)
async def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current user's shopping cart."""
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return {"items": cart_items, "total_price": total_price}

@cart_router.post("/add", response_model=CartItemResponse)
async def add_to_cart(item: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add a product to the shopping cart."""
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock_quantity < item.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock")

    cart_item = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == item.product_id).first()
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=item.product_id, quantity=item.quantity)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

@cart_router.post("/add-kit/{kit_id}", response_model=CartResponse)
async def add_meal_kit_to_cart(kit_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add all items from a meal kit to the cart."""
    meal_kit = db.query(MealKit).filter(MealKit.id == kit_id).first()
    if not meal_kit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal kit not found")

    for kit_item in meal_kit.items:
        await add_to_cart(CartItemCreate(product_id=kit_item.product_id, quantity=kit_item.quantity), current_user, db)
    
    return await get_cart(current_user, db)

@cart_router.delete("/remove/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(cart_item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove an item from the shopping cart."""
    cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id, CartItem.user_id == current_user.id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return

app.include_router(cart_router, prefix="/api/v1/cart", tags=["Shopping Cart"])

# --- Order Processing Routes ---
order_router = FastAPI()

@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    delivery_slot: BookDeliverySlotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an order from the user's current cart."""
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total_amount = 0
    order_items = []
    for item in cart_items:
        product = item.product
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {product.name}")
        
        total_amount += product.price * item.quantity
        product.stock_quantity -= item.quantity
        order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, price_at_purchase=product.price))

    new_order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        items=order_items,
        delivery_slot_start=delivery_slot.start_time,
        delivery_slot_end=delivery_slot.start_time + timedelta(hours=1)
    )
    
    db.add(new_order)
    # Clear the cart
    for item in cart_items:
        db.delete(item)
        
    db.commit()
    db.refresh(new_order)
    return new_order

@order_router.get("/", response_model=List[OrderResponse])
async def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current user's order history."""
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()

@order_router.post("/restock", response_model=CartResponse)
async def weekly_restock(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """'One-Click Weekly Restock' - adds items from the most recent order to the cart."""
    last_order = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).first()
    if not last_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No previous orders found to restock from.")

    # Clear current cart before restocking
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()

    for item in last_order.items:
        await add_to_cart(CartItemCreate(product_id=item.product_id, quantity=item.quantity), current_user, db)
    
    return await get_cart(current_user, db)

app.include_router(order_router, prefix="/api/v1/orders", tags=["Orders"])

# --- Payment Processing Route ---
@app.post("/api/v1/payments/process", tags=["Payments"])
async def process_payment(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mock payment processing endpoint."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order has already been processed")

    # Mocking a successful payment
    order.status = "processing"
    db.commit()
    return {"status": "success", "message": f"Payment for order {order_id} processed successfully."}

# --- Subscription Routes ---
subscription_router = FastAPI()

@subscription_router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(sub: SubscriptionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new subscription for a pantry staple."""
    if sub.frequency not in ["weekly", "bi-weekly"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid frequency. Must be 'weekly' or 'bi-weekly'.")
    
    product = db.query(Product).filter(Product.id == sub.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    new_sub = Subscription(
        user_id=current_user.id,
        product_id=sub.product_id,
        quantity=sub.quantity,
        frequency=sub.frequency
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@subscription_router.get("/me", response_model=List[SubscriptionResponse])
async def get_my_subscriptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current user's active subscriptions."""
    return db.query(Subscription).filter(Subscription.user_id == current_user.id, Subscription.is_active == True).all()

@subscription_router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(subscription_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cancel a subscription."""
    sub = db.query(Subscription).filter(Subscription.id == subscription_id, Subscription.user_id == current_user.id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    sub.is_active = False
    db.commit()
    return

app.include_router(subscription_router, prefix="/api/v1/subscriptions", tags=["Subscriptions"])

# --- Smart Shopping List & Delivery Routes ---
features_router = FastAPI()

@features_router.post("/shopping-list/import-url", response_model=RecipeImportResponse)
async def import_recipe_from_url(request: RecipeImportRequest, current_user: User = Depends(get_current_user)):
    """
    Smart Shopping List: Parses a recipe URL to create a shopping list.
    NOTE: This is a MOCK implementation. A real version would use a web scraper.
    """
    url = request.url
    if "tuscanchicken" in url:
        return {
            "recipe_title": "30-Minute Tuscan Chicken",
            "ingredients": [
                {"name": "Chicken Breast", "quantity": "1 lb"},
                {"name": "Heavy Cream", "quantity": "1 cup"},
                {"name": "Spinach", "quantity": "5 oz"},
                {"name": "Sun-Dried Tomatoes", "quantity": "1/2 cup"}
            ]
        }
    elif "pastarecipe" in url:
        return {
            "recipe_title": "Classic Tomato Pasta",
            "ingredients": [
                {"name": "Tomatoes", "quantity": "2 lbs"},
                {"name": "Pasta", "quantity": "1 lb"},
                {"name": "Basil", "quantity": "1 bunch"},
                {"name": "Parmesan Cheese", "quantity": "1/2 cup"}
            ]
        }
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse recipe from this URL.")

@features_router.get("/delivery/slots", response_model=List[DeliverySlot])
async def get_delivery_slots():
    """Get available 1-hour delivery slots for the next 24 hours."""
    slots = []
    now = datetime.utcnow()
    # Start from the next whole hour
    start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    for i in range(24): # Generate slots for the next 24 hours
        slot_start = start_time + timedelta(hours=i)
        slot_end = slot_start + timedelta(hours=1)
        slots.append({"start_time": slot_start, "end_time": slot_end})
        
    return slots

app.include_router(features_router, prefix="/api/v1", tags=["Special Features"])

# ==============================================================================
# DATA SEEDING UTILITY
# ==============================================================================
def seed_data(db: Session):
    """Seeds the database with initial products and meal kits."""
    products_data = [
        # Pantry Staples
        Product(name="Organic Milk", description="1 Gallon, Whole Milk", price=4.50, category="Dairy", tags="Organic", stock_quantity=100),
        Product(name="Sourdough Bread", description="Freshly baked loaf", price=5.00, category="Bakery", tags="Vegan", stock_quantity=50),
        Product(name="Free-Range Eggs", description="One dozen large eggs", price=3.75, category="Dairy", tags="Organic", stock_quantity=80),
        Product(name="Artisan Coffee Beans", description="12oz bag, whole bean", price=12.99, category="Pantry", tags="Organic", stock_quantity=60),
        # Tuscan Chicken Ingredients
        Product(name="Chicken Breast", description="1 lb boneless, skinless", price=8.99, category="Meat", tags="Gluten-Free", stock_quantity=40),
        Product(name="Heavy Cream", description="1 pint", price=3.20, category="Dairy", tags="", stock_quantity=30),
        Product(name="Spinach", description="5 oz bag, pre-washed", price=2.50, category="Produce", tags="Vegan,Organic,Gluten-Free", stock_quantity=70),
        Product(name="Sun-Dried Tomatoes", description="8 oz jar in oil", price=4.50, category="Pantry", tags="Vegan,Gluten-Free", stock_quantity=50),
        # Taco Tuesday Ingredients
        Product(name="Ground Beef", description="1 lb, 85% lean", price=7.50, category="Meat", tags="Gluten-Free", stock_quantity=45),
        Product(name="Corn Tortillas", description="30 count", price=2.80, category="Bakery", tags="Vegan,Gluten-Free", stock_quantity=90),
        Product(name="Shredded Cheddar Cheese", description="8 oz bag", price=3.50, category="Dairy", tags="", stock_quantity=65),
        Product(name="Salsa", description="16 oz jar, medium heat", price=3.00, category="Pantry", tags="Vegan,Gluten-Free", stock_quantity=75),
        # Pasta Ingredients
        Product(name="Tomatoes", description="2 lbs, on the vine", price=4.00, category="Produce", tags="Vegan,Organic,Gluten-Free", stock_quantity=100),
        Product(name="Pasta", description="1 lb, spaghetti", price=1.50, category="Pantry", tags="Vegan", stock_quantity=200),
        Product(name="Basil", description="1 bunch, fresh", price=2.00, category="Produce", tags="Vegan,Organic,Gluten-Free", stock_quantity=40),
        Product(name="Parmesan Cheese", description="8 oz wedge", price=6.00, category="Dairy", tags="", stock_quantity=30),
    ]
    db.add_all(products_data)
    db.commit()

    # Create Meal Kits
    tuscan_chicken_kit = MealKit(name="30-Minute Tuscan Chicken", description="All you need for a creamy, delicious Tuscan chicken dinner.", price=20.00, image_url="/images/tuscan_chicken.jpg")
    taco_kit = MealKit(name="Taco Tuesday Kit", description="Everything for a classic taco night. Just add your favorite toppings!", price=18.00, image_url="/images/taco_kit.jpg")
    db.add_all([tuscan_chicken_kit, taco_kit])
    db.commit()

    # Link products to meal kits
    product_map = {p.name: p.id for p in products_data}
    tuscan_chicken_items = [
        MealKitItem(meal_kit_id=tuscan_chicken_kit.id, product_id=product_map["Chicken Breast"], quantity=1),
        MealKitItem(meal_kit_id=tuscan_chicken_kit.id, product_id=product_map["Heavy Cream"], quantity=1),
        MealKitItem(meal_kit_id=tuscan_chicken_kit.id, product_id=product_map["Spinach"], quantity=1),
        MealKitItem(meal_kit_id=tuscan_chicken_kit.id, product_id=product_map["Sun-Dried Tomatoes"], quantity=1),
    ]
    taco_items = [
        MealKitItem(meal_kit_id=taco_kit.id, product_id=product_map["Ground Beef"], quantity=1),
        MealKitItem(meal_kit_id=taco_kit.id, product_id=product_map["Corn Tortillas"], quantity=1),
        MealKitItem(meal_kit_id=taco_kit.id, product_id=product_map["Shredded Cheddar Cheese"], quantity=1),
        MealKitItem(meal_kit_id=taco_kit.id, product_id=product_map["Salsa"], quantity=1),
    ]
    db.add_all(tuscan_chicken_items + taco_items)
    db.commit()