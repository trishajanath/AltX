```python
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime

# Import models and in-memory "database"
from .models import (
    Product, ProductCreate, ProductUpdate, ClothingCategory, ClothingSize,
    Seller, SellerCreate,
    Order, OrderCreate
)

router = APIRouter()

#  In-Memory Data Store (for demonstration purposes) 
# In a real application, this would be a database (e.g., PostgreSQL with SQLAlchemy)
db = {
    "sellers": {},
    "products": {},
    "orders": {}
}

# Pre-populate with some data for demonstration
def populate_initial_data():
    seller1_id = uuid.uuid4()
    seller2_id = uuid.uuid4()
    
    db["sellers"][seller1_id] = Seller(
        id=seller1_id,
        username="vintage_vibes",
        email="contact@vintagevibes.com",
        store_name="Vintage Vibes Boutique",
        created_at=datetime.utcnow()
    )
    db["sellers"][seller2_id] = Seller(
        id=seller2_id,
        username="modern_threads",
        email="support@modernthreads.com",
        store_name="Modern Threads Co.",
        created_at=datetime.utcnow()
    )

    product1_id = uuid.uuid4()
    product2_id = uuid.uuid4()
    product3_id = uuid.uuid4()

    db["products"][product1_id] = Product(
        id=product1_id,
        name="Classic Denim Jacket",
        description="A timeless denim jacket perfect for any season.",
        price=79.99,
        category=ClothingCategory.JACKET,
        available_sizes=[ClothingSize.S, ClothingSize.M, ClothingSize.L],
        seller_id=seller1_id,
        created_at=datetime.utcnow()
    )
    db["products"][product2_id] = Product(
        id=product2_id,
        name="Organic Cotton T-Shirt",
        description="Soft, breathable, and eco-friendly.",
        price=24.99,
        category=ClothingCategory.TSHIRT,
        available_sizes=[ClothingSize.XS, ClothingSize.S, ClothingSize.M, ClothingSize.L, ClothingSize.XL],
        seller_id=seller2_id,
        created_at=datetime.utcnow()
    )
    db["products"][product3_id] = Product(
        id=product3_id,
        name="High-Waisted Skinny Jeans",
        description="Flattering and comfortable for everyday wear.",
        price=59.99,
        category=ClothingCategory.JEANS,
        available_sizes=[ClothingSize.S, ClothingSize.M],
        seller_id=seller2_id,
        created_at=datetime.utcnow()
    )

populate_initial_data()

#  Seller Endpoints 

@router.post("/sellers", response_model=Seller, status_code=status.HTTP_201_CREATED, tags=["Sellers"])
def create_seller(seller_in: SellerCreate):
    """
    Register a new seller.
    """
    # In a real app, you'd check for unique username/email
    for existing_seller in db["sellers"].values():
        if existing_seller.email == seller_in.email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seller with this email already exists.")
    
    new_seller = Seller(**seller_in.model_dump())
    db["sellers"][new_seller.id] = new_seller
    return new_seller

@router.get("/sellers/{seller_id}", response_model=Seller, tags=["Sellers"])
def get_seller(seller_id: UUID):
    """
    Retrieve details for a specific seller.
    """
    seller = db["sellers"].get(seller_id)
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found.")
    return seller

#  Product Endpoints 

@router.post("/products", response_model=Product, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(product_in: ProductCreate):
    """
    Create a new product listing. The `seller_id` must correspond to an existing seller.
    """
    if product_in.seller_id not in db["sellers"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Seller with id {product_in.seller_id} not found.")

    new_product = Product(**product_in.model_dump())
    db["products"][new_product.id] = new_product
    return new_product

@router.get("/products", response_model=List[Product], tags=["Products"])
def list_products(
    category: Optional[ClothingCategory] = Query(None, description="Filter products by category."),
    size: Optional[ClothingSize] = Query(None, description="Filter products by available size."),
    max_price: Optional[float] = Query(None, gt=0, description="Filter products by a maximum price.")
):
    """
    List all available products with optional filtering.
    - Filter by `category` (e.g., 'T-Shirt', 'Jeans').
    - Filter by `size` (e.g., 'S', 'M', 'L').
    - Filter by `max_price`.
    """
    products = list(db["products"].values())
    
    if category:
        products = [p for p in products if p.category == category]
    if size:
        products = [p for p in products if size in p.available_sizes]
    if max_price:
        products = [p for p in products if p.price <= max_price]
        
    return products

@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
def get_product(product_id: UUID):
    """
    Retrieve a single product by its ID.
    """
    product = db["products"].get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product

@router.put("/products/{product_id}", response_model=Product, tags=["Products"])
def update_product(product_id: UUID, product_update: ProductUpdate):
    """
    Update an existing product's details.
    """
    product = db["products"].get(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db["products"][product_id] = product
    return product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
def delete_product(product_id: UUID):
    """
    Delete a product listing.
    """
    if product_id not in db["products"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    
    del db["products"][product_id]
    return

@router.get("/sellers/{seller_id}/products", response_model=List[Product], tags=["Sellers", "Products"])
def get_products_by_seller(seller_id: UUID):
    """
    Get all products listed by a specific seller.
    """
    if seller_id not in db["sellers"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found.")
    
    return [p for p in db["products"].values() if p.seller_id == seller_id]

#  Order Endpoints 

@router.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(order_in: OrderCreate):
    """
    Place a new order for one or more products.
    """
    total_price = 0.0
    
    # Validate products and calculate total price
    for item in order_in.items:
        product = db["products"].get(item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} not found in order."
            )
        total_price += product.price * item.quantity
        
    new_order = Order(
        customer_email=order_in.customer_email,
        items=order_in.items,
        total_price=round(total_price, 2)
    )
    
    db["orders"][new_order.id] = new_order
    return new_order

@router.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
def get_order(order_id: UUID):
    """
    Retrieve details of a specific order.
    """
    order = db["orders"].get(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_Found, detail="Order not found.")
    return order
```