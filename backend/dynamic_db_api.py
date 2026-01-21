"""
Dynamic Database API for Generated Applications
Provides universal CRUD operations that any generated app can use
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "altx_db")

# Create router
router = APIRouter(prefix="/api/db", tags=["Dynamic Database"])


class DynamicDB:
    """Dynamic MongoDB operations for any collection"""
    
    _client = None
    _db = None
    
    @classmethod
    def get_database(cls):
        if cls._db is None:
            cls._client = MongoClient(MONGODB_URL)
            cls._db = cls._client[DATABASE_NAME]
        return cls._db
    
    @classmethod
    def get_collection(cls, project_name: str, collection_name: str):
        """Get a project-specific collection"""
        db = cls.get_database()
        # Prefix collection with project name for isolation
        full_collection_name = f"{project_name}_{collection_name}"
        return db[full_collection_name]


class CreateItemRequest(BaseModel):
    """Request model for creating an item"""
    data: Dict[str, Any]


class UpdateItemRequest(BaseModel):
    """Request model for updating an item"""
    data: Dict[str, Any]


class QueryRequest(BaseModel):
    """Request model for querying items"""
    filter: Optional[Dict[str, Any]] = {}
    sort: Optional[Dict[str, int]] = None
    limit: Optional[int] = 100
    skip: Optional[int] = 0


def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [serialize_doc(item) if isinstance(item, dict) else 
                          str(item) if isinstance(item, ObjectId) else item 
                          for item in value]
        else:
            result[key] = value
    return result


# ==================== CRUD ENDPOINTS ====================

@router.post("/{project_name}/{collection}")
async def create_item(
    project_name: str,
    collection: str,
    request: CreateItemRequest
):
    """Create a new item in a collection"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        # Add timestamps
        data = request.data.copy()
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        
        result = coll.insert_one(data)
        data["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "data": serialize_doc(data),
            "message": f"Created item in {collection}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_name}/{collection}")
async def get_items(
    project_name: str,
    collection: str,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    sort_by: Optional[str] = None,
    sort_order: int = Query(-1, ge=-1, le=1)
):
    """Get all items from a collection with pagination"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        cursor = coll.find()
        
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)
        else:
            cursor = cursor.sort("created_at", DESCENDING)
        
        cursor = cursor.skip(skip).limit(limit)
        
        items = [serialize_doc(doc) for doc in cursor]
        total = coll.count_documents({})
        
        return {
            "success": True,
            "data": items,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_name}/{collection}/{item_id}")
async def get_item(
    project_name: str,
    collection: str,
    item_id: str
):
    """Get a single item by ID"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        try:
            doc = coll.find_one({"_id": ObjectId(item_id)})
        except InvalidId:
            # Try finding by string ID field
            doc = coll.find_one({"id": item_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {
            "success": True,
            "data": serialize_doc(doc)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_name}/{collection}/{item_id}")
async def update_item(
    project_name: str,
    collection: str,
    item_id: str,
    request: UpdateItemRequest
):
    """Update an item by ID"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        # Add updated timestamp
        data = request.data.copy()
        data["updated_at"] = datetime.utcnow()
        
        try:
            result = coll.update_one(
                {"_id": ObjectId(item_id)},
                {"$set": data}
            )
        except InvalidId:
            result = coll.update_one(
                {"id": item_id},
                {"$set": data}
            )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get updated document
        try:
            doc = coll.find_one({"_id": ObjectId(item_id)})
        except InvalidId:
            doc = coll.find_one({"id": item_id})
        
        return {
            "success": True,
            "data": serialize_doc(doc),
            "message": "Item updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_name}/{collection}/{item_id}")
async def delete_item(
    project_name: str,
    collection: str,
    item_id: str
):
    """Delete an item by ID"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        try:
            result = coll.delete_one({"_id": ObjectId(item_id)})
        except InvalidId:
            result = coll.delete_one({"id": item_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {
            "success": True,
            "message": "Item deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_name}/{collection}/query")
async def query_items(
    project_name: str,
    collection: str,
    request: QueryRequest
):
    """Query items with filters"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        cursor = coll.find(request.filter or {})
        
        if request.sort:
            sort_list = [(k, v) for k, v in request.sort.items()]
            cursor = cursor.sort(sort_list)
        
        cursor = cursor.skip(request.skip or 0).limit(request.limit or 100)
        
        items = [serialize_doc(doc) for doc in cursor]
        total = coll.count_documents(request.filter or {})
        
        return {
            "success": True,
            "data": items,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_name}/{collection}/bulk")
async def bulk_create(
    project_name: str,
    collection: str,
    items: List[Dict[str, Any]]
):
    """Bulk create items"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        now = datetime.utcnow()
        for item in items:
            item["created_at"] = now
            item["updated_at"] = now
        
        result = coll.insert_many(items)
        
        return {
            "success": True,
            "inserted_count": len(result.inserted_ids),
            "inserted_ids": [str(id) for id in result.inserted_ids]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_name}/{collection}/search")
async def search_items(
    project_name: str,
    collection: str,
    q: str = Query(..., min_length=1),
    fields: str = Query("name,title,description", description="Comma-separated fields to search")
):
    """Search items by text in specified fields"""
    try:
        coll = DynamicDB.get_collection(project_name, collection)
        
        search_fields = [f.strip() for f in fields.split(",")]
        
        # Build OR query for text search
        or_conditions = []
        for field in search_fields:
            or_conditions.append({field: {"$regex": q, "$options": "i"}})
        
        cursor = coll.find({"$or": or_conditions}).limit(50)
        items = [serialize_doc(doc) for doc in cursor]
        
        return {
            "success": True,
            "data": items,
            "query": q,
            "searched_fields": search_fields
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SPECIALIZED ENDPOINTS ====================

@router.get("/{project_name}/products")
async def get_products(
    project_name: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    limit: int = 50
):
    """Get products with filters (e-commerce helper)"""
    try:
        coll = DynamicDB.get_collection(project_name, "products")
        
        filter_query = {}
        if category:
            filter_query["category"] = category
        if min_price is not None:
            filter_query["price"] = {"$gte": min_price}
        if max_price is not None:
            filter_query.setdefault("price", {})["$lte"] = max_price
        if in_stock is not None:
            filter_query["in_stock"] = in_stock
        
        cursor = coll.find(filter_query).limit(limit)
        products = [serialize_doc(doc) for doc in cursor]
        
        return {
            "success": True,
            "data": products,
            "total": len(products)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_name}/orders")
async def create_order(
    project_name: str,
    order_data: Dict[str, Any]
):
    """Create an order (e-commerce helper)"""
    try:
        coll = DynamicDB.get_collection(project_name, "orders")
        
        order = {
            **order_data,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Calculate total if items provided
        if "items" in order:
            order["total"] = sum(
                item.get("price", 0) * item.get("quantity", 1) 
                for item in order["items"]
            )
        
        result = coll.insert_one(order)
        order["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "data": serialize_doc(order),
            "message": "Order created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_name}/orders/{user_id}")
async def get_user_orders(
    project_name: str,
    user_id: str
):
    """Get orders for a user"""
    try:
        coll = DynamicDB.get_collection(project_name, "orders")
        
        cursor = coll.find({"user_id": user_id}).sort("created_at", DESCENDING)
        orders = [serialize_doc(doc) for doc in cursor]
        
        return {
            "success": True,
            "data": orders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATS ENDPOINT ====================

@router.get("/{project_name}/stats")
async def get_project_stats(project_name: str):
    """Get statistics for a project's data"""
    try:
        db = DynamicDB.get_database()
        
        # Find all collections for this project
        all_collections = db.list_collection_names()
        project_collections = [c for c in all_collections if c.startswith(f"{project_name}_")]
        
        stats = {}
        for coll_name in project_collections:
            short_name = coll_name.replace(f"{project_name}_", "")
            stats[short_name] = db[coll_name].count_documents({})
        
        return {
            "success": True,
            "project": project_name,
            "collections": stats,
            "total_documents": sum(stats.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
