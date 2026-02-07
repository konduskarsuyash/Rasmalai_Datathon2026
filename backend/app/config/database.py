from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection settings
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "finnet_db")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def get_database():
    """Get database instance"""
    return db.db

async def connect_to_mongo():
    """Connect to MongoDB"""
    print("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(MONGODB_URI)
    db.db = db.client[MONGODB_DB_NAME]
    print("Connected to MongoDB successfully!")

async def close_mongo_connection():
    """Close MongoDB connection"""
    print("Closing MongoDB connection...")
    db.client.close()
    print("MongoDB connection closed!")

# Collections
def get_users_collection():
    """Get users collection"""
    return db.db.users

def get_networks_collection():
    """Get networks collection"""
    return db.db.networks

def get_simulations_collection():
    """Get simulations collection"""
    return db.db.simulations

def get_institutions_collection():
    """Get institutions collection"""
    return db.db.institutions
