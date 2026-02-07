# Fix: 401 Unauthorized Error on Simulation Run

## Issue
When clicking the "Run simulation" button in the frontend, users were getting a **401 Unauthorized** error, even though the simulation endpoint is supposed to work without authentication.

## Root Cause
The `get_optional_user` function in `backend/app/middleware/auth.py` was re-raising `HTTPException` errors instead of returning `None` when authentication failed. This meant that even though the endpoint declared authentication as optional, it would still fail with 401 if:
- Invalid token was provided
- Token verification failed with Clerk API
- Any authentication error occurred

## Fix Applied

### File: `backend/app/middleware/auth.py`

**Before:**
```python
async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    # ... code ...
    except HTTPException:
        raise  # ❌ This was causing the 401 error
    except Exception:
        return None
```

**After:**
```python
async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """
    Get user if authenticated, otherwise return None.
    Returns same shape as get_current_user: {user_id, session_id, session_data}.
    Does NOT raise exceptions - returns None if authentication fails.
    """
    # ... code ...
    except HTTPException:
        # For optional auth, return None instead of raising
        return None  # ✅ Now returns None, allowing request to proceed
    except Exception:
        return None
```

## Testing

The simulation endpoint (`POST /api/simulation/run`) now works in three scenarios:

1. **No authentication** - Works fine, `current_user` is `None`
2. **Valid authentication** - Works fine, `current_user` contains user data
3. **Invalid authentication** - Works fine, `current_user` is `None` (no longer raises 401)

## Impact

- ✅ Simulation can now run without requiring login
- ✅ Simulation still works with valid authentication
- ✅ No breaking changes to other endpoints
- ✅ Consistent with "optional authentication" pattern

## Status
**Fixed** - Backend server has auto-reloaded with the changes. Users can now run simulations without authentication errors.

## How to Verify

1. Open the playground at `http://localhost:5173/playground`
2. Configure simulation parameters in the left panel
3. Click "Run simulation" button
4. Should see successful simulation results without 401 errors

## Related Files

- `backend/app/middleware/auth.py` - Authentication middleware (FIXED)
- `backend/app/routers/simulation.py` - Uses `get_optional_user`
- All other endpoints using `get_optional_user` also benefit from this fix
