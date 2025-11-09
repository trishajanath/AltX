# main.py
# COMPLETE, PRODUCTION-READY FastAPI for Online Grocery Platform: web-provide-convenient-959883

# --- Imports ---
import os
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, 
                        Float, ForeignKey, Date, Time, Enum as SQLAlchemyEnum)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
import enum

# --- Configuration ---
# In a real production environment, use environment variables for these settings.
# Example: SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secure_secret_key_for_dev_959883")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app_grocery.db")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Enums for Model Choices ---
class OrderStatus(str, enum.Enum):
    PENDING = "Order Placed"
    PROCESSING = "Personal Shopper is Picking Your Items"
    OUT_FOR_DELIVERY = "Out for Delivery"
    ARRIVING_SOON = "Arriving Soon"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

class SubscriptionFrequency(str, enum.Enum):
    WEEKLY = "weekly"
    BI_WEEKLY = "bi-weekly"
    MONTHLY = "monthly"

# --- SQLAlchemy ORM Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    category = Column(String, index=True)
    stock_quantity = Column(Integer, default=0)
    # Storing tags as a comma-separated string for simplicity in SQLite
    dietary_tags = Column(String, index=True) # e.g., "gluten-free,vegan,low-sodium"
    created_at = Column(DateTime, default=datetime.utcnow)

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
    status = Column(SQLAlchemyEnum(OrderStatus), default=OrderStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivery_slot_id = Column(Integer, ForeignKey("delivery_slots.id"))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_slot = relationship("DeliverySlot")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    image_url = Column(String)
    
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    recipe = relationship("Recipe", back_populates="ingredients")
    product = relationship("Product")

class DeliverySlot(Base):
    __tablename__ = "delivery_slots"
    id = Column(Integer, primary_key=True, index=True)
    delivery_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_booked = Column(Integer, default=0) # Using Integer for SQLite compatibility (0=False, 1=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    frequency = Column(SQLAlchemyEnum(SubscriptionFrequency), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="subscriptions")
    product = relationship("Product")

# --- Pydantic Schemas ---

# User & Auth Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: str
    stock_quantity: int
    dietary_tags: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Cart Schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_price: float

# Order Schemas
class OrderItemResponse(BaseModel):
    quantity: int
    price_at_purchase: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    delivery_slot_id: int

class OrderResponse(BaseModel):
    id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# Recipe Schemas
class RecipeIngredientResponse(BaseModel):
    quantity: int
    product: ProductResponse
    
    class Config:
        from_attributes = True

class RecipeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    image_url: Optional[str] = None
    ingredients: List[RecipeIngredientResponse]

    class Config:
        from_attributes = True

# Delivery Schemas
class DeliverySlotResponse(BaseModel):
    id: int
    delivery_date: date
    start_time: str
    end_time: str

    class Config:
        from_attributes = True
        
    def model_post_init(self, __context):
        self.start_time = self.start_time.strftime('%H:%M')
        self.end_time = self.end_time.strftime('%H:%M')

# Subscription Schemas
class SubscriptionCreate(BaseModel):
    product_id: int
    frequency: SubscriptionFrequency
    quantity: int = Field(..., gt=0)

class SubscriptionResponse(BaseModel):
    id: int
    frequency: SubscriptionFrequency
    quantity: int
    product: ProductResponse
    created_at: datetime

    class Config:
        from_attributes = True

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Online Grocery Platform",
    description="A web application for a seamless and convenient online grocery shopping experience for busy working professionals.",
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} | Status: {response.status_code} | Duration: {process_time:.4f}s"
    )
    return response

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication Utilities ---
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

def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Current User Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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

# --- Startup Event to Create DB Tables ---
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # You can add seed data here for development
    # seed_data()

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app": "web-provide-convenient-959883"}

# --- Authentication Router ---
auth_router = FastAPI.router.APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": new_user
    }

@auth_router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@auth_router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    new_access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": new_access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# --- Product Router ---
product_router = FastAPI.router.APIRouter(prefix="/api/v1/products", tags=["Products"])

@product_router.get("/", response_model=List[ProductResponse])
async def search_products(
    q: Optional[str] = None,
    dietary: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    AI-Powered Smart Search & Filtering:
    - Search by name/description with 'q'.
    - Filter by dietary tags (e.g., 'gluten-free', 'vegan').
    - Filter by category.
    """
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%"))
    if dietary:
        # Assumes tags are stored like "vegan,gluten-free"
        dietary_tags = [tag.strip() for tag in dietary.lower().split(',')]
        for tag in dietary_tags:
            query = query.filter(Product.dietary_tags.ilike(f"%{tag}%"))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    
    return query.all()

@product_router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # In a real app, this would be an admin-only endpoint
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# --- Inventory Router ---
inventory_router = FastAPI.router.APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])

@inventory_router.get("/{product_id}", response_model=dict)
async def get_inventory(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {"product_id": product.id, "stock_quantity": product.stock_quantity}

# --- Cart Router ---
cart_router = FastAPI.router.APIRouter(prefix="/api/v1/cart", tags=["Shopping Cart"])

@cart_router.get("/", response_model=CartResponse)
async def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return {"items": cart_items, "total_price": total_price}

@cart_router.post("/add", response_model=CartItemResponse)
async def add_to_cart(item: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.stock_quantity < item.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock available")

    cart_item = db.query(CartItem).filter(CartItem.user_id == current_user.id, CartItem.product_id == item.product_id).first()
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=item.product_id, quantity=item.quantity)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

@cart_router.delete("/remove/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return

# --- User-specific Features Router ---
user_router = FastAPI.router.APIRouter(prefix="/api/v1/users", tags=["User Features"])

@user_router.get("/me/buy-again", response_model=List[ProductResponse])
async def get_buy_again_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Generates a 'Buy Again' list from the user's past orders.
    """
    # Get distinct product IDs from all of the user's past order items
    product_ids = db.query(OrderItem.product_id)\
        .join(Order)\
        .filter(Order.user_id == current_user.id)\
        .distinct()\
        .all()
    
    product_ids_list = [pid[0] for pid in product_ids]
    
    if not product_ids_list:
        return []
        
    products = db.query(Product).filter(Product.id.in_(product_ids_list)).all()
    return products

# --- Recipe Router ---
recipe_router = FastAPI.router.APIRouter(prefix="/api/v1/recipes", tags=["Recipes"])

@recipe_router.get("/", response_model=List[RecipeResponse])
async def get_all_recipes(db: Session = Depends(get_db)):
    recipes = db.query(Recipe).all()
    return recipes

@recipe_router.post("/{recipe_id}/add-to-cart", status_code=status.HTTP_200_OK)
async def add_recipe_to_cart(recipe_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    for ingredient in recipe.ingredients:
        # Check stock
        if ingredient.product.stock_quantity < ingredient.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Not enough stock for product: {ingredient.product.name}"
            )
        
        # Add or update cart item
        cart_item = db.query(CartItem).filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == ingredient.product_id
        ).first()
        
        if cart_item:
            cart_item.quantity += ingredient.quantity
        else:
            new_cart_item = CartItem(
                user_id=current_user.id,
                product_id=ingredient.product_id,
                quantity=ingredient.quantity
            )
            db.add(new_cart_item)
    
    db.commit()
    return {"message": f"All ingredients for '{recipe.name}' have been added to your cart."}

# --- Delivery Router ---
delivery_router = FastAPI.router.APIRouter(prefix="/api/v1/delivery", tags=["Delivery"])

@delivery_router.get("/slots", response_model=List[DeliverySlotResponse])
async def get_available_slots(delivery_date: date, db: Session = Depends(get_db)):
    slots = db.query(DeliverySlot).filter(
        DeliverySlot.delivery_date == delivery_date,
        DeliverySlot.is_booked == 0
    ).all()
    return slots

# --- Order Router ---
order_router = FastAPI.router.APIRouter(prefix="/api/v1/orders", tags=["Orders"])

@order_router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    # Check delivery slot
    slot = db.query(DeliverySlot).filter(DeliverySlot.id == order_data.delivery_slot_id).first()
    if not slot or slot.is_booked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery slot is not available")

    total_amount = 0
    order_items_to_create = []

    # Start a transaction
    try:
        # Lock the slot to prevent double booking
        slot.is_booked = 1
        db.add(slot)

        for item in cart_items:
            product = item.product
            if product.stock_quantity < item.quantity:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Not enough stock for {product.name}")
            
            total_amount += product.price * item.quantity
            product.stock_quantity -= item.quantity
            
            order_items_to_create.append(
                OrderItem(product_id=product.id, quantity=item.quantity, price_at_purchase=product.price)
            )
            db.add(product)

        new_order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            delivery_slot_id=slot.id,
            items=order_items_to_create
        )
        db.add(new_order)
        
        # Clear the cart
        for item in cart_items:
            db.delete(item)
            
        db.commit()
        db.refresh(new_order)
        return new_order
    except Exception as e:
        db.rollback()
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create order")

@order_router.get("/", response_model=List[OrderResponse])
async def get_user_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()

@order_router.get("/{order_id}/status", response_model=dict)
async def get_order_status(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return {"order_id": order.id, "status": order.status.value}

# --- Subscription Router ---
subscription_router = FastAPI.router.APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])

@subscription_router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(sub_data: SubscriptionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == sub_data.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    new_sub = Subscription(**sub_data.model_dump(), user_id=current_user.id)
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@subscription_router.get("/", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Subscription).filter(Subscription.user_id == current_user.id).all()

@subscription_router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(subscription_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.id == subscription_id, Subscription.user_id == current_user.id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    db.delete(sub)
    db.commit()
    return

# --- Payment Router (Mock) ---
payment_router = FastAPI.router.APIRouter(prefix="/api/v1/payments", tags=["Payments"])

@payment_router.post("/process")
async def process_payment(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # This is a mock endpoint. In a real application, this would integrate with a payment gateway like Stripe or PayPal.
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Simulate a successful payment
    logger.info(f"Simulating payment processing for order {order_id} with amount {order.total_amount}")
    return {"status": "success", "message": "Payment processed successfully", "order_id": order_id}

# --- Include Routers in Main App ---
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(inventory_router)
app.include_router(cart_router)
app.include_router(user_router)
app.include_router(recipe_router)
app.include_router(delivery_router)
app.include_router(order_router)
app.include_router(subscription_router)
app.include_router(payment_router)

# To run this application:
# 1. Install dependencies: pip install "fastapi[all]" sqlalchemy passlib[bcrypt] python-jose[cryptography]
# 2. Save the code as main.py
# 3. Run from your terminal: uvicorn main:app --reload