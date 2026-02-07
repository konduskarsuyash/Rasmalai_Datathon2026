# User Storage Verification Guide

## ✅ User Auto-Sync Implementation

Users are now **automatically synced to MongoDB** when they authenticate with Clerk!

### How It Works

1. **User signs up/logs in** with Clerk (email, Google, or GitHub)
2. **UserSyncWrapper** component detects authentication
3. **Automatic API call** to `/api/users/sync` endpoint
4. **User record created/updated** in MongoDB with:
   - Clerk ID
   - Email address
   - Full name
   - Profile image URL
   - Timestamps

### Verify Users Are Being Stored

#### Method 1: Using the Backend Test Script

```bash
cd backend
python test_mongodb.py
```

This will show:

- Connection status
- Total number of users
- List of all users with details

#### Method 2: Using the API Endpoint

Visit the API docs and test the endpoint:

```
http://localhost:8000/docs
```

Go to `/api/users/` endpoint and click "Try it out" to see all users.

#### Method 3: Using MongoDB Compass

1. Open MongoDB Compass
2. Connect with your connection string
3. Navigate to: `finnet_db` → `users` collection
4. View all user documents

#### Method 4: Check Browser Console

When you log in, check the browser console (F12):

- You'll see: `✅ User synced to MongoDB: {user data}`
- Or an error message if sync failed

### Test the Flow

1. **Start the backend**:

   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start the frontend** (if not running):

   ```bash
   cd frontend
   npm run dev
   ```

3. **Sign up a new user**:
   - Go to http://localhost:5174/signup
   - Create an account
   - After login, check the console

4. **Verify in database**:
   ```bash
   cd backend
   python test_mongodb.py
   ```

### API Endpoints

- `POST /api/users/sync` - Sync user from Clerk (no auth required)
- `GET /api/users/` - List all users
- `GET /api/users/me` - Get current user (requires auth)
- `PUT /api/users/me` - Update current user (requires auth)
- `DELETE /api/users/me` - Delete current user (requires auth)

### Troubleshooting

If users aren't being stored:

1. **Check backend logs** for errors
2. **Verify MongoDB connection string** in `backend/.env`
3. **Check browser console** for sync errors
4. **Test MongoDB connection**:
   ```bash
   cd backend
   python test_mongodb.py
   ```
5. **Check CORS settings** - frontend must be allowed
6. **Verify API_URL** in `frontend/.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

### Success Indicators

✅ Backend logs show: "Connected to MongoDB successfully!"
✅ Browser console shows: "✅ User synced to MongoDB: ..."
✅ `test_mongodb.py` shows user count > 0
✅ MongoDB Compass shows users in the collection

## 🔄 What Changed

### Frontend

- Added `UserSyncWrapper.jsx` component
- Automatically syncs users on authentication
- Shows loading state during sync
- Integrated into protected routes

### Backend

- Added `/api/users/sync` endpoint (no auth required)
- Creates or updates user on each login
- Extended user schema with image URL
- Added `/api/users/` endpoint to list all users

### Files Modified

- `frontend/src/App.jsx`
- `frontend/src/components/UserSyncWrapper.jsx`
- `backend/app/routers/users.py`
- `backend/app/schemas/user.py`
- `backend/test_mongodb.py` (new)
