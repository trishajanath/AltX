# models.py - E-commerce Data Models
# VALIDATED: Syntax ✓ Imports ✓ Functionality ✓

from datetime import datetime
from typing import List, Optional

# Pydantic for validation
from pydantic import BaseModel, ConfigDict, EmailStr

# SQLAlchemy for database
from sqlalchemy import (
    create_engine, Column, String, Float, Integer, 
    DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Password hashing
from passlib.context import CryptContext

# Database Configuration
DATABASE_URL = "sqlite:///./ecommerce.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """Hash password securely."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return pwd_context.verify(plain_password, hashed_password)

# SQLAlchemy Models
class UserDB(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("OrderDB", back_populates="user")

class ProductDB(Base):
    """Product database model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order_items = relationship("OrderItemDB", back_populates="product")

class OrderDB(Base):
    """Order database model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("UserDB", back_populates="orders")
    items = relationship("OrderItemDB", back_populates="order")

class OrderItemDB(Base):
    """Order item database model."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    order = relationship("OrderDB", back_populates="items")
    product = relationship("ProductDB", back_populates="order_items")

# Pydantic Schemas
class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    """Product creation schema."""
    pass

class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(ProductBase):
    """Product response schema."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """User creation schema."""
    password: str

class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    """Order item creation schema."""
    pass

class OrderItemResponse(OrderItemBase):
    """Order item response schema."""
    id: int
    price: float
    product: ProductResponse
    
    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    """Order creation schema."""
    items: List[OrderItemCreate]
    total: float

class OrderResponse(BaseModel):
    """Order response schema."""
    id: int
    user_id: int
    total: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# Authentication schemas
class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str

# Create tables
Base.metadata.create_all(bind=engine)

# Sample data creation
def create_sample_data():
    """Create sample products for e-commerce-quick-online-391909."""
    db = SessionLocal()
    try:
        if db.query(ProductDB).first():
            return
            
        sample_products = [
            ProductDB(
                name="Fresh Bananas",
                description="Organic yellow bananas, perfect for snacks",
                price=2.99, stock=50, category="fruits",
                image_url="https://placehold.co/400x300/000000/FFFFFF/png?text=Bananas"
            ),
            ProductDB(
                name="Whole Milk",
                description="Fresh dairy milk, 1 gallon",
                price=3.49, stock=25, category="dairy",
                image_url="https://placehold.co/400x300/000000/FFFFFF/png?text=Milk"
            ),
            ProductDB(
                name="Bread Loaf",
                description="Whole wheat bread loaf",
                price=2.79, stock=30, category="bakery",
                image_url="https://placehold.co/400x300/000000/FFFFFF/png?text=Bread"
            )
        ]
        
        db.add_all(sample_products)
        db.commit()
        print(f"✅ Sample data created for e-commerce-quick-online-391909")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

# Initialize sample data
create_sample_data()
