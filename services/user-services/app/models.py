import enum
import uuid
from sqlalchemy import Column, String, Enum, Boolean, TIMESTAMP, ForeignKey, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class UserType(enum.Enum):
    STUDENT = "STUDENT"
    RICKSHAW_PULLER = "RICKSHAW_PULLER"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    user_type = Column(Enum(UserType), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class RickshawProfile(Base):
    __tablename__ = "rickshaw_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rickshaw_number = Column(String(50), unique=True)
    license_number = Column(String(50))
    is_available = Column(Boolean, default=False)
    total_rides = Column(Integer, default=0)
    rating = Column(DECIMAL(3, 2), default=0.00)
    created_at = Column(TIMESTAMP, server_default=func.now())

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id = Column(String(50), unique=True)
    department = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
