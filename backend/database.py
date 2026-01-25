"""
MongoDB Database Configuration and Models
Handles user authentication and storage
"""
import os
from datetime import datetime
from typing import Optional
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "altx_db")

class MongoDB:
    """MongoDB connection manager"""
    
    _client = None
    _db = None
    
    @classmethod
    def get_database(cls):
        """Get database instance (singleton pattern)"""
        if cls._db is None:
            cls._client = MongoClient(MONGODB_URL)
            cls._db = cls._client[DATABASE_NAME]
            cls._initialize_indexes()
        return cls._db
    
    @classmethod
    def _initialize_indexes(cls):
        """Create database indexes"""
        db = cls._db
        
        # Users collection indexes
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)
        
        # Projects collection indexes (optional, for future use)
        db.projects.create_index([("user_id", ASCENDING)])
        db.projects.create_index([("project_slug", ASCENDING)])
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None


class UserModel:
    """User database operations"""
    
    def __init__(self):
        self.db = MongoDB.get_database()
        self.collection = self.db.users
    
    def create_user(self, email: str, username: str, hashed_password: str) -> dict:
        """Create a new user"""
        user_data = {
            "email": email.lower(),
            "username": username,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "is_verified": False,
            # Stripe Connect fields (for payment-enabled apps)
            "stripe_connect": {
                "account_id": None,
                "status": "not_connected",
                "charges_enabled": False,
                "payouts_enabled": False,
                "details_submitted": False,
                "default_currency": None,
                "country": None,
                "connected_at": None
            }
        }
        
        try:
            result = self.collection.insert_one(user_data)
            user_data["_id"] = str(result.inserted_id)
            return user_data
        except DuplicateKeyError as e:
            if "email" in str(e):
                raise ValueError("Email already registered")
            elif "username" in str(e):
                raise ValueError("Username already taken")
            raise ValueError("User already exists")
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        user = self.collection.find_one({"email": email.lower()})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        user = self.collection.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        from bson import ObjectId
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except:
            return None
    
    def update_user(self, user_id: str, update_data: dict) -> bool:
        """Update user data"""
        from bson import ObjectId
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except:
            return False
    
    def verify_user(self, user_id: str) -> bool:
        """Mark user as verified"""
        return self.update_user(user_id, {"is_verified": True})
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        return self.update_user(user_id, {"is_active": False})
