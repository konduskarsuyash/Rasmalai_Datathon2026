# Clerk & MongoDB Integration

This project uses **Clerk** for authentication and **MongoDB** for data persistence.

## 🔐 Authentication Setup (Clerk)

### Frontend Configuration

The frontend uses Clerk's React SDK for seamless authentication:

1. **Environment Variables** (`.env`):

   ```env
   VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
   ```

2. **Features**:
   - Protected routes with `ClerkProvider`
   - Beautiful customized sign-in/sign-up pages
   - Social login (Google, GitHub)
   - Automatic redirect to `/playground` after authentication
   - Session management

3. **Usage**:
   - Navigate to `/login` or `/signup`
   - Clerk handles all authentication flows
   - Authenticated users can access `/playground`

### Backend Configuration

The backend validates Clerk JWT tokens:

1. **Environment Variables** (`.env`):

   ```env
   CLERK_SECRET_KEY=your_clerk_secret_key
   CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
   ```

2. **Protected Endpoints**:

   ```python
   from app.middleware.auth import get_current_user

   @router.get("/protected")
   async def protected_route(current_user: dict = Depends(get_current_user)):
       return {"user_id": current_user["user_id"]}
   ```

3. **Authentication Middleware**:
   - Located in `backend/app/middleware/auth.py`
   - Verifies JWT tokens with Clerk API
   - Returns user session data

## 💾 Database Setup (MongoDB)

### Configuration

1. **Environment Variables** (`backend/.env`):

   ```env
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=app
   MONGODB_DB_NAME=finnet_db
   ```

2. **Database Connection**:
   - Managed in `backend/app/config/database.py`
   - Async connection using Motor (AsyncIOMotorClient)
   - Lifecycle events in `main.py` (startup/shutdown)

### Collections

The database includes the following collections:

- **users**: User profiles and settings
- **networks**: Financial network configurations
- **simulations**: Simulation results and history
- **institutions**: Financial institution data

### Database Operations

Example CRUD operations:

```python
from app.config.database import get_users_collection

# Get collection
users = get_users_collection()

# Create
result = await users.insert_one({"clerk_id": "...", "email": "..."})

# Read
user = await users.find_one({"clerk_id": "..."})

# Update
await users.update_one({"clerk_id": "..."}, {"$set": {"name": "..."}})

# Delete
await users.delete_one({"clerk_id": "..."})
```

## 📡 API Endpoints

### User Management

- `GET /api/users/me` - Get current user info
- `POST /api/users/` - Create user profile
- `PUT /api/users/me` - Update user profile
- `DELETE /api/users/me` - Delete user account

All endpoints require authentication via Clerk JWT token.

### Making Authenticated Requests

```javascript
// Frontend Example
import { useAuth } from "@clerk/clerk-react";

function MyComponent() {
  const { getToken } = useAuth();

  const fetchData = async () => {
    const token = await getToken();

    const response = await fetch("http://localhost:8000/api/users/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();
    return data;
  };
}
```

## 🚀 Running the Application

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Access: http://localhost:5174

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Access: http://localhost:8000
API Docs: http://localhost:8000/docs

## 🔒 Security Notes

- **Never commit** `.env` files to version control
- Keep Clerk secret keys private
- Use HTTPS in production
- Regularly rotate API keys
- Implement rate limiting for production

## 📚 Additional Resources

- [Clerk Documentation](https://clerk.com/docs)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Router Documentation](https://reactrouter.com/)
