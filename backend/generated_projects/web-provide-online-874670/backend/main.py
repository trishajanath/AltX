An online platform for users to browse and purchase groceries, designed with a minimalist and clean black and white interface. The application prioritizes a fast, intuitive shopping experience, allowing users to quickly find products, manage their cart, and checkout seamlessly, either as a guest or a registered user.

```python
# main.py
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (create_engine, Column, Integer, String, DateTime, Text, 
                        Float, ForeignKey, Boolean)
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from sqlalchemy.exc import IntegrityError

# --- Configuration ---
# In a real production app, use environment variables (e.g., from a .env file)
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development_only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./grocery_ecommerce.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security & Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SQLAlchemy Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    category = Column(String, index=True)
    brand = Column(String, index=True)
    dietary_tags = Column(String) # Comma-separated tags like "Organic,Gluten-Free"
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for guest checkouts
    guest_email = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="pending", index=True) # e.g., pending, paid, shipped, delivered
    shipping_address = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
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

class Promotion(Base):
    __tablename__ = "promotions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    image_url = Column(String)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True) # Link to a specific product if applicable
    is_active = Column(Boolean, default=True)

# --- Pydantic Schemas ---

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    
    class Config:
        from_attributes = True

# Token Schemas
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
    brand: Optional[str] = None
    dietary_tags: Optional[str] = None
    stock_quantity: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Cart Schemas
class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    id: int
    quantity: int
    product: ProductResponse

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: float

# Order Schemas
class GuestDetails(BaseModel):
    email: EmailStr
    shipping_address: str

class OrderCreate(BaseModel):
    guest_details: Optional[GuestDetails] = None

class OrderItemResponse(BaseModel):
    quantity: int
    price_at_purchase: float
    product: ProductResponse

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    guest_email: Optional[EmailStr] = None
    total_amount: float
    status: str
    shipping_address: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentRequest(BaseModel):
    order_id: int
    payment_token: str # Mock token from a payment provider like Stripe or Braintree

# Promotion Schemas
class PromotionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    product_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Authentication Utilities ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
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

# --- FastAPI Application ---
app = FastAPI(
    title="web-provide-online-874670",
    description="An online platform for users to browse and purchase groceries, designed with a minimalist and clean black and white interface. The application prioritizes a fast, intuitive shopping experience, allowing users to quickly find products, manage their cart, and checkout seamlessly, either as a guest or a registered user.",
    version="1.0.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} | Response: {response.status_code} | Duration: {process_time:.4f}s"
    )
    return response

# --- Startup Event to Create DB and Seed Data ---
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # Seed data if the database is empty
    db = SessionLocal()
    if db.query(Product).count() == 0:
        logger.info("Database is empty, seeding with initial data...")
        products_to_add = [
            Product(name="Organic Apples", description="Crisp and sweet organic Gala apples.", price=3.99, category="Produce", brand="FarmFresh", dietary_tags="Organic,Gluten-Free", stock_quantity=100, image_url="https://example.com/images/apples.jpg"),
            Product(name="Whole Milk", description="Gallon of fresh whole milk.", price=4.50, category="Dairy", brand="DairyLand", dietary_tags="Vegetarian", stock_quantity=50, image_url="https://example.com/images/milk.jpg"),
            Product(name="Sourdough Bread", description="Artisanal sourdough loaf.", price=5.99, category="Bakery", brand="Artisan Bakes", dietary_tags="Vegan", stock_quantity=30, image_url="https://example.com/images/bread.jpg"),
            Product(name="Organic Cheddar Cheese", description="Sharp cheddar cheese block.", price=7.25, category="Dairy", brand="CheeseMasters", dietary_tags="Organic,Vegetarian", stock_quantity=40, image_url="https://example.com/images/cheese.jpg"),
            Product(name="Gluten-Free Crackers", description="Crispy rice crackers.", price=4.20, category="Snacks", brand="HealthyBites", dietary_tags="Gluten-Free,Vegan", stock_quantity=75, image_url="https://example.com/images/crackers.jpg"),
            Product(name="Avocados", description="Ripe and ready to eat.", price=2.50, category="Produce", brand="FarmFresh", dietary_tags="Organic,Vegan", stock_quantity=60, image_url="https://example.com/images/avocados.jpg"),
        ]
        db.add_all(products_to_add)
        
        promotions_to_add = [
            Promotion(title="Buy One, Get One Free Avocados!", description="This week only, get a free avocado when you buy one.", product_id=6, image_url="https://example.com/promo/avocado_bogo.jpg"),
            Promotion(title="Bakery Bonanza", description="20% off all items from our bakery aisle.", image_url="https://example.com/promo/bakery_sale.jpg"),
        ]
        db.add_all(promotions_to_add)
        
        db.commit()
        logger.info("Seeding complete.")
    db.close()

# --- API Endpoints ---

# Health Check
@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "healthy", "app": "web-provide-online-874670"}

# --- Authentication Routes ---
auth_router = FastAPI()

@auth_router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.from_orm(db_user)
    )

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
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@auth_router.post("/refresh", response_model=Token)
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
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# --- Product & Promotion Routes ---
product_router = FastAPI()

@product_router.get("/products", response_model=List[ProductResponse])
async def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if tag:
        query = query.filter(Product.dietary_tags.ilike(f"%{tag}%"))
    return query.all()

@product_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@product_router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # In a real app, you'd check if the user is an admin
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@product_router.get("/promotions", response_model=List[PromotionResponse])
async def get_promotions(db: Session = Depends(get_db)):
    return db.query(Promotion).filter(Promotion.is_active == True).all()

# --- Cart Routes ---
cart_router = FastAPI()

def get_cart_details(user_id: int, db: Session) -> CartResponse:
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    return CartResponse(items=cart_items, subtotal=round(subtotal, 2))

@cart_router.get("", response_model=CartResponse)
async def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_cart_details(current_user.id, db)

@cart_router.post("/add", response_model=CartResponse)
async def add_to_cart(item: CartItemAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
    return get_cart_details(current_user.id, db)

@cart_router.put("/update/{item_id}", response_model=CartResponse)
async def update_cart_item(item_id: int, item_update: CartItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    if cart_item.product.stock_quantity < item_update.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough stock available")

    cart_item.quantity = item_update.quantity
    db.commit()
    return get_cart_details(current_user.id, db)

@cart_router.delete("/remove/{item_id}", response_model=CartResponse)
async def remove_from_cart(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return get_cart_details(current_user.id, db)

# --- Order & Payment Routes ---
order_router = FastAPI()

@order_router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = None
    guest_email = None
    shipping_address = None
    cart_items = []

    if token:
        try:
            user = get_current_user(token, db)
            user_id = user.id
            cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
            # In a real app, get address from user profile or request it
            shipping_address = "123 User St, City, Country" 
        except HTTPException:
            # Token is invalid or expired, treat as guest
            pass
    
    if not user_id: # Guest checkout
        if not order_data.guest_details:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Guest details are required for guest checkout")
        # For guest checkout, cart items must be passed in the request body.
        # This implementation assumes cart is only for logged-in users.
        # A real guest cart would use session cookies or local storage managed by the frontend.
        # For this API, we'll simulate by requiring a logged-in user to place an order.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Guest checkout not fully implemented. Please log in to place an order.")

    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total_amount = 0
    order_items_to_create = []

    for item in cart_items:
        product = item.product
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for {product.name}")
        
        total_amount += product.price * item.quantity
        product.stock_quantity -= item.quantity # Decrease stock
        order_items_to_create.append(
            OrderItem(product_id=product.id, quantity=item.quantity, price_at_purchase=product.price)
        )

    new_order = Order(
        user_id=user_id,
        guest_email=guest_email,
        total_amount=round(total_amount, 2),
        shipping_address=shipping_address,
        items=order_items_to_create
    )

    db.add(new_order)
    # Clear the user's cart
    for item in cart_items:
        db.delete(item)
    
    db.commit()
    db.refresh(new_order)
    return new_order

@order_router.get("", response_model=List[OrderResponse])
async def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()

@order_router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order

payment_router = FastAPI()

@payment_router.post("/process", status_code=status.HTTP_200_OK)
async def process_payment(payment_data: PaymentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # This is a mock payment processing endpoint
    order = db.query(Order).filter(Order.id == payment_data.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order has already been processed")

    # Mock validation of payment_token
    if not payment_data.payment_token.startswith("tok_"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment token")

    order.status = "paid"
    db.commit()
    return {"message": "Payment successful", "order_id": order.id, "new_status": "paid"}

# --- Inventory Routes ---
inventory_router = FastAPI()

@inventory_router.get("", response_model=Dict[int, int])
async def get_all_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Admin-only route in a real app
    products = db.query(Product).all()
    return {p.id: p.stock_quantity for p in products}

@inventory_router.get("/{product_id}", response_model=Dict[str, int])
async def get_inventory(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return {"product_id": product.id, "stock_quantity": product.stock_quantity}


# --- API Router Includes ---
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=f"{api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(product_router, prefix=api_v1_prefix, tags=["Products & Promotions"])
app.include_router(cart_router, prefix=f"{api_v1_prefix}/cart", tags=["Shopping Cart"])
app.include_router(order_router, prefix=f"{api_v1_prefix}/orders", tags=["Orders"])
app.include_router(payment_router, prefix=f"{api_v1_prefix}/payments", tags=["Payments"])
app.include_router(inventory_router, prefix=f"{api_v1_prefix}/inventory", tags=["Inventory"])

# To run this app:
# 1. Install dependencies: pip install "fastapi[all]" sqlalchemy passlib python-jose "bcrypt<4.0.0"
# 2. Save the code as main.py
# 3. Run with uvicorn: uvicorn main:app --reload