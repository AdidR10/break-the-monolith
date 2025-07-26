from sqlalchemy import Column, String, Boolean, ForeignKey, DECIMAL, Integer, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
import sys
import os

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import Base

class UserType(str, enum.Enum):
    STUDENT = "STUDENT"
    RICKSHAW_PULLER = "RICKSHAW_PULLER"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rickshaw_profile = relationship("RickshawProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', type='{self.user_type}')>"

class RickshawProfile(Base):
    __tablename__ = "rickshaw_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    rickshaw_number = Column(String(50), unique=True, nullable=False, index=True)
    license_number = Column(String(50), unique=True)
    is_available = Column(Boolean, default=False)
    current_location = Column(String(255))
    current_latitude = Column(DECIMAL(10, 8))
    current_longitude = Column(DECIMAL(11, 8))
    total_rides = Column(Integer, default=0)
    rating = Column(DECIMAL(3, 2), default=0.00)
    rating_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="rickshaw_profile")
    
    def __repr__(self):
        return f"<RickshawProfile(id={self.id}, rickshaw_number='{self.rickshaw_number}')>"

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    department = Column(String(100))
    batch = Column(String(10))
    year = Column(Integer)
    total_rides = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    emergency_contact = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    
    def __repr__(self):
        return f"<StudentProfile(id={self.id}, student_id='{self.student_id}')>"

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(Text)
    ip_address = Column(String(45))
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>" 