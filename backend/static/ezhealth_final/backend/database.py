from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Depends
from urllib.parse import quote_plus

# MongoDB connection settings
username = quote_plus("admin1")
password = quote_plus("admin@123$#")
cluster_url = "ezhealth.phjf1.mongodb.net"

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority&appName=Ezhealth"

DB_NAME = "EzHealth"

# Configure MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def get_db():
    try:
        await client.admin.command('ping')
        return db
    except Exception as e:
        print(f"Database connection error: {e}")
        raise