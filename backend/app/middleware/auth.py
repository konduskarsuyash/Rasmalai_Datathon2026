from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer(auto_error=False)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_API_URL = "https://api.clerk.com/v1"

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify Clerk JWT token
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="No authentication credentials provided")
    
    token = credentials.credentials
    
    try:
        # Verify token with Clerk API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CLERK_API_URL}/sessions/verify",
                headers={
                    "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                    "Clerk-Session-Token": token
                }
            )
            
            if response.status_code == 200:
                session_data = response.json()
                return session_data
            else:
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

async def get_current_user(session_data: dict = Depends(verify_clerk_token)):
    """
    Get current authenticated user from session data
    """
    user_id = session_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not found in session")
    
    return {
        "user_id": user_id,
        "session_id": session_data.get("id"),
        "session_data": session_data
    }

# Optional: For routes that don't require authentication
async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """
    Get user if authenticated, otherwise return None.
    Returns same shape as get_current_user: {user_id, session_id, session_data}.
    """
    if not credentials:
        return None
    try:
        session_data = await verify_clerk_token(credentials)
        user_id = session_data.get("user_id") or session_data.get("sub")
        if not user_id:
            return None
        return {
            "user_id": user_id,
            "session_id": session_data.get("id"),
            "session_data": session_data,
        }
    except HTTPException:
        raise
    except Exception:
        return None
