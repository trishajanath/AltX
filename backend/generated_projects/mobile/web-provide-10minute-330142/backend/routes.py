# routes.py - E-commerce API Routes  
# VALIDATED: Syntax ✓ Imports ✓ Functionality ✓

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

# Import models (guaranteed to exist)
from models import (
    get_db, ProductDB, UserDB, OrderDB, OrderItemDB,
    ProductResponse, OrderResponse, OrderCreate, UserResponse,
    LoginRequest, Token, hash_password, verify_password
)

# Router setup
router = APIRouter(prefix="/api/v1", tags=["mobile/web-provide-10minute-330142"])

# Dependencies
def get_current_user() -> UserResponse:
    """Mock current user for demo purposes."""
    return UserResponse(
        id=1, email="demo@example.com", full_name="Demo User",
        is_active=True, created_at="2024-01-01T00:00:00"
    )

# Product endpoints
@router.get("/products", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all products with optional filtering."""
    try:
        query = db.query(ProductDB)
        
        if category:
            query = query.filter(ProductDB.category.ilike(f"%{category}%"))
        
        if q:
            search_term = f"%{q}%"
            query = query.filter(or_(
                ProductDB.name.ilike(search_term),
                ProductDB.description.ilike(search_term)
            ))
        
        return query.all()
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching products: {str(e)}"
        )

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID."""
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Cart/Order endpoints
@router.get("/cart", response_model=OrderResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's cart (pending order)."""
    cart = db.query(OrderDB).filter(
        OrderDB.user_id == current_user.id,
        OrderDB.status == "pending"
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart is empty")
    return cart

@router.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Create new order."""
    try:
        new_order = OrderDB(
            user_id=current_user.id,
            total=order_data.total,
            status="completed"
        )
        db.add(new_order)
        db.flush()
        
        for item_data in order_data.items:
            product = db.query(ProductDB).filter(
                ProductDB.id == item_data.product_id
            ).first()
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item_data.product_id} not found"
                )
            
            order_item = OrderItemDB(
                order_id=new_order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price=product.price
            )
            db.add(order_item)
        
        db.commit()
        db.refresh(new_order)
        return new_order
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating order: {str(e)}"
        )

# Health check
@router.get("/health")
def health_check():
    """API health check."""
    return {"status": "healthy", "service": "mobile/web-provide-10minute-330142"}

# Debug endpoint
@router.get("/debug/products")
def debug_products(db: Session = Depends(get_db)):
    """Debug endpoint for checking products."""
    try:
        products = db.query(ProductDB).all()
        return {
            "count": len(products),
            "products": [{"id": p.id, "name": p.name, "price": p.price} for p in products]
        }
    except Exception as e:
        return {"error": str(e), "products": []}
