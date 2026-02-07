from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.user import User, UserCreate, UserUpdate, UserSync
from ..middleware.auth import get_current_user
from ..config.database import get_users_collection
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/sync", response_model=User, status_code=status.HTTP_201_CREATED)
async def sync_user(user_data: UserSync):
    """
    Sync user from Clerk to MongoDB (create or update)
    This endpoint doesn't require authentication as it's called right after Clerk signup
    """
    users_collection = get_users_collection()
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"clerk_id": user_data.clerk_id})
    
    if existing_user:
        # Update existing user
        update_data = user_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await users_collection.find_one_and_update(
            {"clerk_id": user_data.clerk_id},
            {"$set": update_data},
            return_document=True
        )
        result["_id"] = str(result["_id"])
        return result
    else:
        # Create new user
        user_dict = user_data.model_dump()
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        result = await users_collection.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        return user_dict

@router.get("/", response_model=list[User])
async def list_all_users():
    """
    List all users in MongoDB (for testing/admin purposes)
    """
    users_collection = get_users_collection()
    users = []
    
    async for user in users_collection.find():
        user["_id"] = str(user["_id"])
        users.append(user)
    
    return users

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    users_collection = get_users_collection()
    user = await users_collection.find_one({"clerk_id": current_user["user_id"]})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    return user

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new user record in MongoDB
    """
    users_collection = get_users_collection()
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"clerk_id": user_data.clerk_id})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create user document
    user_dict = user_data.model_dump()
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    result = await users_collection.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    
    return user_dict

@router.put("/me", response_model=User)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user information
    """
    users_collection = get_users_collection()
    
    # Get update fields
    update_data = user_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    result = await users_collection.find_one_and_update(
        {"clerk_id": current_user["user_id"]},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result["_id"] = str(result["_id"])
    return result

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(current_user: dict = Depends(get_current_user)):
    """
    Delete current user account
    """
    users_collection = get_users_collection()
    
    result = await users_collection.delete_one({"clerk_id": current_user["user_id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return None
