from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import os
import json
import sys
import logging

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.redis_config import redis_client

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "BreakingTheMonolithWithIEEECSCUET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Cache configuration
USER_CACHE_TTL = 86400  # 24 hours
TOKEN_CACHE_TTL = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Cache the token payload for faster verification
    user_id = data.get("user_id")
    if user_id:
        cache_token_payload(encoded_jwt, to_encode, user_id)
    
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token using Redis cache for optimization"""
    try:
        # First, check if token is blacklisted
        if TokenBlacklist.is_blacklisted(token):
            raise jwt.InvalidTokenError("Token has been revoked")
        
        # Try to get cached token payload first
        cached_payload = get_cached_token_payload(token)
        if cached_payload:
            # Verify expiration from cached data
            exp_timestamp = cached_payload.get("exp")
            if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
                # Remove expired token from cache
                invalidate_token_cache(token)
                raise jwt.ExpiredSignatureError("Token has expired")
            
            logger.debug("Token verified from cache")
            return cached_payload
        
        # Fallback to JWT verification if not in cache
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is expired
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
            raise jwt.ExpiredSignatureError("Token has expired")
        
        # Check token type
        token_type = payload.get("type")
        if token_type != "access":
            raise jwt.InvalidTokenError("Invalid token type")
        
        # Cache the payload for future requests
        user_id = payload.get("user_id")
        if user_id:
            cache_token_payload(token, payload, user_id)
        
        logger.debug("Token verified from JWT decode")
        return payload
        
    except jwt.ExpiredSignatureError:
        invalidate_token_cache(token)
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        invalidate_token_cache(token)
        raise jwt.InvalidTokenError("Invalid token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise jwt.InvalidTokenError("Token validation failed")

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token with longer expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verification (for debugging)"""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None

# Redis Cache Functions for User Data
def cache_user_data(user_id: str, user_data: Dict[str, Any], ttl: int = USER_CACHE_TTL):
    """Cache user data in Redis"""
    try:
        cache_key = f"user:{user_id}"
        redis_client.set_cache(cache_key, user_data, ttl)
        logger.debug(f"User data cached for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user data for {user_id}: {e}")

def get_cached_user_data(user_id: str) -> Optional[Dict[str, Any]]:
    """Get cached user data from Redis"""
    try:
        cache_key = f"user:{user_id}"
        cached_data = redis_client.get_cache(cache_key)
        if cached_data:
            logger.debug(f"User data retrieved from cache for user_id: {user_id}")
        return cached_data
    except Exception as e:
        logger.error(f"Failed to get cached user data for {user_id}: {e}")
        return None

def invalidate_user_cache(user_id: str):
    """Invalidate user cache"""
    try:
        cache_key = f"user:{user_id}"
        redis_client.delete_cache(cache_key)
        
        # Also invalidate all active tokens for this user
        invalidate_user_tokens(user_id)
        
        logger.debug(f"User cache invalidated for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate user cache for {user_id}: {e}")

# Redis Cache Functions for Token Verification
def cache_token_payload(token: str, payload: Dict[str, Any], user_id: str):
    """Cache token payload for faster verification"""
    try:
        # Cache token payload with shorter TTL
        token_cache_key = f"token:{token[-16:]}"  # Use last 16 chars as key
        redis_client.set_cache(token_cache_key, payload, TOKEN_CACHE_TTL)
        
        # Maintain a set of active tokens for the user
        user_tokens_key = f"user_tokens:{user_id}"
        redis_client.client.sadd(user_tokens_key, token[-16:])
        redis_client.client.expire(user_tokens_key, TOKEN_CACHE_TTL)
        
        logger.debug(f"Token payload cached for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache token payload: {e}")

def get_cached_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Get cached token payload"""
    try:
        token_cache_key = f"token:{token[-16:]}"
        cached_payload = redis_client.get_cache(token_cache_key)
        return cached_payload
    except Exception as e:
        logger.error(f"Failed to get cached token payload: {e}")
        return None

def invalidate_token_cache(token: str):
    """Invalidate specific token cache"""
    try:
        token_cache_key = f"token:{token[-16:]}"
        redis_client.delete_cache(token_cache_key)
        logger.debug(f"Token cache invalidated for token: {token[-16:]}")
    except Exception as e:
        logger.error(f"Failed to invalidate token cache: {e}")

def invalidate_user_tokens(user_id: str):
    """Invalidate all cached tokens for a user"""
    try:
        user_tokens_key = f"user_tokens:{user_id}"
        token_ids = redis_client.client.smembers(user_tokens_key)
        
        # Delete all cached token payloads
        for token_id in token_ids:
            token_cache_key = f"token:{token_id}"
            redis_client.delete_cache(token_cache_key)
        
        # Clear the user tokens set
        redis_client.delete_cache(user_tokens_key)
        
        logger.debug(f"All tokens invalidated for user_id: {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate user tokens for {user_id}: {e}")

# Utility functions for user data serialization
def serialize_user_for_cache(user) -> Dict[str, Any]:
    """Serialize user object for Redis caching"""
    try:
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "current_latitude": user.current_latitude,
            "current_longitude": user.current_longitude
        }
        
        # Add profile data if exists
        if hasattr(user, 'rickshaw_profile') and user.rickshaw_profile:
            user_data["rickshaw_profile"] = {
                "license_number": user.rickshaw_profile.license_number,
                "vehicle_type": user.rickshaw_profile.vehicle_type,
                "is_available": user.rickshaw_profile.is_available,
                "rating": float(user.rickshaw_profile.rating) if user.rickshaw_profile.rating else None,
                "rating_count": user.rickshaw_profile.rating_count
            }
        
        if hasattr(user, 'student_profile') and user.student_profile:
            user_data["student_profile"] = {
                "student_id": user.student_profile.student_id,
                "university": user.student_profile.university,
                "emergency_contact": user.student_profile.emergency_contact
            }
        
        return user_data
    except Exception as e:
        logger.error(f"Failed to serialize user for cache: {e}")
        return {}

class TokenBlacklist:
    """Redis-based token blacklist for secure token revocation"""
    
    @classmethod
    def add_token(cls, token: str, user_id: str = None):
        """Add token to blacklist"""
        try:
            blacklist_key = f"blacklist:{token[-16:]}"
            redis_client.set_cache(blacklist_key, {"revoked_at": datetime.utcnow().isoformat()}, TOKEN_CACHE_TTL)
            
            # Also invalidate from token cache
            invalidate_token_cache(token)
            
            logger.debug(f"Token blacklisted: {token[-16:]}")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
    
    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            blacklist_key = f"blacklist:{token[-16:]}"
            return redis_client.get_cache(blacklist_key) is not None
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    @classmethod
    def blacklist_user_tokens(cls, user_id: str):
        """Blacklist all tokens for a user"""
        try:
            user_tokens_key = f"user_tokens:{user_id}"
            token_ids = redis_client.client.smembers(user_tokens_key)
            
            for token_id in token_ids:
                blacklist_key = f"blacklist:{token_id}"
                redis_client.set_cache(blacklist_key, {"revoked_at": datetime.utcnow().isoformat()}, TOKEN_CACHE_TTL)
            
            # Invalidate all user tokens from cache
            invalidate_user_tokens(user_id)
            
            logger.debug(f"All tokens blacklisted for user_id: {user_id}")
        except Exception as e:
            logger.error(f"Failed to blacklist user tokens for {user_id}: {e}")
