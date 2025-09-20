from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["main"])

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

# In-memory storage (replace with database in production)
items_db = []
next_id = 1

@router.get("/items", response_model=List[ItemResponse])
async def get_items():
    """Get all items"""
    return items_db

@router.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """Create a new item"""
    global next_id
    new_item = ItemResponse(
        id=next_id,
        title=item.title,
        description=item.description
    )
    items_db.append(new_item)
    next_id += 1
    return new_item

@router.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    """Get item by ID"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete item by ID"""
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": "Item deleted successfully"}