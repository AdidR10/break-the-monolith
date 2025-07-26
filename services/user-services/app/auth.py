from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "BreakingTheMonolithWithIEEECSCUET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

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
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is expired
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
            raise jwt.ExpiredSignatureError("Token has expired")
        
        # Check token type
        token_type = payload.get("type")
        if token_type != "access":
            raise jwt.InvalidTokenError("Invalid token type")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")
    except Exception:
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

class TokenBlacklist:
    """Simple in-memory token blacklist (In production, use Redis)"""
    _blacklist = set()
    
    @classmethod
    def add_token(cls, token: str):
        """Add token to blacklist"""
        cls._blacklist.add(token)
    
    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in cls._blacklist
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired tokens from blacklist"""
        # In a real implementation, you'd check token expiration
        # For now, we'll keep it simple
        pass
