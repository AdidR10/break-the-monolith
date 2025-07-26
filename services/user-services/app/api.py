from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import sys
import os
from datetime import datetime

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import get_db

from . import schemas, crud, auth

# Create router
router = APIRouter()
security = HTTPBearer()

class UserFromCache:
    """User object created from cached data for performance optimization"""
    def __init__(self, cached_data: dict):
        self.id = UUID(cached_data.get("id"))
        self.email = cached_data.get("email")
        self.phone = cached_data.get("phone")
        self.first_name = cached_data.get("first_name")
        self.last_name = cached_data.get("last_name")
        self.user_type = schemas.UserType(cached_data.get("user_type"))
        self.is_active = cached_data.get("is_active", True)
        self.is_verified = cached_data.get("is_verified", False)
        self.current_latitude = cached_data.get("current_latitude")
        self.current_longitude = cached_data.get("current_longitude")
        
        # Handle datetime fields
        created_at_str = cached_data.get("created_at")
        self.created_at = datetime.fromisoformat(created_at_str) if created_at_str else None
        
        last_login_str = cached_data.get("last_login")
        self.last_login = datetime.fromisoformat(last_login_str) if last_login_str else None
        
        # Handle profile data
        self.rickshaw_profile = None
        self.student_profile = None
        
        if "rickshaw_profile" in cached_data and cached_data["rickshaw_profile"]:
            profile_data = cached_data["rickshaw_profile"]
            self.rickshaw_profile = type('RickshawProfile', (), {
                'license_number': profile_data.get("license_number"),
                'vehicle_type': profile_data.get("vehicle_type"),
                'is_available': profile_data.get("is_available", False),
                'rating': profile_data.get("rating"),
                'rating_count': profile_data.get("rating_count", 0)
            })()
        
        if "student_profile" in cached_data and cached_data["student_profile"]:
            profile_data = cached_data["student_profile"]
            self.student_profile = type('StudentProfile', (), {
                'student_id': profile_data.get("student_id"),
                'university': profile_data.get("university"),
                'emergency_contact': profile_data.get("emergency_contact")
            })()
    
    def __getattr__(self, name):
        """Handle any missing attributes gracefully"""
        return None

# Dependencies
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user with Redis caching optimization"""
    try:
        payload = auth.verify_token(credentials.credentials)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Try to get user from Redis cache first
        cached_user_data = auth.get_cached_user_data(user_id)
        if cached_user_data:
            # Create a user-like object from cached data for backward compatibility
            user_obj = UserFromCache(cached_user_data)
            return user_obj
        
        # Fallback to database if not in cache
        user = crud.UserCRUD.get_user_by_id(db, UUID(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Cache the user data for future requests
        auth.cache_user_data(user_id, auth.serialize_user_for_cache(user))
        
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_current_rickshaw_user(current_user = Depends(get_current_active_user)):
    """Get current rickshaw puller user"""
    if current_user.user_type != schemas.UserType.RICKSHAW_PULLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Rickshaw puller access required."
        )
    return current_user

def get_current_student_user(current_user = Depends(get_current_active_user)):
    """Get current student user"""
    if current_user.user_type != schemas.UserType.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Student access required."
        )
    return current_user

# Authentication endpoints
@router.post("/auth/register", response_model=schemas.UserCompleteResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = crud.UserCRUD.get_user_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_phone = crud.UserCRUD.get_user_by_phone(db, user.phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
        
        # Create user
        db_user = crud.UserCRUD.create_user(db, user)
        return db_user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/auth/login", response_model=schemas.Token)
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token with Redis caching"""
    db_user = crud.UserCRUD.authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Update last login time
    crud.UserCRUD.update_last_login(db, db_user.id)
    
    # Cache user data in Redis for faster future access
    user_data = auth.serialize_user_for_cache(db_user)
    auth.cache_user_data(str(db_user.id), user_data)
    
    # Create access token (this will also cache the token payload)
    access_token = auth.create_access_token(data={"user_id": str(db_user.id), "email": db_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": db_user
    }

@router.post("/auth/logout", response_model=schemas.MessageResponse)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user = Depends(get_current_user)
):
    """Logout user and invalidate token"""
    try:
        # Add token to blacklist
        auth.TokenBlacklist.add_token(credentials.credentials, str(current_user.id))
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/auth/logout-all", response_model=schemas.MessageResponse)
async def logout_all_sessions(current_user = Depends(get_current_active_user)):
    """Logout from all sessions (invalidate all user tokens)"""
    try:
        # Blacklist all user tokens
        auth.TokenBlacklist.blacklist_user_tokens(str(current_user.id))
        
        return {"message": "Successfully logged out from all sessions"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all sessions failed"
        )

# User management endpoints
@router.get("/users/me", response_model=schemas.UserCompleteResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.put("/users/me", response_model=schemas.UserCompleteResponse)
async def update_current_user(
    user_update: schemas.UserUpdate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    try:
        updated_user = crud.UserCRUD.update_user(db, current_user.id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/users/me", response_model=schemas.MessageResponse)
async def deactivate_current_user(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate current user account"""
    success = crud.UserCRUD.deactivate_user(db, current_user.id)
    if success:
        return {"message": "Account deactivated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

# Admin endpoints for user management
@router.get("/users", response_model=schemas.PaginatedResponse)
async def get_users(
    user_type: Optional[schemas.UserType] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None),
    department: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get users with filters and pagination"""
    filters = schemas.UserSearchFilters(
        user_type=user_type,
        is_active=is_active,
        is_verified=is_verified,
        department=department,
        is_available=is_available
    )
    pagination = schemas.PaginationParams(page=page, size=size)
    
    result = crud.UserCRUD.get_users_with_filters(db, filters, pagination)
    return result

@router.get("/users/{user_id}", response_model=schemas.UserCompleteResponse)
async def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = crud.UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# Rickshaw profile endpoints
@router.post("/rickshaw/profile", response_model=schemas.RickshawProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_rickshaw_profile(
    profile: schemas.RickshawProfileCreate,
    current_user = Depends(get_current_rickshaw_user),
    db: Session = Depends(get_db)
):
    """Create rickshaw profile for current user"""
    # Check if profile already exists
    if current_user.rickshaw_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rickshaw profile already exists"
        )
    
    try:
        db_profile = crud.RickshawProfileCRUD.create_profile(db, current_user.id, profile)
        return db_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/rickshaw/profile", response_model=schemas.RickshawProfileResponse)
async def update_rickshaw_profile(
    profile_update: schemas.RickshawProfileUpdate,
    current_user = Depends(get_current_rickshaw_user),
    db: Session = Depends(get_db)
):
    """Update rickshaw profile"""
    updated_profile = crud.RickshawProfileCRUD.update_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rickshaw profile not found"
        )
    return updated_profile

@router.put("/rickshaw/location", response_model=schemas.RickshawProfileResponse)
async def update_rickshaw_location(
    location: schemas.LocationUpdate,
    current_user = Depends(get_current_rickshaw_user),
    db: Session = Depends(get_db)
):
    """Update rickshaw location"""
    updated_profile = crud.RickshawProfileCRUD.update_location(db, current_user.id, location)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rickshaw profile not found"
        )
    return updated_profile

@router.put("/rickshaw/availability", response_model=schemas.RickshawProfileResponse)
async def update_rickshaw_availability(
    availability: schemas.AvailabilityUpdate,
    current_user = Depends(get_current_rickshaw_user),
    db: Session = Depends(get_db)
):
    """Update rickshaw availability"""
    updated_profile = crud.RickshawProfileCRUD.update_availability(db, current_user.id, availability)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rickshaw profile not found"
        )
    return updated_profile

@router.get("/rickshaw/available", response_model=List[schemas.RickshawProfileResponse])
async def get_available_rickshaws(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get available rickshaws"""
    rickshaws = crud.RickshawProfileCRUD.get_available_rickshaws(db, limit)
    return rickshaws

# Student profile endpoints
@router.post("/student/profile", response_model=schemas.StudentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_student_profile(
    profile: schemas.StudentProfileCreate,
    current_user = Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """Create student profile for current user"""
    # Check if profile already exists
    if current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile already exists"
        )
    
    try:
        db_profile = crud.StudentProfileCRUD.create_profile(db, current_user.id, profile)
        return db_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/student/profile", response_model=schemas.StudentProfileResponse)
async def update_student_profile(
    profile_update: schemas.StudentProfileUpdate,
    current_user = Depends(get_current_student_user),
    db: Session = Depends(get_db)
):
    """Update student profile"""
    updated_profile = crud.StudentProfileCRUD.update_profile(db, current_user.id, profile_update)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    return updated_profile

# Performance monitoring endpoints (for demonstration)
@router.get("/performance/auth-stats")
async def get_auth_performance_stats(current_user = Depends(get_current_active_user)):
    """Get authentication performance statistics (cache vs database)"""
    try:
        # Get user data from cache
        import time
        
        # Test cache performance
        cache_start = time.time()
        cached_data = auth.get_cached_user_data(str(current_user.id))
        cache_time = time.time() - cache_start
        
        # Test database performance (if needed)
        db_time = None
        if not cached_data:
            from shared.database_config import SessionLocal
            db = SessionLocal()
            try:
                db_start = time.time()
                db_user = crud.UserCRUD.get_user_by_id(db, current_user.id)
                db_time = time.time() - db_start
            finally:
                db.close()
        
        return {
            "user_id": str(current_user.id),
            "cache_hit": cached_data is not None,
            "cache_response_time_ms": round(cache_time * 1000, 3),
            "database_response_time_ms": round(db_time * 1000, 3) if db_time else None,
            "performance_improvement": f"{round((db_time / cache_time) if db_time and cache_time > 0 else 0, 2)}x faster" if db_time and cached_data else "N/A",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance stats failed: {str(e)}"
        )

@router.post("/cache/refresh", response_model=schemas.MessageResponse)
async def refresh_user_cache(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually refresh user cache from database"""
    try:
        # Get fresh user data from database
        fresh_user = crud.UserCRUD.get_user_by_id(db, current_user.id)
        if not fresh_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update cache
        user_data = auth.serialize_user_for_cache(fresh_user)
        auth.cache_user_data(str(current_user.id), user_data)
        
        return {"message": "User cache refreshed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache refresh failed: {str(e)}"
        )

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"} 