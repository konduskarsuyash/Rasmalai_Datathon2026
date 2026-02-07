import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import connect_to_mongo, close_mongo_connection, get_users_collection

async def test_mongodb():
    """Test MongoDB connection and list users"""
    print("🔍 Testing MongoDB Connection...\n")
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("✅ Connected to MongoDB successfully!\n")
        
        # Get users collection
        users_collection = get_users_collection()
        
        # Count users
        user_count = await users_collection.count_documents({})
        print(f"📊 Total users in database: {user_count}\n")
        
        # List all users
        if user_count > 0:
            print("👥 Users in database:")
            print("-" * 80)
            async for user in users_collection.find():
                print(f"ID: {user.get('_id')}")
                print(f"Clerk ID: {user.get('clerk_id')}")
                print(f"Email: {user.get('email')}")
                print(f"Name: {user.get('full_name', 'N/A')}")
                print(f"Created: {user.get('created_at')}")
                print("-" * 80)
        else:
            print("ℹ️  No users found in database yet.")
            print("   Users will be automatically created when they first log in.")
        
        # Close connection
        await close_mongo_connection()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mongodb())
