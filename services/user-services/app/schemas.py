from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal

class UserType(str, Enum):
    STUDENT = "STUDENT"
    RICKSHAW_PULLER = "RICKSHAW_PULLER"

# Base Schemas
class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., pattern=r"^(\+8801|01)[3-9]\d{8}$", description="Valid Bangladeshi phone number")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    user_type: UserType

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^(\+8801|01)[3-9]\d{8}$")

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Rickshaw Profile Schemas
class RickshawProfileBase(BaseModel):
    rickshaw_number: str = Field(..., min_length=1, max_length=50)
    license_number: Optional[str] = Field(None, max_length=50)

class RickshawProfileCreate(RickshawProfileBase):
    pass

class RickshawProfileUpdate(BaseModel):
    is_available: Optional[bool] = None
    current_location: Optional[str] = None
    current_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    current_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)

class LocationUpdate(BaseModel):
    current_location: str
    current_latitude: Decimal = Field(..., ge=-90, le=90)
    current_longitude: Decimal = Field(..., ge=-180, le=180)

class AvailabilityUpdate(BaseModel):
    is_available: bool

class RickshawProfileResponse(RickshawProfileBase):
    id: UUID
    user_id: UUID
    is_available: bool
    current_location: Optional[str]
    current_latitude: Optional[Decimal]
    current_longitude: Optional[Decimal]
    total_rides: int
    rating: Decimal
    rating_count: int
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Student Profile Schemas
class StudentProfileBase(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    batch: Optional[str] = Field(None, max_length=10)
    year: Optional[int] = Field(None, ge=1, le=6)
    emergency_contact: Optional[str] = Field(None, pattern=r"^(\+8801|01)[3-9]\d{8}$")

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileUpdate(BaseModel):
    department: Optional[str] = Field(None, max_length=100)
    batch: Optional[str] = Field(None, max_length=10)
    year: Optional[int] = Field(None, ge=1, le=6)
    emergency_contact: Optional[str] = Field(None, pattern=r"^(\+8801|01)[3-9]\d{8}$")

class StudentProfileResponse(StudentProfileBase):
    id: UUID
    user_id: UUID
    total_rides: int
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Complete User Response
class UserCompleteResponse(UserResponse):
    rickshaw_profile: Optional[RickshawProfileResponse] = None
    student_profile: Optional[StudentProfileResponse] = None

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserCompleteResponse

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[str] = None

# Search and Filter Schemas
class UserSearchFilters(BaseModel):
    user_type: Optional[UserType] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    department: Optional[str] = None
    is_available: Optional[bool] = None  # For rickshaw pullers

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: List[UserCompleteResponse]
    total: int
    page: int
    size: int
    pages: int

# Response Schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
