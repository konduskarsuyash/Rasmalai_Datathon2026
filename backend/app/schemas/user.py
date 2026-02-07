from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model"""
    clerk_id: str = Field(..., description="Clerk user ID")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User full name")
    organization: Optional[str] = Field(None, description="User organization")
    image_url: Optional[str] = Field(None, description="User profile image URL")

class UserCreate(UserBase):
    """User creation model"""
    pass

class UserSync(BaseModel):
    """User sync model for Clerk integration"""
    clerk_id: str
    email: str
    full_name: Optional[str] = None
    image_url: Optional[str] = None

class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = None
    organization: Optional[str] = None

class User(UserBase):
    """Complete user model"""
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "clerk_id": "user_2...",
                "email": "user@example.com",
                "full_name": "John Doe",
                "organization": "Financial Corp",
                "image_url": "https://...",
                "created_at": "2026-02-07T00:00:00Z",
                "updated_at": "2026-02-07T00:00:00Z"
            }
        }
